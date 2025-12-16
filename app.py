import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
from sqlalchemy.orm import Session
from db import engine, init_db, User, Repository, PullRequest, Comment, create_user
from git_utils import list_repositories, get_repo_branches, create_branch, get_diff, merge_branch
import pandas as pd
import bcrypt
import os

# Initialize DB
init_db()

# Create default admin if not exists
with Session(engine) as session:
    if not session.query(User).filter_by(username='admin').first():
        hashed = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(username='admin', password_hash=hashed, is_admin=True)
        session.add(admin)
        session.commit()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "GitWatch"

# Layouts
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("GitWatch Login", className="text-center mb-4"),
            dbc.Input(id="login-username", placeholder="Username", type="text", className="mb-2"),
            dbc.Input(id="login-password", placeholder="Password", type="password", className="mb-2"),
            dbc.Button("Login", id="login-button", color="primary", className="w-100"),
            html.Div(id="login-alert", className="mt-2"),
            html.Div([
                "Don't have an account? ",
                dcc.Link("Sign up here", href="/signup")
            ], className="mt-3 text-center")
        ], width=4, className="mx-auto mt-5")
    ])
])

signup_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("GitWatch Sign Up", className="text-center mb-4"),
            dbc.Input(id="signup-username", placeholder="Username", type="text", className="mb-2"),
            dbc.Input(id="signup-password", placeholder="Password", type="password", className="mb-2"),
            dbc.Input(id="signup-confirm", placeholder="Confirm Password", type="password", className="mb-2"),
            dbc.Button("Sign Up", id="signup-button", color="success", className="w-100"),
            html.Div(id="signup-alert", className="mt-2"),
            html.Div([
                "Already have an account? ",
                dcc.Link("Login here", href="/login")
            ], className="mt-3 text-center")
        ], width=4, className="mx-auto mt-5")
    ])
])

def get_sidebar(user_data):
    return html.Div([
        html.H4("GitWatch", className="mb-4"),
        html.P(f"User: {user_data['username']}"),
        dbc.Nav([
            dbc.NavLink("Dashboard", href="/", active="exact"),
            dbc.NavLink("New Pull Request", href="/new-pr", active="exact"),
            dbc.NavLink("Logout", id="logout-btn", href="#", active="exact"),
        ], vertical=True, pills=True),
    ], style={"padding": "2rem 1rem", "backgroundColor": "#f8f9fa", "height": "100vh"})

def get_dashboard_layout(user_data):
    with Session(engine) as session:
        prs = session.query(PullRequest).all()
        
        pr_list = []
        if not prs:
            pr_list.append(dbc.ListGroupItem("No active pull requests found."))
        else:
            for pr in prs:
                pr_list.append(
                    dbc.ListGroupItem([
                        html.Div([
                            html.H5(pr.title, className="mb-1"),
                            html.Small(f"#{pr.id} opened by {pr.author.username} • {pr.status}")
                        ], className="d-flex w-100 justify-content-between"),
                        html.P(f"Repo: {pr.repo.name} | {pr.source_branch} -> {pr.target_branch}", className="mb-1")
                    ], href=f"/pr/{pr.id}", action=True)
                )

    return dbc.Container([
        dbc.Row([
            dbc.Col(get_sidebar(user_data), width=2),
            dbc.Col([
                html.H2("Dashboard", className="mt-4"),
                dbc.ListGroup(pr_list, className="mt-4")
            ], width=10)
        ])
    ], fluid=True)

def get_new_pr_layout(user_data):
    repos = list_repositories()
    repo_options = [{'label': r['name'], 'value': r['path']} for r in repos]
    
    return dbc.Container([
        dbc.Row([
            dbc.Col(get_sidebar(user_data), width=2),
            dbc.Col([
                html.H2("Create New Pull Request", className="mt-4"),
                dbc.Label("Select Repository"),
                dbc.Select(id="new-pr-repo", options=repo_options, className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Source Branch"),
                        dbc.Select(id="new-pr-source", className="mb-3")
                    ]),
                    dbc.Col([
                        dbc.Label("Target Branch"),
                        dbc.Select(id="new-pr-target", className="mb-3")
                    ])
                ]),
                
                dbc.Label("Title"),
                dbc.Input(id="new-pr-title", type="text", className="mb-3"),
                
                dbc.Label("Description"),
                dbc.Textarea(id="new-pr-desc", className="mb-3"),
                
                dbc.Button("Create Pull Request", id="create-pr-btn", color="success"),
                html.Div(id="create-pr-alert", className="mt-3")
            ], width=8)
        ])
    ], fluid=True)

def get_pr_detail_layout(pr_id, user_data):
    with Session(engine) as session:
        pr = session.query(PullRequest).filter_by(id=pr_id).first()
        if not pr:
            return html.Div("PR not found")
        
        diff_text = get_diff(pr.repo.path, pr.source_branch, pr.target_branch)
        
        merge_button = html.Div()
        if user_data['is_admin'] and pr.status == 'open':
            merge_button = dbc.Button("Merge Pull Request", id={"type": "merge-btn", "index": pr.id}, color="success", className="mt-3")

        # Fetch comments
        comments_list = []
        for comment in pr.comments:
            comments_list.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{comment.author.username} - {comment.created_at.strftime('%Y-%m-%d %H:%M')}", className="card-subtitle mb-2 text-muted"),
                        html.P(comment.content, className="card-text")
                    ])
                ], className="mb-2")
            )
        
        if not comments_list:
            comments_list = [html.P("No comments yet.", className="text-muted")]

        return dbc.Container([
            dbc.Row([
                dbc.Col(get_sidebar(user_data), width=2),
                dbc.Col([
                    html.H2(f"#{pr.id} {pr.title}", className="mt-4"),
                    html.P(pr.description),
                    html.Hr(),
                    html.H4("Changes"),
                    html.Pre(diff_text, style={"backgroundColor": "#f0f0f0", "padding": "10px", "maxHeight": "500px", "overflowY": "scroll"}),
                    merge_button,
                    html.Div(id="merge-alert", className="mt-2"),
                    html.Hr(),
                    html.H4("Comments"),
                    html.Div(id="comments-container", children=comments_list, className="mb-4"),
                    dcc.Store(id="current-pr-id", data=pr.id),
                    dbc.Textarea(id="comment-textarea", placeholder="Leave a comment...", className="mb-2"),
                    dbc.Button("Post Comment", id="post-comment-btn", color="primary"),
                    html.Div(id="comment-alert", className="mt-2")
                ], width=10)
            ])
        ], fluid=True)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session"),
    dcc.Store(id="login-signal", storage_type="memory"),
    dcc.Store(id="logout-signal", storage_type="memory"),
    html.Div(id="page-content")
])

# --- Callbacks ---

# 1. Login Callback
@app.callback(
    Output("login-signal", "data"),
    Output("login-alert", "children"),
    Input("login-button", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return dash.no_update, dbc.Alert("Please enter username and password", color="warning")
        
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return {'user_id': user.id, 'username': user.username, 'is_admin': user.is_admin}, ""
        else:
            return dash.no_update, dbc.Alert("Invalid credentials", color="danger")

@app.callback(
    Output("signup-alert", "children"),
    Input("signup-button", "n_clicks"),
    State("signup-username", "value"),
    State("signup-password", "value"),
    State("signup-confirm", "value"),
    prevent_initial_call=True
)
def handle_signup(n_clicks, username, password, confirm):
    if not username or not password or not confirm:
        return dbc.Alert("Please fill in all fields", color="warning")
    
    if password != confirm:
        return dbc.Alert("Passwords do not match", color="danger")
    
    try:
        user = create_user(username, password)
        if user:
            return dbc.Alert("Account created! Please login.", color="success")
        else:
            return dbc.Alert("Username already exists", color="danger")
    except Exception as e:
        return dbc.Alert(f"Error creating account: {e}", color="danger")

# 2. Logout Callback
@app.callback(
    Output("logout-signal", "data"),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    return True

# 3. Session Manager
@app.callback(
    Output("session-store", "data"),
    Input("login-signal", "data"),
    Input("logout-signal", "data"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def manage_session(login_data, logout_data, current_session):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
        
    trigger = ctx.triggered[0]['prop_id']
    
    if 'login-signal' in trigger:
        return login_data
    if 'logout-signal' in trigger:
        return None
        
    return dash.no_update

# 4. Router
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("session-store", "data")
)
def router(pathname, session_data):
    if pathname == "/signup":
        return signup_layout

    # If no session, show login
    if not session_data:
        return login_layout

    # If session exists, show content
    if pathname == "/new-pr":
        return get_new_pr_layout(session_data)
    
    if pathname and pathname.startswith("/pr/"):
        try:
            pr_id = int(pathname.split("/")[-1])
            return get_pr_detail_layout(pr_id, session_data)
        except ValueError:
            pass

    return get_dashboard_layout(session_data)

# Populate branches when repo is selected
@app.callback(
    Output("new-pr-source", "options"),
    Output("new-pr-target", "options"),
    Input("new-pr-repo", "value")
)
def update_branches(repo_path):
    if not repo_path:
        return [], []
    branches = get_repo_branches(repo_path)
    options = [{'label': b, 'value': b} for b in branches]
    return options, options

# Create PR
@app.callback(
    Output("create-pr-alert", "children"),
    Input("create-pr-btn", "n_clicks"),
    State("new-pr-repo", "value"),
    State("new-pr-source", "value"),
    State("new-pr-target", "value"),
    State("new-pr-title", "value"),
    State("new-pr-desc", "value"),
    State("session-store", "data")
)
def create_pr(n_clicks, repo_path, source, target, title, desc, session_data):
    if not n_clicks:
        return ""
    
    if not session_data:
        return dbc.Alert("You must be logged in to create a PR", color="danger")
    
    if not all([repo_path, source, target, title]):
        return dbc.Alert("Please fill in all fields", color="danger")
    
    with Session(engine) as session:
        # Find or create repo entry
        repo_name = os.path.basename(repo_path)
        repo = session.query(Repository).filter_by(path=repo_path).first()
        if not repo:
            repo = Repository(name=repo_name, path=repo_path)
            session.add(repo)
            session.commit()
            
        pr = PullRequest(
            title=title,
            description=desc,
            author_id=session_data['user_id'],
            repo_id=repo.id,
            source_branch=source,
            target_branch=target
        )
        session.add(pr)
        session.commit()
        
    return dbc.Alert("Pull Request Created Successfully!", color="success")

# Merge PR
@app.callback(
    Output("merge-alert", "children"),
    Input({"type": "merge-btn", "index": ALL}, "n_clicks"),
    State("session-store", "data")
)
def merge_pr(n_clicks, session_data):
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Parse ID from string if needed, but dash gives us the dict structure in triggered_id if we use pattern matching correctly? 
    # Actually ctx.triggered_id is better in newer dash, but let's stick to safe parsing
    import json
    try:
        # triggered_id is a string like '{"index":1,"type":"merge-btn"}'
        prop_id = ctx.triggered[0]['prop_id']
        if "merge-btn" not in prop_id:
            return ""
        
        # We need to extract the index. 
        # Since we used ALL, n_clicks is a list. We need to find which one was clicked.
        # But wait, if we use ALL, the callback fires when ANY of them change.
        # We can find the one that is not None?
        
        # Let's simplify: The triggered prop_id contains the JSON string of the ID.
        id_str = prop_id.split('.')[0]
        id_dict = json.loads(id_str)
        pr_id = id_dict['index']
        
        # Check if actually clicked (n_clicks > 0)
        # We need to find the value in n_clicks list corresponding to this ID? 
        # Actually, let's just check if the specific button was the trigger.
        
        with Session(engine) as session:
            pr = session.query(PullRequest).filter_by(id=pr_id).first()
            if not pr:
                return dbc.Alert("PR not found", color="danger")
            
            success, msg = merge_branch(pr.repo.path, pr.source_branch, pr.target_branch)
            
            if success:
                pr.status = 'merged'
                session.commit()
                return dbc.Alert(f"Merged! {msg}", color="success")
            else:
                return dbc.Alert(f"Merge failed: {msg}", color="danger")

    except Exception as e:
        return dbc.Alert(f"Error: {e}", color="danger")

# Post Comment
@app.callback(
    Output("comments-container", "children"),
    Output("comment-alert", "children"),
    Output("comment-textarea", "value"),
    Input("post-comment-btn", "n_clicks"),
    State("comment-textarea", "value"),
    State("current-pr-id", "data"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def post_comment(n_clicks, comment_text, pr_id, session_data):
    try:
        if not session_data:
            return dash.no_update, dbc.Alert("You must be logged in to post a comment", color="danger"), dash.no_update
        
        if not comment_text or not comment_text.strip():
            return dash.no_update, dbc.Alert("Comment cannot be empty", color="warning"), dash.no_update

        with Session(engine) as session:
            pr = session.query(PullRequest).filter_by(id=pr_id).first()
            if not pr:
                return dash.no_update, dbc.Alert("PR not found", color="danger"), dash.no_update
            
            comment = Comment(
                pr_id=pr.id,
                user_id=session_data['user_id'],
                content=comment_text
            )
            session.add(comment)
            session.commit()
            
            # Refresh comments list
            updated_pr = session.query(PullRequest).filter_by(id=pr_id).first()
            comments_list = []
            for c in updated_pr.comments:
                comments_list.append(
                    dbc.Card([
                        dbc.CardBody([
                            html.H6(f"{c.author.username} - {c.created_at.strftime('%Y-%m-%d %H:%M')}", className="card-subtitle mb-2 text-muted"),
                            html.P(c.content, className="card-text")
                        ])
                    ], className="mb-2")
                )
            
            return comments_list, dbc.Alert("Comment posted!", color="success"), ""

    except Exception as e:
        return dash.no_update, dbc.Alert(f"Error: {e}", color="danger"), dash.no_update

if __name__ == "__main__":
    app.run(debug=True)

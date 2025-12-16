# GitWatch - Local GitHub Replica

A Dash application to manage local git repositories with Pull Request functionality.

## Features
- **Local Authentication**: SQLite based user management.
- **Repository Scanning**: Automatically finds repositories in your `local_projects` folder.
- **Pull Requests**: Create PRs between branches.
- **Code Review**: View diffs of changes.
- **Merging**: Merge PRs directly from the UI (Admin only).
- **Close Requests**: Close requests to hide them from the active list (Admin only). Closed requests appear in a collapsible "Closed" dropdown.

## Setup
1.  Ensure you have the required packages installed:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the application:
    ```bash
    python app.py
    ```
3.  Open your browser to `http://127.0.0.1:8050`.

## Default Login
- **Username**: `admin`
- **Password**: `admin`

## Sign Up
New users can create an account by clicking the "Sign up here" link on the login page.
- Enter a unique username and password.
- Once registered, log in with your new credentials.
- New accounts are standard users (non-admin) by default.

## Usage
1.  **Login** with the default credentials or create a new account.
2.  **Create a PR**: Go to "New Pull Request", select a repo, source branch, and target branch.
3.  **Review**: Go to the Dashboard and click on the PR to view the diff.
4.  **Merge**: If you are an admin, click "Merge Pull Request" to merge the changes.
5.  **Close Request**: If you are an admin, click "Close Request" to close a PR. Closed requests will be hidden from the main list and appear under the collapsible "Closed" dropdown.

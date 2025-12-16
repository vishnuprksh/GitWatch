import os
import git
from git import Repo
import shutil

def get_local_projects_path():
    user_profile = os.environ.get('USERPROFILE')
    return os.path.join(user_profile, 'local_projects')

def get_project_repos_path():
    username = os.environ.get('USERNAME')
    search_paths = [
        f"C:\\Users\\{username}\\OneDrive - Ship Watch\\Desktop\\Data Science\\project_repos",
        f"C:\\Users\\{username}\\Ship Watch\\Vishnu Prakash - Data Science\\project_repos",
        f"C:\\Users\\{username}\\Ship Watch\\sa_365backup - Ship-watch Shared\\Reference Information\\Data Science\\project_repos"
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    return None

def list_repositories():
    """Scans local projects and returns a list of repo names and paths."""
    base_path = get_local_projects_path()
    repos = []
    if not os.path.exists(base_path):
        return repos
        
    for name in os.listdir(base_path):
        full_path = os.path.join(base_path, name)
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, '.git')):
            repos.append({'name': name, 'path': full_path})
    return repos

def get_repo_branches(repo_path):
    try:
        repo = Repo(repo_path)
        return [head.name for head in repo.heads]
    except Exception as e:
        print(f"Error getting branches for {repo_path}: {e}")
        return []

def create_branch(repo_path, branch_name, source_branch='main'):
    try:
        repo = Repo(repo_path)
        if branch_name in repo.heads:
            return False, "Branch already exists"
        
        if source_branch not in repo.heads:
             return False, f"Source branch {source_branch} does not exist"

        source = repo.heads[source_branch]
        new_branch = repo.create_head(branch_name, source)
        # Don't checkout, just create
        return True, f"Branch {branch_name} created"
    except Exception as e:
        return False, str(e)

def get_diff(repo_path, source_branch, target_branch='main'):
    try:
        repo = Repo(repo_path)
        
        if source_branch not in repo.heads or target_branch not in repo.heads:
            return "One or both branches do not exist."

        # Get commit objects
        source_commit = repo.heads[source_branch].commit
        target_commit = repo.heads[target_branch].commit
        
        # Get diff
        diff_index = target_commit.diff(source_commit, create_patch=True)
        
        diff_text = ""
        for diff in diff_index:
            diff_text += f"File: {diff.a_path}\n"
            diff_text += str(diff.diff.decode('utf-8')) + "\n\n"
            
        return diff_text if diff_text else "No changes found."
    except Exception as e:
        return f"Error generating diff: {e}"

def merge_branch(repo_path, source_branch, target_branch='main'):
    try:
        repo = Repo(repo_path)
        
        # Checkout target
        repo.git.checkout(target_branch)
        
        # Merge source
        repo.git.merge(source_branch)
        
        return True, "Merge successful"
    except Exception as e:
        return False, f"Merge failed: {e}"

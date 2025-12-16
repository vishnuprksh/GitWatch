import os

SECRET_KEY = os.urandom(24)

# Database path - use environment variable or default to current directory
DATA_DIR = os.environ.get('GITWATCH_DATA_DIR', '/data/gitwatch')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = f'sqlite:///{DATA_DIR}/gitwatch.db'

# Repository scan path
REPOS_PATH = os.environ.get('GITWATCH_REPOS_PATH', '/data/gitwatch/repos')
os.makedirs(REPOS_PATH, exist_ok=True)

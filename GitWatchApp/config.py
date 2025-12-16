import os

SECRET_KEY = os.urandom(24)
DB_PATH = 'sqlite:///gitwatch.db'

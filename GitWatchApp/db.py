from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import os
import bcrypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    
    pull_requests = relationship("PullRequest", back_populates="author")
    comments = relationship("Comment", back_populates="author")

class Repository(Base):
    __tablename__ = 'repositories'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    path = Column(String, nullable=False) # Local path
    remote_path = Column(String, nullable=True) # Bare repo path
    
    pull_requests = relationship("PullRequest", back_populates="repo")

class PullRequest(Base):
    __tablename__ = 'pull_requests'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey('users.id'))
    repo_id = Column(Integer, ForeignKey('repositories.id'))
    source_branch = Column(String, nullable=False)
    target_branch = Column(String, default='main')
    status = Column(String, default='open') # open, merged, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("User", back_populates="pull_requests")
    repo = relationship("Repository", back_populates="pull_requests")
    comments = relationship("Comment", back_populates="pr")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    pr_id = Column(Integer, ForeignKey('pull_requests.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    pr = relationship("PullRequest", back_populates="comments")
    author = relationship("User", back_populates="comments")

# Database setup
DB_PATH = 'sqlite:///gitwatch.db'
engine = create_engine(DB_PATH)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def create_user(username, password, is_admin=False):
    """Creates a new user with hashed password. Returns the user object or None if username exists."""
    with Session() as session:
        if session.query(User).filter_by(username=username).first():
            return None
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=username, password_hash=hashed, is_admin=is_admin)
        session.add(new_user)
        session.commit()
        # Refresh to get ID
        session.refresh(new_user)
        return new_user


"""
Database operations for authentication
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import User, RefreshToken
from auth.utils import hash_token
from datetime import datetime, timedelta
from config import settings
import uuid


def get_user_by_github_id(db: Session, github_id: str) -> User | None:
    """Fetch user by GitHub ID"""
    return db.query(User).filter(User.github_id == github_id).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Fetch user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch user by email"""
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    github_id: str,
    username: str,
    email: str,
    display_name: str | None = None,
    avatar_url: str | None = None
) -> User:
    """Create a new user"""
    user = User(
        id=str(uuid.uuid4()),
        github_id=github_id,
        username=username,
        email=email,
        display_name=display_name or username,
        avatar_url=avatar_url,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, **kwargs) -> User:
    """Update user fields"""
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def create_refresh_token(db: Session, user_id: str, token_hash: str) -> RefreshToken:
    """Create a refresh token for the user"""
    refresh_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=token_hash,
        is_revoked=False,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def verify_refresh_token(db: Session, token_hash: str, user_id: str) -> RefreshToken | None:
    """Verify refresh token"""
    token = db.query(RefreshToken).filter(
        and_(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        )
    ).first()
    return token


def revoke_refresh_token(db: Session, token_hash: str) -> None:
    """Revoke a refresh token"""
    token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    if token:
        token.is_revoked = True
        db.commit()


def get_db_session():
    """Dependency for getting database session"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

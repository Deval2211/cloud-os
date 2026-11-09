"""
Database initialization script
"""
import os
from sqlalchemy import create_engine
from config import settings
from models import Base

def init_db():
    """Initialize database with all tables"""
    engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()

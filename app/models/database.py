"""
Database models and connection management.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from core.config import settings

Base = declarative_base()


class Result(Base):
    """Database model for quiz results."""
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(String, nullable=False)  # Keep as string for compatibility
    name = Column(String, nullable=False)
    top_type = Column(Integer, nullable=False)
    scores_json = Column(Text, nullable=False)
    raw_json = Column(Text, nullable=False)
    validity_json = Column(Text)
    delete_token = Column(String, unique=True, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_results_delete_token', 'delete_token'),
        Index('idx_results_top_type', 'top_type'),
    )


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    def init_database(self) -> None:
        """Initialize database connection and create tables.""" 
        # Check for Cloud Run environment and SQLite
        import os
        is_cloud_run = os.getenv('K_SERVICE') is not None  # Cloud Run sets this
        
        if settings.database_url.startswith("sqlite"):
            if is_cloud_run:
                from core.logging import app_logger
                app_logger.warning(
                    "CRITICAL: Using SQLite in Cloud Run! Data will be lost on container restart. "
                    "Consider using Cloud SQL for production: "
                    "https://cloud.google.com/sql/docs/postgres/connect-run"
                )
            
            db_path = settings.database_path
            if db_path:
                db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            # SQLite specific optimizations
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        
        # Create tables
        Base.metadata.create_all(self._engine)
        
        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)
    
    def get_session(self) -> Session:
        """Get database session."""
        if not self._session_factory:
            self.init_database()
        return self._session_factory()
    
    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()


# Legacy database functions for backwards compatibility
def init_db():
    """Legacy function to initialize database."""
    db_manager.init_database()


def get_db_connection():
    """Get raw SQLite connection for legacy code."""
    db_path = settings.database_path or settings.app_dir / "results.sqlite"
    return sqlite3.connect(str(db_path))


# Global database manager instance
db_manager = DatabaseManager()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # helps avoid stale connections
    pool_recycle=3600        # refresh connections every hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from app.models.user import User
    from app.models.task import Task
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

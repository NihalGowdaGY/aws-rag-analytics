from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import settings

# Created connection enginee
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False}  
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()
# dependancy to get db sessions per request
def get_db():
    """Contextual generator dependency to inject clean DB handles per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
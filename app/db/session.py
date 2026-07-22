from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import settings

engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker[Session](bind=engine)


def get_db():
    """Функция для инъекции сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

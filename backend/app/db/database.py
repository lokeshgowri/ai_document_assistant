from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# backend/data/
DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"

DATA_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# SQLite database file
DATABASE_URL = (
    f"sqlite:///{DATA_DIRECTORY / 'conversations.db'}"
)


# Database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
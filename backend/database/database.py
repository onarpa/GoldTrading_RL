from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/gold_trading.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
    echo=False,
)


def create_db_and_tables():
    """สร้าง tables ทั้งหมดถ้ายังไม่มี"""
    os.makedirs("database", exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency สำหรับ DB session"""
    with Session(engine) as session:
        yield session

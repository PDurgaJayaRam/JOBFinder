"""Database engine and session management."""

import os

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

# Create data directory automatically
os.makedirs("./data", exist_ok=True)

# SQLite database URL
DATABASE_URL = "sqlite+aiosqlite:///./data/career_agent.db"

# Create async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base model class
Base = declarative_base()


# Initialize database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Dependency for FastAPI routes
async def get_db():
    async with async_session() as session:
        yield session
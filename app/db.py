# app/db.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Default dev DB is a local sqlite file. In prod set DATABASE_URL env var.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

# Ensure tables exist without dropping data
# Only create tables if they don't exist - preserves existing data
if DATABASE_URL.startswith("sqlite") and ("./dev.db" in DATABASE_URL or DATABASE_URL.endswith("/dev.db")):
    try:
        # create tables synchronously so they exist immediately
        # use a sync engine for this one-time bootstrap
        from sqlalchemy import create_engine
        sync_url = "sqlite:///./dev.db"
        sync_engine = create_engine(sync_url, future=True)
        # create_all only creates tables that don't exist - doesn't drop data
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()
    except Exception:
        # don't fail import on filesystem errors; it's only a dev convenience
        pass

# For Postgres use: postgresql+asyncpg://user:pass@localhost:5432/dbname
engine = create_async_engine(DATABASE_URL, future=True, echo=False)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """
    Ensure tables exist. Does NOT drop existing tables.
    Use reset_db() to forcibly recreate schema (dev only).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_db():
    """
    Drop and recreate all tables. Intended for local dev / tests when using the
    default sqlite dev DB. Avoid calling in production.
    """
    async with engine.begin() as conn:
        # Drop all, then create all
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

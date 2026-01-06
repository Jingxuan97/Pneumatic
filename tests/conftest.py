# tests/conftest.py
"""
Pytest configuration and fixtures for test cleanup.
"""
import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.db import engine, AsyncSessionLocal


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def cleanup_database():
    """
    Clean up database after each test.
    This ensures tests don't interfere with each other.
    Only cleans up if using a file-based database (not in-memory).
    """
    yield

    # Only cleanup if using file-based database
    from app.db import DATABASE_URL
    if ":memory:" not in DATABASE_URL:
        try:
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                # Delete in reverse order of dependencies
                await session.execute(text("DELETE FROM messages"))
                await session.execute(text("DELETE FROM conversation_members"))
                await session.execute(text("DELETE FROM conversations"))
                await session.execute(text("DELETE FROM users"))
                await session.commit()
        except Exception:
            # If cleanup fails, continue (database might not exist or be in use)
            pass


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """
    Clean up test-related files after all tests complete.
    """
    yield

    # Cleanup test database files
    test_db_files = [
        "test.db",
        "test.sqlite",
        "test.sqlite3",
        "pytest.db",
        "pytest.sqlite",
    ]

    for db_file in test_db_files:
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
        except Exception:
            pass

    # Cleanup __pycache__ in tests directory
    import shutil
    test_cache_dirs = [
        "tests/__pycache__",
        "__pycache__",
    ]

    for cache_dir in test_cache_dirs:
        try:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
        except Exception:
            pass


@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """
    Set test environment variables before tests run.
    """
    # Use in-memory SQLite for tests if DATABASE_URL not set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    # Disable tracing during tests
    os.environ["DISABLE_TRACING"] = "1"

    yield

    # Cleanup environment variables after tests
    if "DISABLE_TRACING" in os.environ:
        del os.environ["DISABLE_TRACING"]

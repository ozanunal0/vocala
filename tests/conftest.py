"""
Pytest configuration and fixtures for Vocala tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.core.config import settings
from app.main import app

# Test database URL - using SQLite for simplicity
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create test engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up
    await engine.dispose()


@pytest.fixture
def override_get_db(test_db: AsyncSession):
    """Override the get_db dependency for testing."""
    async def _get_test_db():
        yield test_db
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return {
        "llm_provider": "mock",
        "database_url": TEST_DATABASE_URL,
        "redis_url": "redis://localhost:6379/15",  # Test Redis DB
        "telegram_bot_token": "test_token",
        "secret_key": "test_secret_key",
        "daily_word_count": 3,
        "oxford_3000_difficulty": "B1_B2",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "telegram_id": 123456789,
        "telegram_username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "tr",
    }


@pytest.fixture
def sample_word_data():
    """Sample word data for testing."""
    return {
        "english_word": "journey",
        "turkish_translation": "yolculuk", 
        "part_of_speech": "noun",
        "definition": "an act of traveling from one place to another",
        "llm_provider": "mock",
        "llm_model": "mock-model",
        "difficulty_level": "B1_B2",
    }


@pytest.fixture
def sample_example_data():
    """Sample example data for testing."""
    return {
        "english_sentence": "The journey took three hours.",
        "turkish_translation": "Yolculuk üç saat sürdü.",
        "llm_provider": "mock",
        "llm_model": "mock-model",
    } 
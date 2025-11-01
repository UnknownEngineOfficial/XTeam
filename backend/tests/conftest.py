"""
Test configuration and fixtures for XTeam backend tests.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient


# ============================================================================
# Pytest Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DEBUG", "true")


# Import after env setup
from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    This fixture creates a new in-memory SQLite database for each test
    and tears it down after the test completes.
    """
    # Create test engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Yield session
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with database override.
    """
    # Override get_db dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client with transport
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Cleanup
    app.dependency_overrides.clear()


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    from app.core.security import hash_password
    
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=hash_password("testpassword"),
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_superuser(test_db: AsyncSession) -> User:
    """Create a test superuser."""
    from app.core.security import hash_password
    
    user = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=hash_password("adminpassword"),
        is_active=True,
        is_superuser=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create a JWT token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def test_superuser_token(test_superuser: User) -> str:
    """Create a JWT token for test superuser."""
    return create_access_token(data={"sub": str(test_superuser.id)})


# ============================================================================
# Project Fixtures
# ============================================================================

@pytest.fixture
async def test_project(test_db: AsyncSession, test_user: User):
    """Create a test project."""
    from app.models.project import Project
    
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=test_user.id,
        status="active",
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)
    return project


# ============================================================================
# Agent Fixtures
# ============================================================================

@pytest.fixture
async def test_agent_config(test_db: AsyncSession, test_project):
    """Create a test agent configuration."""
    from app.models.agent_config import AgentConfig
    
    agent = AgentConfig(
        project_id=test_project.id,
        agent_type="assistant",
        name="Test Agent",
        description="A test agent",
        config={"model": "gpt-4", "temperature": 0.7},
    )
    test_db.add(agent)
    await test_db.commit()
    await test_db.refresh(agent)
    return agent

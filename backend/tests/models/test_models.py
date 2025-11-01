"""
Test database models.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestUserModel:
    """Test User model."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_db: AsyncSession):
        """Test creating a user."""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        user = User(
            email="model_test@example.com",
            username="modeltest",
            full_name="Model Test User",
            hashed_password=get_password_hash("password"),
            is_active=True,
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        assert user.id is not None
        assert user.email == "model_test@example.com"
        assert user.username == "modeltest"
    
    @pytest.mark.asyncio
    async def test_user_relationships(self, test_user, test_project):
        """Test user-project relationships."""
        assert test_project.owner_id == test_user.id


class TestProjectModel:
    """Test Project model."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, test_db: AsyncSession, test_user):
        """Test creating a project."""
        from app.models.project import Project
        
        project = Project(
            name="Model Test Project",
            description="Testing project model",
            owner_id=test_user.id,
            status="active",
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)
        
        assert project.id is not None
        assert project.name == "Model Test Project"
        assert project.owner_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_project_status_values(self):
        """Test valid project status values."""
        from app.models.project import ProjectStatus
        
        valid_statuses = ["draft", "active", "paused", "completed", "archived"]
        for status in valid_statuses:
            assert hasattr(ProjectStatus, status.upper())


class TestAgentConfigModel:
    """Test AgentConfig model."""
    
    @pytest.mark.asyncio
    async def test_create_agent_config(self, test_db: AsyncSession, test_project):
        """Test creating an agent configuration."""
        from app.models.agent_config import AgentConfig
        
        agent = AgentConfig(
            project_id=test_project.id,
            agent_type="developer",
            name="Model Test Agent",
            description="Testing agent model",
            config={"model": "gpt-4"},
        )
        test_db.add(agent)
        await test_db.commit()
        await test_db.refresh(agent)
        
        assert agent.id is not None
        assert agent.name == "Model Test Agent"
        assert agent.project_id == test_project.id


class TestExecutionModel:
    """Test Execution model."""
    
    @pytest.mark.asyncio
    async def test_create_execution(self, test_db: AsyncSession, test_project, test_agent_config):
        """Test creating an execution record."""
        from app.models.execution import Execution
        
        execution = Execution(
            project_id=test_project.id,
            agent_id=test_agent_config.id,
            status="pending",
            input_data={"task": "test task"},
        )
        test_db.add(execution)
        await test_db.commit()
        await test_db.refresh(execution)
        
        assert execution.id is not None
        assert execution.status == "pending"
        assert execution.project_id == test_project.id

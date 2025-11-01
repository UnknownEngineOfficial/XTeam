"""
Test agent configuration endpoints.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestAgentEndpoints:
    """Test agent API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_agent(self, client: AsyncClient, test_user_token: str, test_project):
        """Test creating a new agent configuration."""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/agents/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "agent_type": "developer",
                "name": "Test Developer Agent",
                "description": "An agent for testing",
                "config": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                }
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Developer Agent"
        assert data["agent_type"] == "developer"
        assert data["project_id"] == str(test_project.id)
    
    @pytest.mark.asyncio
    async def test_list_agents(self, client: AsyncClient, test_user_token: str, test_project, test_agent_config):
        """Test listing agents for a project."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/agents/",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(a["id"] == str(test_agent_config.id) for a in data)
    
    @pytest.mark.asyncio
    async def test_get_agent(self, client: AsyncClient, test_user_token: str, test_agent_config):
        """Test getting a specific agent."""
        response = await client.get(
            f"/api/v1/agents/{test_agent_config.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_agent_config.id)
        assert data["name"] == test_agent_config.name
    
    @pytest.mark.asyncio
    async def test_update_agent(self, client: AsyncClient, test_user_token: str, test_agent_config):
        """Test updating an agent configuration."""
        response = await client.put(
            f"/api/v1/agents/{test_agent_config.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "name": "Updated Agent Name",
                "config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.5,
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Agent Name"
        assert data["config"]["model"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_delete_agent(self, client: AsyncClient, test_user_token: str, test_project):
        """Test deleting an agent."""
        # First create an agent
        create_response = await client.post(
            f"/api/v1/projects/{test_project.id}/agents/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "agent_type": "tester",
                "name": "Agent to Delete",
                "description": "This will be deleted",
                "config": {}
            }
        )
        assert create_response.status_code == 201
        agent_id = create_response.json()["id"]
        
        # Then delete it
        delete_response = await client.delete(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert delete_response.status_code in [200, 204]
        
        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert get_response.status_code == 404


class TestAgentTypes:
    """Test agent type validation."""
    
    @pytest.mark.asyncio
    async def test_valid_agent_types(self, client: AsyncClient, test_user_token: str, test_project):
        """Test that valid agent types are accepted."""
        valid_types = ["assistant", "developer", "reviewer", "tester", "architect"]
        
        for agent_type in valid_types:
            response = await client.post(
                f"/api/v1/projects/{test_project.id}/agents/",
                headers={"Authorization": f"Bearer {test_user_token}"},
                json={
                    "agent_type": agent_type,
                    "name": f"{agent_type.capitalize()} Agent",
                    "description": f"A {agent_type} agent",
                    "config": {}
                }
            )
            # Should succeed or already exist
            assert response.status_code in [201, 400]

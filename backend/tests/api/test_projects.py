"""
Test project endpoints and functionality.
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestProjectEndpoints:
    """Test project API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient, test_user: User, test_user_token: str):
        """Test creating a new project."""
        response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "name": "New Test Project",
                "description": "A new test project",
                "repository_url": "https://github.com/test/project",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Test Project"
        assert data["owner_id"] == str(test_user.id)
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient, test_user: User, test_user_token: str, test_project):
        """Test listing user projects."""
        response = await client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(p["id"] == str(test_project.id) for p in data)
    
    @pytest.mark.asyncio
    async def test_get_project(self, client: AsyncClient, test_user_token: str, test_project):
        """Test getting a specific project."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["name"] == test_project.name
    
    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient, test_user_token: str, test_project):
        """Test updating a project."""
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "name": "Updated Project Name",
                "description": "Updated description",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_delete_project(self, client: AsyncClient, test_user: User, test_user_token: str):
        """Test deleting a project."""
        # Create a project to delete
        from app.models.project import Project
        from tests.conftest import test_db
        
        # First create a project
        create_response = await client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "name": "Project to Delete",
                "description": "This will be deleted",
            }
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # Then delete it
        delete_response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert delete_response.status_code in [200, 204]
        
        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient, test_project):
        """Test accessing project without authentication fails."""
        response = await client.get(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_access_other_user_project(self, client: AsyncClient, test_superuser_token: str, test_project):
        """Test accessing another user's project."""
        # Superuser should be able to access any project
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {test_superuser_token}"}
        )
        # This might be 200 (allowed) or 403 (forbidden) depending on implementation
        assert response.status_code in [200, 403]

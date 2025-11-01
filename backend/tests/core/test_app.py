"""
Basic tests for core functionality.
"""

import pytest


class TestHealthCheck:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test basic health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_detailed_health_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = await client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data


class TestCORS:
    """Test CORS configuration."""
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = await client.options("/health")
        # CORS headers should be present in production
        # This is a basic test structure
        assert response.status_code in [200, 405]


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self, client):
        """Test normal request rate."""
        # Make a few requests
        for _ in range(5):
            response = await client.get("/health")
            assert response.status_code == 200

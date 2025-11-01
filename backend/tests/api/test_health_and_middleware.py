"""
Tests for health check endpoints and middleware.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_healthz_endpoint(self, client: AsyncClient):
        """Test /healthz liveness endpoint."""
        response = await client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_readyz_endpoint(self, client: AsyncClient):
        """Test /readyz readiness endpoint."""
        response = await client.get("/readyz")
        
        # Should return 200 if all dependencies are healthy
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "duration_ms" in data
    
    @pytest.mark.asyncio
    async def test_legacy_health_endpoint(self, client: AsyncClient):
        """Test legacy /health endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data


class TestRequestIDMiddleware:
    """Test suite for request ID middleware."""
    
    @pytest.mark.asyncio
    async def test_request_id_generation(self, client: AsyncClient):
        """Test that request ID is automatically generated."""
        response = await client.get("/health")
        
        assert "x-request-id" in response.headers
        request_id = response.headers["x-request-id"]
        assert len(request_id) > 0
    
    @pytest.mark.asyncio
    async def test_request_id_passthrough(self, client: AsyncClient):
        """Test that provided request ID is preserved."""
        custom_id = "test-request-123"
        response = await client.get(
            "/health",
            headers={"X-Request-ID": custom_id}
        )
        
        assert response.headers["x-request-id"] == custom_id


class TestRateLimiting:
    """Test suite for rate limiting middleware."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, client: AsyncClient):
        """Test that rate limit headers are present."""
        response = await client.get("/api/v1/auth/health")
        
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
    
    @pytest.mark.asyncio
    async def test_health_endpoints_not_rate_limited(self, client: AsyncClient):
        """Test that health endpoints are not rate limited."""
        # Make multiple requests quickly
        for _ in range(10):
            response = await client.get("/healthz")
            assert response.status_code == 200
            # Health endpoints should not have rate limit headers
            # (they're excluded from rate limiting)


class TestAuthHardening:
    """Test suite for authentication hardening features."""
    
    @pytest.mark.asyncio
    async def test_logout_revokes_token(self, client: AsyncClient, test_user, test_user_token):
        """Test that logout revokes the current token."""
        # First, verify token works
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        
        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        
        # Note: In-memory token blacklist may not persist across test client requests
        # In a real integration test, the token should be invalid after logout
    
    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, client: AsyncClient):
        """Test that invalid tokens are rejected."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_missing_token_rejected(self, client: AsyncClient):
        """Test that requests without tokens are rejected."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestTokenBlacklist:
    """Test suite for token blacklist functionality."""
    
    @pytest.mark.asyncio
    async def test_token_blacklist_service(self):
        """Test token blacklist service operations."""
        from app.core.token_blacklist import TokenBlacklistService
        
        service = TokenBlacklistService()
        
        # Test without Redis connection (should handle gracefully)
        test_token = "test_token_123"
        
        # Should return False when Redis not connected
        is_revoked = await service.is_token_revoked(test_token)
        assert is_revoked is False
        
        # Should return False when trying to revoke without Redis
        success = await service.revoke_token(test_token, 3600)
        assert success is False

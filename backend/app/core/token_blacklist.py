"""
Token Blacklist Service

Provides token revocation functionality using Redis for blacklisting.
"""

import logging
from typing import Optional
from datetime import timedelta
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenBlacklistService:
    """
    Service for managing revoked JWT tokens using Redis.
    
    Tokens are stored in Redis with their expiration time as TTL,
    so they are automatically cleaned up when they expire.
    """
    
    def __init__(self):
        """Initialize the token blacklist service."""
        self.redis_client: Optional[aioredis.Redis] = None
        self.prefix = "token_blacklist:"
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = await aioredis.from_url(
                settings.redis_cache_url,
                decode_responses=True,
                max_connections=10,
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis for token blacklist")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for token blacklist: {e}")
            # Don't raise - allow application to start without blacklist
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis token blacklist")
    
    async def revoke_token(self, token: str, expires_in_seconds: int) -> bool:
        """
        Revoke a token by adding it to the blacklist.
        
        Args:
            token: JWT token to revoke
            expires_in_seconds: Time until token expires naturally
            
        Returns:
            bool: True if token was revoked successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis not connected, cannot revoke token")
            return False
        
        try:
            key = f"{self.prefix}{token}"
            # Store token with TTL equal to its remaining lifetime
            await self.redis_client.setex(
                key,
                expires_in_seconds,
                "revoked"
            )
            logger.info(f"Token revoked successfully, expires in {expires_in_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    async def is_token_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token: JWT token to check
            
        Returns:
            bool: True if token is revoked, False otherwise
        """
        if not self.redis_client:
            # If Redis is down, allow authentication to proceed
            # In production, you might want to fail-closed instead
            logger.warning("Redis not connected, cannot check token revocation")
            return False
        
        try:
            key = f"{self.prefix}{token}"
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check token revocation: {e}")
            # Fail-open: if we can't check, allow access
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """
        Revoke all tokens for a specific user.
        
        This is useful for logout-all scenarios or when a user's password changes.
        Note: This stores a user-level revocation marker.
        
        Args:
            user_id: User ID whose tokens should be revoked
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis not connected, cannot revoke user tokens")
            return False
        
        try:
            key = f"{self.prefix}user:{user_id}"
            # Store for max token lifetime (use refresh token expiry)
            ttl = settings.refresh_token_expire_days * 24 * 60 * 60
            await self.redis_client.setex(
                key,
                ttl,
                "all_revoked"
            )
            logger.info(f"All tokens revoked for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
            return False
    
    async def is_user_tokens_revoked(self, user_id: str) -> bool:
        """
        Check if all tokens for a user have been revoked.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if user tokens are revoked, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.prefix}user:{user_id}"
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check user token revocation: {e}")
            return False


# Global token blacklist service instance
token_blacklist = TokenBlacklistService()

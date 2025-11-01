"""
Agents API Endpoints

This module defines FastAPI endpoints for agent configuration management including
per-user, per-agent LLM settings and preset management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.agent_config import AgentRole, LLMProvider
from app.schemas.agent_config import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    AgentConfigDetailResponse,
    AgentConfigListResponse,
    AgentConfigByRoleResponse,
    PresetConfig,
    PresetListResponse,
    CloneConfigRequest,
    ValidateConfigRequest,
    ValidateConfigResponse,
    TestConfigRequest,
    TestConfigResponse,
    AgentConfigErrorResponse,
)
from app.services.agent_service import AgentService, get_agent_service
from app.api.deps import get_current_user

# ============================================================================
# Module Constants
# ============================================================================

# Provider-to-API-key setting mapping
# Maps LLM provider names to their corresponding settings attribute names
PROVIDER_API_KEY_SETTINGS = {
    "openai": "openai_api_key",
    "azure_openai": "azure_openai_api_key",
    "groq": "groq_api_key",
    "ollama": "",  # Ollama doesn't need an API key
}

# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(
    tags=["Agents"],
    responses={
        401: {"model": AgentConfigErrorResponse, "description": "Unauthorized"},
        403: {"model": AgentConfigErrorResponse, "description": "Forbidden"},
        404: {"model": AgentConfigErrorResponse, "description": "Not Found"},
        422: {"model": AgentConfigErrorResponse, "description": "Validation Error"},
        500: {"model": AgentConfigErrorResponse, "description": "Internal Server Error"},
    },
)


# ============================================================================
# List Agent Configurations Endpoint
# ============================================================================

@router.get(
    "/config",
    response_model=AgentConfigListResponse,
    status_code=status.HTTP_200_OK,
    summary="List agent configurations",
    description="Get all agent configurations for the current user",
)
async def list_agent_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    agent_role: Optional[str] = Query(None, description="Filter by agent role"),
    active_only: bool = Query(True, description="Return only active configurations"),
) -> AgentConfigListResponse:
    """
    List all agent configurations for the current user.
    
    This endpoint returns a list of all agent configurations owned by the user,
    with optional filtering by agent role and active status.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        agent_role: Optional agent role filter
        active_only: Whether to return only active configurations
        
    Returns:
        AgentConfigListResponse: List of agent configurations
        
    Example:
        GET /api/v1/agents/config
        GET /api/v1/agents/config?agent_role=architect&active_only=true
    """
    try:
        # Parse agent role if provided
        role = None
        if agent_role:
            try:
                role = AgentRole(agent_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent role: {agent_role}",
                )
        
        service = get_agent_service(db)
        configs = await service.get_user_agent_configs(
            str(current_user.id),
            agent_role=role,
            active_only=active_only,
        )
        
        return configs
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent configurations",
        )


# ============================================================================
# Create Agent Configuration Endpoint
# ============================================================================

@router.post(
    "/config",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent configuration",
    description="Create a new agent configuration for the current user",
)
async def create_agent_config(
    config_data: AgentConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """
    Create a new agent configuration.
    
    This endpoint creates a new agent configuration with specified LLM settings.
    
    Args:
        config_data: Configuration creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigResponse: Created configuration
        
    Raises:
        HTTPException: 400 Bad Request if configuration is invalid
        
    Example:
        POST /api/v1/agents/config
        {
            "agent_role": "architect",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    """
    try:
        service = get_agent_service(db)
        config = await service.create_agent_config(str(current_user.id), config_data)
        
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent configuration",
        )


# ============================================================================
# Get Agent Configuration by Role Endpoint
# ============================================================================

@router.get(
    "/config/{agent_role}",
    response_model=AgentConfigByRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get configurations for agent role",
    description="Get all configurations for a specific agent role",
)
async def get_configs_by_role(
    agent_role: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigByRoleResponse:
    """
    Get all configurations for a specific agent role.
    
    This endpoint returns all configurations for a specific agent role,
    with the default configuration highlighted.
    
    Args:
        agent_role: Agent role (product_manager, architect, engineer, qa_engineer, project_manager, custom)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigByRoleResponse: Configurations for the role
        
    Raises:
        HTTPException: 400 Bad Request if agent role is invalid
        HTTPException: 404 Not Found if no configurations found
        
    Example:
        GET /api/v1/agents/config/architect
    """
    try:
        # Parse agent role
        try:
            role = AgentRole(agent_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent role: {agent_role}",
            )
        
        service = get_agent_service(db)
        configs = await service.get_configs_by_role(str(current_user.id), role)
        
        if not configs.all_configs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No configurations found for role: {agent_role}",
            )
        
        return configs
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configurations",
        )


# ============================================================================
# Get Specific Agent Configuration Endpoint
# ============================================================================

@router.get(
    "/config/{agent_role}/default",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get default configuration for role",
    description="Get the default agent configuration for a specific role",
)
async def get_default_config_for_role(
    agent_role: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """
    Get the default configuration for a specific agent role.
    
    This endpoint returns the default configuration for a specific agent role.
    
    Args:
        agent_role: Agent role
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigResponse: Default configuration for the role
        
    Raises:
        HTTPException: 400 Bad Request if agent role is invalid
        HTTPException: 404 Not Found if no default configuration found
        
    Example:
        GET /api/v1/agents/config/architect/default
    """
    try:
        # Parse agent role
        try:
            role = AgentRole(agent_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent role: {agent_role}",
            )
        
        service = get_agent_service(db)
        config = await service.get_agent_config_for_role(
            str(current_user.id),
            role,
            use_default=True,
        )
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No default configuration found for role: {agent_role}",
            )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration",
        )


# ============================================================================
# Update Agent Configuration Endpoint
# ============================================================================

@router.put(
    "/config/{config_id}",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Update agent configuration",
    description="Update an existing agent configuration",
)
async def update_agent_config(
    config_id: str,
    update_data: AgentConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """
    Update an agent configuration.
    
    This endpoint allows updating agent configuration parameters.
    
    Args:
        config_id: Configuration ID
        update_data: Update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigResponse: Updated configuration
        
    Raises:
        HTTPException: 404 Not Found if configuration not found
        HTTPException: 403 Forbidden if user is not the owner
        HTTPException: 400 Bad Request if update is invalid
        
    Example:
        PUT /api/v1/agents/config/550e8400-e29b-41d4-a716-446655440000
        {
            "temperature": 0.8,
            "max_tokens": 3000
        }
    """
    try:
        service = get_agent_service(db)
        config = await service.update_agent_config(
            config_id,
            str(current_user.id),
            update_data,
        )
        
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this configuration",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration",
        )


# ============================================================================
# Set Default Configuration Endpoint
# ============================================================================

@router.post(
    "/config/{config_id}/set-default",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Set as default configuration",
    description="Set a configuration as default for its agent role",
)
async def set_default_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """
    Set a configuration as default for its agent role.
    
    This endpoint sets a configuration as the default for its agent role.
    
    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigResponse: Updated configuration
        
    Raises:
        HTTPException: 404 Not Found if configuration not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        POST /api/v1/agents/config/550e8400-e29b-41d4-a716-446655440000/set-default
    """
    try:
        service = get_agent_service(db)
        config = await service.set_default_config(config_id, str(current_user.id))
        
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default configuration",
        )


# ============================================================================
# Delete Agent Configuration Endpoint
# ============================================================================

@router.delete(
    "/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent configuration",
    description="Delete an agent configuration",
)
async def delete_agent_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an agent configuration.
    
    This endpoint deletes an agent configuration.
    
    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: 404 Not Found if configuration not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        DELETE /api/v1/agents/config/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        service = get_agent_service(db)
        deleted = await service.delete_agent_config(config_id, str(current_user.id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration not found",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete configuration",
        )


# ============================================================================
# Preset Endpoints
# ============================================================================

@router.get(
    "/presets",
    response_model=PresetListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get available presets",
    description="Get list of available preset configurations",
)
async def get_presets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresetListResponse:
    """
    Get available preset configurations.
    
    This endpoint returns a list of available preset configurations
    that can be applied to the user's agents.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PresetListResponse: List of available presets
        
    Example:
        GET /api/v1/agents/presets
    """
    try:
        service = get_agent_service(db)
        presets = await service.get_presets()
        
        return PresetListResponse(presets=presets)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve presets",
        )


@router.post(
    "/presets/{preset_name}/apply",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply preset configuration",
    description="Apply a preset configuration for the current user",
)
async def apply_preset(
    preset_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """
    Apply a preset configuration.
    
    This endpoint applies a preset configuration for the current user.
    
    Args:
        preset_name: Preset name
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigResponse: Created configuration from preset
        
    Raises:
        HTTPException: 404 Not Found if preset not found
        
    Example:
        POST /api/v1/agents/presets/GPT-4%20Architect/apply
    """
    try:
        service = get_agent_service(db)
        config = await service.apply_preset(str(current_user.id), preset_name)
        
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply preset",
        )


# ============================================================================
# Clone Configuration Endpoint
# ============================================================================

@router.post(
    "/config/{config_id}/clone",
    response_model=AgentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone configuration",
    description="Clone a configuration to another user",
)
async def clone_config(
    config_id: str,
    clone_request: CloneConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentConfigResponse:
    """
    Clone a configuration to another user.
    
    This endpoint clones a configuration to another user.
    Only the configuration owner can clone their configurations.
    
    Args:
        config_id: Configuration ID to clone
        clone_request: Clone request data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AgentConfigResponse: Cloned configuration
        
    Raises:
        HTTPException: 404 Not Found if configuration not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        POST /api/v1/agents/config/550e8400-e29b-41d4-a716-446655440000/clone
        {
            "target_user_id": "550e8400-e29b-41d4-a716-446655440001",
            "target_agent_role": "architect"
        }
    """
    try:
        service = get_agent_service(db)
        
        # Parse target role if provided
        target_role = None
        if clone_request.target_agent_role:
            target_role = AgentRole(clone_request.target_agent_role.value)
        
        config = await service.clone_config(
            config_id,
            str(current_user.id),
            clone_request.target_user_id,
            target_role,
        )
        
        return config
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone configuration",
        )


# ============================================================================
# Validation Endpoint
# ============================================================================

@router.post(
    "/validate",
    response_model=ValidateConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate configuration",
    description="Validate agent configuration parameters",
)
async def validate_config(
    config: ValidateConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ValidateConfigResponse:
    """
    Validate agent configuration parameters.
    
    This endpoint validates agent configuration parameters without saving.
    
    Args:
        config: Configuration to validate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ValidateConfigResponse: Validation result
        
    Example:
        POST /api/v1/agents/validate
        {
            "agent_role": "architect",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    """
    try:
        service = get_agent_service(db)
        validation = await service.validate_config(config)
        
        return validation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate configuration",
        )


# ============================================================================
# Test Configuration Endpoint
# ============================================================================

@router.post(
    "/test",
    response_model=TestConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Test configuration",
    description="Test an agent configuration with a sample prompt",
)
async def test_config(
    test_request: TestConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestConfigResponse:
    """
    Test an agent configuration.
    
    This endpoint tests an agent configuration by sending a sample prompt
    to the configured LLM and returning the response.
    
    Args:
        test_request: Test request data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TestConfigResponse: Test result with LLM response
        
    Raises:
        HTTPException: 404 Not Found if configuration not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        POST /api/v1/agents/test
        {
            "config_id": "550e8400-e29b-41d4-a716-446655440000",
            "test_prompt": "Design a simple REST API"
        }
    """
    try:
        service = get_agent_service(db)
        
        # Verify configuration exists and user has access
        config = await service.get_agent_config(
            test_request.config_id,
            user_id=str(current_user.id),
        )
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration not found",
            )
        
        # Get LLM client from registry
        from app.metagpt_integration.llm_registry import get_llm_client
        from app.core.config import settings
        import time
        
        try:
            # Get API key from settings using module constant mapping
            from app.core.config import settings
            import time
            
            provider = config.llm_provider.value
            api_key_setting = PROVIDER_API_KEY_SETTINGS.get(provider, "")
            
            # Get API key from settings if setting name is provided
            api_key = getattr(settings, api_key_setting, "") if api_key_setting else ""
            
            if not api_key and provider != "ollama":
                return TestConfigResponse(
                    success=False,
                    response=None,
                    duration_ms=None,
                    error=f"API key not configured for provider: {provider}",
                )
            
            # Create LLM client
            llm_client = get_llm_client(
                provider=config.llm_provider.value,
                model=config.llm_model,
                api_key=api_key,
                cache=False,  # Don't cache test clients
            )
            
            # Validate connection
            is_valid = await llm_client.validate_connection()
            if not is_valid:
                return TestConfigResponse(
                    success=False,
                    response=None,
                    duration_ms=None,
                    error="Failed to connect to LLM provider",
                )
            
            # Test with prompt
            start_time = time.time()
            response_text = await llm_client.generate(
                prompt=test_request.test_prompt,
                temperature=config.temperature,
                max_tokens=int(config.max_tokens),
            )
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            
            return TestConfigResponse(
                success=True,
                response=response_text,
                duration_ms=duration_ms,
                error=None,
            )
            
        except ImportError as e:
            return TestConfigResponse(
                success=False,
                response=None,
                duration_ms=None,
                error=f"LLM provider package not installed: {str(e)}",
            )
        except Exception as e:
            return TestConfigResponse(
                success=False,
                response=None,
                duration_ms=None,
                error=str(e),
            )
        
    except HTTPException:
        raise
    except Exception as e:
        return TestConfigResponse(
            success=False,
            response=None,
            duration_ms=None,
            error=str(e),
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if agents service is healthy",
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    This endpoint can be used to verify that the agents service is running.
    
    Returns:
        dict: Health status
        
    Example:
        GET /api/v1/agents/health
    """
    return {"status": "healthy", "service": "agents"}

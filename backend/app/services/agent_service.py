"""
Agent Service

This module provides business logic for agent configuration management including
CRUD operations and agent-related utilities.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_config import AgentConfig, AgentRole, LLMProvider
from app.models.user import User
from app.schemas.agent_config import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    AgentConfigDetailResponse,
    AgentConfigListResponse,
    AgentConfigByRoleResponse,
    PresetConfig,
    ValidateConfigRequest,
    ValidateConfigResponse,
)


# ============================================================================
# Default Preset Configurations
# ============================================================================

DEFAULT_PRESETS = [
    PresetConfig(
        name="GPT-4 Architect",
        description="High-quality architecture design with GPT-4",
        agent_role=AgentRole.ARCHITECT,
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
        system_prompt="You are an expert system architect. Design scalable, maintainable systems.",
    ),
    PresetConfig(
        name="GPT-4 Engineer",
        description="High-quality code generation with GPT-4",
        agent_role=AgentRole.ENGINEER,
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        temperature=0.5,
        max_tokens=3000,
        system_prompt="You are an expert software engineer. Write clean, efficient, well-documented code.",
    ),
    PresetConfig(
        name="GPT-3.5 Turbo Engineer",
        description="Fast code generation with GPT-3.5 Turbo",
        agent_role=AgentRole.ENGINEER,
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=2000,
        system_prompt="You are a software engineer. Write functional code.",
    ),
    PresetConfig(
        name="Groq Fast Engineer",
        description="Ultra-fast code generation with Groq",
        agent_role=AgentRole.ENGINEER,
        llm_provider=LLMProvider.GROQ,
        llm_model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=2000,
        system_prompt="You are a software engineer. Write functional code quickly.",
    ),
    PresetConfig(
        name="GPT-4 QA Engineer",
        description="Comprehensive testing with GPT-4",
        agent_role=AgentRole.QA_ENGINEER,
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        temperature=0.5,
        max_tokens=2000,
        system_prompt="You are a QA engineer. Write comprehensive tests and identify edge cases.",
    ),
    PresetConfig(
        name="GPT-4 Product Manager",
        description="Strategic planning with GPT-4",
        agent_role=AgentRole.PRODUCT_MANAGER,
        llm_provider=LLMProvider.OPENAI,
        llm_model="gpt-4",
        temperature=0.8,
        max_tokens=1500,
        system_prompt="You are a product manager. Create detailed requirements and specifications.",
    ),
]


# ============================================================================
# Agent Service Class
# ============================================================================

class AgentService:
    """
    Service class for agent configuration management.
    
    Provides CRUD operations and business logic for agent configurations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize agent service.
        
        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # Create Operations
    # ========================================================================

    async def create_agent_config(
        self,
        user_id: str,
        config_data: AgentConfigCreate,
    ) -> AgentConfigResponse:
        """
        Create a new agent configuration.
        
        Args:
            user_id: User ID
            config_data: Configuration creation data
            
        Returns:
            AgentConfigResponse: Created configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        config_data_dict = config_data.dict()
        validate_request = ValidateConfigRequest(**config_data_dict)
        validation = await self.validate_config(validate_request)
        
        if not validation.valid:
            raise ValueError(f"Invalid configuration: {', '.join(validation.errors)}")
        
        # Check if default config already exists for this role
        if config_data.is_default:
            await self._unset_default_for_role(user_id, config_data.agent_role)
        
        # Create new config
        new_config = AgentConfig(
            user_id=user_id,
            agent_role=config_data.agent_role,
            agent_name=config_data.agent_name,
            llm_provider=config_data.llm_provider,
            llm_model=config_data.llm_model,
            temperature=config_data.temperature,
            max_tokens=config_data.max_tokens,
            top_p=config_data.top_p,
            frequency_penalty=config_data.frequency_penalty,
            presence_penalty=config_data.presence_penalty,
            parameters=config_data.parameters,
            system_prompt=config_data.system_prompt,
            is_active=True,
            is_default=config_data.is_default,
        )
        
        # Save to database
        self.db.add(new_config)
        await self.db.commit()
        await self.db.refresh(new_config)
        
        return AgentConfigResponse.from_attributes(new_config)

    # ========================================================================
    # Read Operations
    # ========================================================================

    async def get_agent_config(
        self,
        config_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[AgentConfigDetailResponse]:
        """
        Get an agent configuration by ID.
        
        Args:
            config_id: Configuration ID
            user_id: Optional user ID for permission check
            
        Returns:
            Optional[AgentConfigDetailResponse]: Configuration or None if not found
            
        Raises:
            PermissionError: If user is not the owner
        """
        result = await self.db.execute(
            select(AgentConfig).where(AgentConfig.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return None
        
        # Check permissions
        if user_id and str(config.user_id) != user_id:
            raise PermissionError("You do not have permission to access this configuration")
        
        # Convert to response with LLM config
        response = AgentConfigDetailResponse.from_attributes(config)
        response.llm_config = config.get_llm_config()
        response.agent_config = config.get_agent_config()
        
        return response

    async def get_agent_config_for_role(
        self,
        user_id: str,
        agent_role: AgentRole,
        use_default: bool = True,
    ) -> Optional[AgentConfigResponse]:
        """
        Get agent configuration for a specific role.
        
        Returns the default configuration for the role if use_default is True,
        otherwise returns the first active configuration.
        
        Args:
            user_id: User ID
            agent_role: Agent role
            use_default: Whether to prefer default configuration
            
        Returns:
            Optional[AgentConfigResponse]: Configuration or None if not found
        """
        query = select(AgentConfig).where(
            and_(
                AgentConfig.user_id == user_id,
                AgentConfig.agent_role == agent_role,
                AgentConfig.is_active == True,
            )
        )
        
        if use_default:
            query = query.order_by(AgentConfig.is_default.desc())
        
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        
        return AgentConfigResponse.from_attributes(config) if config else None

    async def get_user_agent_configs(
        self,
        user_id: str,
        agent_role: Optional[AgentRole] = None,
        active_only: bool = True,
    ) -> AgentConfigListResponse:
        """
        Get all agent configurations for a user.
        
        Args:
            user_id: User ID
            agent_role: Optional filter by agent role
            active_only: Whether to return only active configurations
            
        Returns:
            AgentConfigListResponse: List of configurations
        """
        query = select(AgentConfig).where(AgentConfig.user_id == user_id)
        
        if agent_role:
            query = query.where(AgentConfig.agent_role == agent_role)
        
        if active_only:
            query = query.where(AgentConfig.is_active == True)
        
        # Order by role and default status
        query = query.order_by(
            AgentConfig.agent_role,
            AgentConfig.is_default.desc(),
        )
        
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        # Convert to responses
        config_responses = [
            AgentConfigResponse.from_attributes(c) for c in configs
        ]
        
        return AgentConfigListResponse(
            total=len(config_responses),
            page=1,
            page_size=len(config_responses),
            configs=config_responses,
        )

    async def get_configs_by_role(
        self,
        user_id: str,
        agent_role: AgentRole,
    ) -> AgentConfigByRoleResponse:
        """
        Get all configurations for a specific role, with default highlighted.
        
        Args:
            user_id: User ID
            agent_role: Agent role
            
        Returns:
            AgentConfigByRoleResponse: Configurations grouped by role
        """
        query = select(AgentConfig).where(
            and_(
                AgentConfig.user_id == user_id,
                AgentConfig.agent_role == agent_role,
            )
        ).order_by(AgentConfig.is_default.desc())
        
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        # Find default config
        default_config = None
        all_configs = []
        
        for config in configs:
            config_response = AgentConfigResponse.from_attributes(config)
            all_configs.append(config_response)
            
            if config.is_default:
                default_config = config_response
        
        return AgentConfigByRoleResponse(
            role=agent_role.value,
            default_config=default_config,
            all_configs=all_configs,
        )

    # ========================================================================
    # Update Operations
    # ========================================================================

    async def update_agent_config(
        self,
        config_id: str,
        user_id: str,
        update_data: AgentConfigUpdate,
    ) -> AgentConfigResponse:
        """
        Update an agent configuration.
        
        Args:
            config_id: Configuration ID
            user_id: User ID (for permission check)
            update_data: Update data
            
        Returns:
            AgentConfigResponse: Updated configuration
            
        Raises:
            PermissionError: If user is not the owner
            ValueError: If configuration not found or update invalid
        """
        # Get config and verify ownership
        result = await self.db.execute(
            select(AgentConfig).where(
                and_(
                    AgentConfig.id == config_id,
                    AgentConfig.user_id == user_id,
                )
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Update fields
        if update_data.agent_name is not None:
            config.agent_name = update_data.agent_name
        
        if update_data.llm_model is not None:
            config.llm_model = update_data.llm_model
        
        if update_data.temperature is not None:
            config.temperature = update_data.temperature
        
        if update_data.max_tokens is not None:
            config.max_tokens = update_data.max_tokens
        
        if update_data.top_p is not None:
            config.top_p = update_data.top_p
        
        if update_data.frequency_penalty is not None:
            config.frequency_penalty = update_data.frequency_penalty
        
        if update_data.presence_penalty is not None:
            config.presence_penalty = update_data.presence_penalty
        
        if update_data.system_prompt is not None:
            config.system_prompt = update_data.system_prompt
        
        if update_data.parameters is not None:
            config.parameters = update_data.parameters
        
        if update_data.is_active is not None:
            config.is_active = update_data.is_active
        
        if update_data.is_default is not None:
            if update_data.is_default:
                await self._unset_default_for_role(user_id, config.agent_role)
            config.is_default = update_data.is_default
        
        # Validate updated config
        config.validate_parameters()
        
        # Save changes
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return AgentConfigResponse.from_attributes(config)

    async def set_default_config(
        self,
        config_id: str,
        user_id: str,
    ) -> AgentConfigResponse:
        """
        Set a configuration as default for its role.
        
        Args:
            config_id: Configuration ID
            user_id: User ID
            
        Returns:
            AgentConfigResponse: Updated configuration
            
        Raises:
            ValueError: If configuration not found
        """
        # Get config
        result = await self.db.execute(
            select(AgentConfig).where(
                and_(
                    AgentConfig.id == config_id,
                    AgentConfig.user_id == user_id,
                )
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Unset other defaults for this role
        await self._unset_default_for_role(user_id, config.agent_role)
        
        # Set as default
        config.set_as_default()
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return AgentConfigResponse.from_attributes(config)

    # ========================================================================
    # Delete Operations
    # ========================================================================

    async def delete_agent_config(
        self,
        config_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete an agent configuration.
        
        Args:
            config_id: Configuration ID
            user_id: User ID (for permission check)
            
        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.db.execute(
            select(AgentConfig).where(
                and_(
                    AgentConfig.id == config_id,
                    AgentConfig.user_id == user_id,
                )
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return False
        
        await self.db.delete(config)
        await self.db.commit()
        
        return True

    # ========================================================================
    # Validation Operations
    # ========================================================================

    async def validate_config(
        self,
        config: ValidateConfigRequest,
    ) -> ValidateConfigResponse:
        """
        Validate agent configuration parameters.
        
        Args:
            config: Configuration to validate
            
        Returns:
            ValidateConfigResponse: Validation result
        """
        errors = []
        warnings = []
        
        # Validate temperature
        if not 0 <= config.temperature <= 2:
            errors.append("Temperature must be between 0 and 2")
        
        # Validate max_tokens
        if config.max_tokens <= 0:
            errors.append("Max tokens must be positive")
        
        # Validate top_p
        if not 0 <= config.top_p <= 1:
            errors.append("Top-p must be between 0 and 1")
        
        # Validate penalties
        if not -2 <= config.frequency_penalty <= 2:
            errors.append("Frequency penalty must be between -2 and 2")
        
        if not -2 <= config.presence_penalty <= 2:
            errors.append("Presence penalty must be between -2 and 2")
        
        # Warnings
        if config.temperature > 1.5:
            warnings.append("High temperature may produce less consistent results")
        
        if config.max_tokens > 4000:
            warnings.append("Very high max_tokens may increase latency")
        
        return ValidateConfigResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # ========================================================================
    # Preset Operations
    # ========================================================================

    async def get_presets(self) -> List[PresetConfig]:
        """
        Get available preset configurations.
        
        Returns:
            List[PresetConfig]: List of preset configurations
        """
        return DEFAULT_PRESETS

    async def apply_preset(
        self,
        user_id: str,
        preset_name: str,
    ) -> AgentConfigResponse:
        """
        Apply a preset configuration for a user.
        
        Args:
            user_id: User ID
            preset_name: Preset name
            
        Returns:
            AgentConfigResponse: Created configuration from preset
            
        Raises:
            ValueError: If preset not found
        """
        # Find preset
        preset = None
        for p in DEFAULT_PRESETS:
            if p.name == preset_name:
                preset = p
                break
        
        if not preset:
            raise ValueError(f"Preset not found: {preset_name}")
        
        # Create config from preset
        config_data = AgentConfigCreate(
            agent_role=preset.agent_role,
            agent_name=preset.name,
            llm_provider=preset.llm_provider,
            llm_model=preset.llm_model,
            temperature=preset.temperature,
            max_tokens=preset.max_tokens,
            system_prompt=preset.system_prompt,
        )
        
        return await self.create_agent_config(user_id, config_data)

    # ========================================================================
    # Clone Operations
    # ========================================================================

    async def clone_config(
        self,
        config_id: str,
        source_user_id: str,
        target_user_id: str,
        target_agent_role: Optional[AgentRole] = None,
    ) -> AgentConfigResponse:
        """
        Clone a configuration to another user.
        
        Args:
            config_id: Configuration ID to clone
            source_user_id: Source user ID
            target_user_id: Target user ID
            target_agent_role: Optional target agent role
            
        Returns:
            AgentConfigResponse: Cloned configuration
            
        Raises:
            ValueError: If source configuration not found
        """
        # Get source config
        result = await self.db.execute(
            select(AgentConfig).where(
                and_(
                    AgentConfig.id == config_id,
                    AgentConfig.user_id == source_user_id,
                )
            )
        )
        source_config = result.scalar_one_or_none()
        
        if not source_config:
            raise ValueError(f"Configuration not found: {config_id}")
        
        # Clone config
        cloned = source_config.clone(target_user_id, target_agent_role)
        
        # Save cloned config
        self.db.add(cloned)
        await self.db.commit()
        await self.db.refresh(cloned)
        
        return AgentConfigResponse.from_attributes(cloned)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _unset_default_for_role(
        self,
        user_id: str,
        agent_role: AgentRole,
    ) -> None:
        """
        Unset default configuration for a role.
        
        Args:
            user_id: User ID
            agent_role: Agent role
        """
        result = await self.db.execute(
            select(AgentConfig).where(
                and_(
                    AgentConfig.user_id == user_id,
                    AgentConfig.agent_role == agent_role,
                    AgentConfig.is_default == True,
                )
            )
        )
        default_config = result.scalar_one_or_none()
        
        if default_config:
            default_config.unset_as_default()
            self.db.add(default_config)
            await self.db.commit()

    async def check_config_exists(self, config_id: str) -> bool:
        """
        Check if a configuration exists.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            bool: True if configuration exists
        """
        result = await self.db.execute(
            select(func.count(AgentConfig.id)).where(AgentConfig.id == config_id)
        )
        return (result.scalar() or 0) > 0

    async def get_config_owner(self, config_id: str) -> Optional[str]:
        """
        Get the owner ID of a configuration.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Optional[str]: Owner ID or None if not found
        """
        result = await self.db.execute(
            select(AgentConfig.user_id).where(AgentConfig.id == config_id)
        )
        user_id = result.scalar_one_or_none()
        return str(user_id) if user_id else None

    async def get_llm_config_for_agent(
        self,
        user_id: str,
        agent_role: AgentRole,
    ) -> Dict[str, Any]:
        """
        Get LLM configuration for an agent.
        
        Args:
            user_id: User ID
            agent_role: Agent role
            
        Returns:
            Dict[str, Any]: LLM configuration
        """
        config = await self.get_agent_config_for_role(user_id, agent_role)
        
        if not config:
            # Return default config if none found
            return {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
            }
        
        # Get the full config object to access get_llm_config method
        result = await self.db.execute(
            select(AgentConfig).where(AgentConfig.id == config.id)
        )
        full_config = result.scalar_one_or_none()
        
        return full_config.get_llm_config() if full_config else {}


# ============================================================================
# Service Factory Function
# ============================================================================

def get_agent_service(db: AsyncSession) -> AgentService:
    """
    Factory function to create an AgentService instance.
    
    Args:
        db: Database session
        
    Returns:
        AgentService: Service instance
    """
    return AgentService(db)

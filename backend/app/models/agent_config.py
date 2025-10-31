"""
Agent Configuration Model

This module defines the AgentConfig ORM model for managing per-agent LLM settings.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey, Enum, Boolean, Float
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class AgentRole(str, enum.Enum):
    """Agent role enumeration based on MetaGPT roles."""
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    QA_ENGINEER = "qa_engineer"
    PROJECT_MANAGER = "project_manager"
    CUSTOM = "custom"


class LLMProvider(str, enum.Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


class AgentConfig(Base):
    """
    Agent Configuration model for managing per-agent LLM settings.
    
    This model allows users to customize LLM settings for each agent role,
    enabling fine-grained control over agent behavior and performance.
    
    Attributes:
        id: Unique configuration identifier (UUID)
        user_id: User ID who owns this configuration (FK to User)
        agent_role: Agent role (product_manager, architect, engineer, qa_engineer, project_manager, custom)
        agent_name: Optional custom agent name
        llm_provider: LLM provider (openai, azure_openai, groq, ollama, anthropic, cohere)
        llm_model: Model name/identifier for the provider
        temperature: Temperature parameter (0-2)
        max_tokens: Maximum tokens for generation
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty parameter
        presence_penalty: Presence penalty parameter
        parameters: Additional provider-specific parameters (JSON)
        system_prompt: Custom system prompt for the agent
        is_active: Whether this configuration is active
        is_default: Whether this is the default configuration for the role
        created_at: Configuration creation timestamp
        updated_at: Last configuration update timestamp
    """

    __tablename__ = "agent_configs"

    # ========================================================================
    # Primary Key
    # ========================================================================

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        doc="Unique configuration identifier"
    )

    # ========================================================================
    # Foreign Keys
    # ========================================================================

    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID who owns this configuration"
    )

    # ========================================================================
    # Agent Configuration
    # ========================================================================

    agent_role = Column(
        Enum(AgentRole),
        nullable=False,
        index=True,
        doc="Agent role"
    )

    agent_name = Column(
        String(255),
        nullable=True,
        doc="Optional custom agent name"
    )

    # ========================================================================
    # LLM Provider Configuration
    # ========================================================================

    llm_provider = Column(
        Enum(LLMProvider),
        nullable=False,
        index=True,
        doc="LLM provider"
    )

    llm_model = Column(
        String(255),
        nullable=False,
        doc="Model name/identifier for the provider"
    )

    # ========================================================================
    # LLM Parameters
    # ========================================================================

    temperature = Column(
        Float,
        default=0.7,
        nullable=False,
        doc="Temperature parameter (0-2)"
    )

    max_tokens = Column(
        Float,
        default=2000,
        nullable=False,
        doc="Maximum tokens for generation"
    )

    top_p = Column(
        Float,
        default=1.0,
        nullable=False,
        doc="Top-p sampling parameter"
    )

    frequency_penalty = Column(
        Float,
        default=0.0,
        nullable=False,
        doc="Frequency penalty parameter"
    )

    presence_penalty = Column(
        Float,
        default=0.0,
        nullable=False,
        doc="Presence penalty parameter"
    )

    # ========================================================================
    # Advanced Configuration
    # ========================================================================

    parameters = Column(
        Text,
        default="{}",
        nullable=False,
        doc="Additional provider-specific parameters"
    )

    system_prompt = Column(
        Text,
        nullable=True,
        doc="Custom system prompt for the agent"
    )

    # ========================================================================
    # Status Fields
    # ========================================================================

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether this configuration is active"
    )

    is_default = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is the default configuration for the role"
    )

    # ========================================================================
    # Timestamp Fields
    # ========================================================================

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Configuration creation timestamp"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Last configuration update timestamp"
    )

    # ========================================================================
    # Relationships
    # ========================================================================

    # Relationship to user (many configs belong to one user)
    user = relationship(
        "User",
        foreign_keys=[user_id],
        doc="Configuration owner"
    )

    # ========================================================================
    # Indexes
    # ========================================================================

    __table_args__ = (
        Index("idx_agent_config_user_id", "user_id"),
        Index("idx_agent_config_agent_role", "agent_role"),
        Index("idx_agent_config_llm_provider", "llm_provider"),
        Index("idx_agent_config_is_active", "is_active"),
        Index("idx_agent_config_is_default", "is_default"),
        Index("idx_agent_config_user_role", "user_id", "agent_role"),
        Index("idx_agent_config_user_active", "user_id", "is_active"),
    )

    # ========================================================================
    # Methods
    # ========================================================================

    def __repr__(self) -> str:
        """String representation of AgentConfig."""
        return f"<AgentConfig(id={self.id}, role={self.agent_role}, provider={self.llm_provider})>"

    def __str__(self) -> str:
        """Agent configuration display name."""
        return f"{self.agent_role.value} ({self.llm_provider.value}/{self.llm_model})"

    def to_dict(self, include_user: bool = False) -> dict:
        """
        Convert agent config to dictionary.
        
        Args:
            include_user: Whether to include user information
            
        Returns:
            dict: Agent config data as dictionary
        """
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "agent_role": self.agent_role.value if self.agent_role else None,
            "agent_name": self.agent_name,
            "llm_provider": self.llm_provider.value if self.llm_provider else None,
            "llm_model": self.llm_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "parameters": self.parameters,
            "system_prompt": self.system_prompt,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_user and self.user:
            data["user"] = {
                "id": str(self.user.id),
                "username": self.user.username,
                "email": self.user.email,
            }
        
        return data

    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get complete LLM configuration for use in agent initialization.
        
        Returns:
            dict: LLM configuration with all parameters
        """
        config = {
            "provider": self.llm_provider.value,
            "model": self.llm_model,
            "temperature": self.temperature,
            "max_tokens": int(self.max_tokens),
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        
        # Add custom parameters
        if self.parameters:
            config.update(self.parameters)
        
        return config

    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get complete agent configuration for agent initialization.
        
        Returns:
            dict: Agent configuration with role, LLM settings, and system prompt
        """
        config = {
            "role": self.agent_role.value,
            "name": self.agent_name or self.agent_role.value,
            "llm": self.get_llm_config(),
        }
        
        if self.system_prompt:
            config["system_prompt"] = self.system_prompt
        
        return config

    def validate_parameters(self) -> bool:
        """
        Validate configuration parameters.
        
        Returns:
            bool: True if all parameters are valid
            
        Raises:
            ValueError: If any parameter is invalid
        """
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        if not 0 <= self.top_p <= 1:
            raise ValueError("Top-p must be between 0 and 1")
        
        if not -2 <= self.frequency_penalty <= 2:
            raise ValueError("Frequency penalty must be between -2 and 2")
        
        if not -2 <= self.presence_penalty <= 2:
            raise ValueError("Presence penalty must be between -2 and 2")
        
        return True

    def set_as_default(self) -> None:
        """Set this configuration as default for its role."""
        self.is_default = True

    def unset_as_default(self) -> None:
        """Unset this configuration as default."""
        self.is_default = False

    def activate(self) -> None:
        """Activate this configuration."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate this configuration."""
        self.is_active = False

    def set_parameter(self, key: str, value: Any) -> None:
        """
        Set a custom parameter.
        
        Args:
            key: Parameter key
            value: Parameter value
        """
        if not self.parameters:
            self.parameters = {}
        self.parameters[key] = value

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get a custom parameter.
        
        Args:
            key: Parameter key
            default: Default value if key not found
            
        Returns:
            Parameter value or default
        """
        if not self.parameters:
            return default
        return self.parameters.get(key, default)

    def clone(self, user_id: str, agent_role: Optional[AgentRole] = None) -> "AgentConfig":
        """
        Create a clone of this configuration for another user or role.
        
        Args:
            user_id: User ID for the cloned configuration
            agent_role: Optional agent role for the clone (defaults to current role)
            
        Returns:
            AgentConfig: New cloned configuration
        """
        return AgentConfig(
            user_id=user_id,
            agent_role=agent_role or self.agent_role,
            agent_name=self.agent_name,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            parameters=self.parameters.copy() if self.parameters else {},
            system_prompt=self.system_prompt,
            is_active=self.is_active,
            is_default=False,
        )

    @classmethod
    def from_dict(cls, data: dict, user_id: str) -> "AgentConfig":
        """
        Create AgentConfig instance from dictionary.
        
        Args:
            data: Dictionary with configuration data
            user_id: User ID
            
        Returns:
            AgentConfig: New AgentConfig instance
        """
        config = cls(
            user_id=user_id,
            agent_role=AgentRole(data.get("agent_role")),
            agent_name=data.get("agent_name"),
            llm_provider=LLMProvider(data.get("llm_provider")),
            llm_model=data.get("llm_model"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            top_p=data.get("top_p", 1.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
            presence_penalty=data.get("presence_penalty", 0.0),
            parameters=data.get("parameters", {}),
            system_prompt=data.get("system_prompt"),
            is_active=data.get("is_active", True),
            is_default=data.get("is_default", False),
        )
        
        config.validate_parameters()
        return config

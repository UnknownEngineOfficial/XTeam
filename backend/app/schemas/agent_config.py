"""
Agent Configuration Schemas

This module defines Pydantic models for agent configuration API requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class AgentRoleEnum(str, Enum):
    """Agent role enumeration."""
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    QA_ENGINEER = "qa_engineer"
    PROJECT_MANAGER = "project_manager"
    CUSTOM = "custom"


class LLMProviderEnum(str, Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


# ============================================================================
# LLM Provider Configuration Schemas
# ============================================================================

class OpenAIConfig(BaseModel):
    """
    Schema for OpenAI provider configuration.
    
    Attributes:
        api_key: OpenAI API key
        organization: Optional organization ID
    """
    api_key: str = Field(..., description="OpenAI API key")
    organization: Optional[str] = Field(None, description="Optional organization ID")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "api_key": "sk-...",
                "organization": "org-..."
            }
        }


class AzureOpenAIConfig(BaseModel):
    """
    Schema for Azure OpenAI provider configuration.
    
    Attributes:
        api_key: Azure OpenAI API key
        endpoint: Azure OpenAI endpoint URL
        deployment_name: Deployment name
        api_version: API version
    """
    api_key: str = Field(..., description="Azure OpenAI API key")
    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    deployment_name: str = Field(..., description="Deployment name")
    api_version: str = Field(default="2024-02-15-preview", description="API version")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "api_key": "...",
                "endpoint": "https://your-resource.openai.azure.com/",
                "deployment_name": "gpt-4",
                "api_version": "2024-02-15-preview"
            }
        }


class GroqConfig(BaseModel):
    """
    Schema for Groq provider configuration.
    
    Attributes:
        api_key: Groq API key
    """
    api_key: str = Field(..., description="Groq API key")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "api_key": "gsk_..."
            }
        }


class OllamaConfig(BaseModel):
    """
    Schema for Ollama provider configuration.
    
    Attributes:
        base_url: Ollama base URL
        model: Model name
    """
    base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    model: str = Field(..., description="Model name")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "base_url": "http://localhost:11434",
                "model": "llama2"
            }
        }


class AnthropicConfig(BaseModel):
    """
    Schema for Anthropic provider configuration.
    
    Attributes:
        api_key: Anthropic API key
    """
    api_key: str = Field(..., description="Anthropic API key")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "api_key": "sk-ant-..."
            }
        }


class CohereConfig(BaseModel):
    """
    Schema for Cohere provider configuration.
    
    Attributes:
        api_key: Cohere API key
    """
    api_key: str = Field(..., description="Cohere API key")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "api_key": "..."
            }
        }


# ============================================================================
# Agent Configuration Creation and Update
# ============================================================================

class AgentConfigCreate(BaseModel):
    """
    Schema for agent configuration creation.
    
    Attributes:
        agent_role: Agent role
        agent_name: Optional custom agent name
        llm_provider: LLM provider
        llm_model: Model name/identifier
        temperature: Temperature parameter (0-2)
        max_tokens: Maximum tokens
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        presence_penalty: Presence penalty
        system_prompt: Custom system prompt
        parameters: Additional provider-specific parameters
    """
    agent_role: AgentRoleEnum = Field(..., description="Agent role")
    agent_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional custom agent name"
    )
    llm_provider: LLMProviderEnum = Field(..., description="LLM provider")
    llm_model: str = Field(
        ...,
        max_length=255,
        description="Model name/identifier"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="Temperature parameter (0-2)"
    )
    max_tokens: float = Field(
        default=2000,
        gt=0,
        description="Maximum tokens"
    )
    top_p: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Top-p sampling parameter"
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2,
        le=2,
        description="Frequency penalty"
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2,
        le=2,
        description="Presence penalty"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Custom system prompt"
    )
    parameters: Dict[str, Any] = Field(
        default={},
        description="Additional provider-specific parameters"
    )

    @validator("llm_model")
    def validate_llm_model(cls, v):
        """Validate LLM model is not empty."""
        if not v or not v.strip():
            raise ValueError("LLM model cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "agent_role": "architect",
                "agent_name": "System Architect",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "system_prompt": "You are an expert system architect...",
                "parameters": {}
            }
        }


class AgentConfigUpdate(BaseModel):
    """
    Schema for agent configuration update.
    
    Attributes:
        agent_name: Custom agent name
        llm_model: Model name/identifier
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        presence_penalty: Presence penalty
        system_prompt: Custom system prompt
        parameters: Additional parameters
        is_active: Whether configuration is active
        is_default: Whether configuration is default
    """
    agent_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Custom agent name"
    )
    llm_model: Optional[str] = Field(
        None,
        max_length=255,
        description="Model name/identifier"
    )
    temperature: Optional[float] = Field(
        None,
        ge=0,
        le=2,
        description="Temperature parameter"
    )
    max_tokens: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum tokens"
    )
    top_p: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Top-p sampling parameter"
    )
    frequency_penalty: Optional[float] = Field(
        None,
        ge=-2,
        le=2,
        description="Frequency penalty"
    )
    presence_penalty: Optional[float] = Field(
        None,
        ge=-2,
        le=2,
        description="Presence penalty"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Custom system prompt"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional parameters"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether configuration is active"
    )
    is_default: Optional[bool] = Field(
        None,
        description="Whether configuration is default"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "temperature": 0.8,
                "max_tokens": 3000,
                "is_active": True
            }
        }


# ============================================================================
# Agent Configuration Response Schemas
# ============================================================================

class AgentConfigResponse(BaseModel):
    """
    Schema for agent configuration response.
    
    Attributes:
        id: Configuration ID
        user_id: User ID
        agent_role: Agent role
        agent_name: Custom agent name
        llm_provider: LLM provider
        llm_model: Model name
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        presence_penalty: Presence penalty
        system_prompt: Custom system prompt
        parameters: Additional parameters
        is_active: Whether configuration is active
        is_default: Whether configuration is default
        created_at: Creation timestamp
        updated_at: Update timestamp
    """
    id: str = Field(..., description="Configuration ID")
    user_id: str = Field(..., description="User ID")
    agent_role: str = Field(..., description="Agent role")
    agent_name: Optional[str] = Field(None, description="Custom agent name")
    llm_provider: str = Field(..., description="LLM provider")
    llm_model: str = Field(..., description="Model name")
    temperature: float = Field(..., description="Temperature parameter")
    max_tokens: float = Field(..., description="Maximum tokens")
    top_p: float = Field(..., description="Top-p sampling parameter")
    frequency_penalty: float = Field(..., description="Frequency penalty")
    presence_penalty: float = Field(..., description="Presence penalty")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    parameters: Dict[str, Any] = Field(..., description="Additional parameters")
    is_active: bool = Field(..., description="Whether configuration is active")
    is_default: bool = Field(..., description="Whether configuration is default")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "agent_role": "architect",
                "agent_name": "System Architect",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "system_prompt": "You are an expert system architect...",
                "parameters": {},
                "is_active": True,
                "is_default": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T15:45:00Z"
            }
        }


class AgentConfigDetailResponse(AgentConfigResponse):
    """
    Schema for detailed agent configuration response.
    
    Extends AgentConfigResponse with:
        llm_config: Complete LLM configuration
        agent_config: Complete agent configuration
    """
    llm_config: Dict[str, Any] = Field(..., description="Complete LLM configuration")
    agent_config: Dict[str, Any] = Field(..., description="Complete agent configuration")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class AgentConfigListResponse(BaseModel):
    """
    Schema for agent configuration list response.
    
    Attributes:
        total: Total number of configurations
        page: Current page number
        page_size: Number of configurations per page
        configs: List of agent configurations
    """
    total: int = Field(..., description="Total number of configurations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of configurations per page")
    configs: List[AgentConfigResponse] = Field(..., description="List of configurations")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total": 6,
                "page": 1,
                "page_size": 10,
                "configs": []
            }
        }


class AgentConfigByRoleResponse(BaseModel):
    """
    Schema for agent configurations grouped by role.
    
    Attributes:
        role: Agent role
        default_config: Default configuration for the role
        all_configs: All configurations for the role
    """
    role: str = Field(..., description="Agent role")
    default_config: Optional[AgentConfigResponse] = Field(
        None,
        description="Default configuration"
    )
    all_configs: List[AgentConfigResponse] = Field(
        ...,
        description="All configurations for the role"
    )

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# ============================================================================
# Preset Configuration Schemas
# ============================================================================

class PresetConfig(BaseModel):
    """
    Schema for preset agent configuration.
    
    Attributes:
        name: Preset name
        description: Preset description
        agent_role: Agent role
        llm_provider: LLM provider
        llm_model: Model name
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        system_prompt: System prompt
    """
    name: str = Field(..., description="Preset name")
    description: Optional[str] = Field(None, description="Preset description")
    agent_role: AgentRoleEnum = Field(..., description="Agent role")
    llm_provider: LLMProviderEnum = Field(..., description="LLM provider")
    llm_model: str = Field(..., description="Model name")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Temperature")
    max_tokens: float = Field(default=2000, gt=0, description="Max tokens")
    system_prompt: Optional[str] = Field(None, description="System prompt")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "GPT-4 Architect",
                "description": "High-quality architecture design with GPT-4",
                "agent_role": "architect",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "system_prompt": "You are an expert system architect..."
            }
        }


class PresetListResponse(BaseModel):
    """
    Schema for preset configuration list response.
    
    Attributes:
        presets: List of available presets
    """
    presets: List[PresetConfig] = Field(..., description="List of presets")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "presets": []
            }
        }


# ============================================================================
# Clone Configuration Schema
# ============================================================================

class CloneConfigRequest(BaseModel):
    """
    Schema for cloning agent configuration.
    
    Attributes:
        target_user_id: Target user ID
        target_agent_role: Optional target agent role
    """
    target_user_id: str = Field(..., description="Target user ID")
    target_agent_role: Optional[AgentRoleEnum] = Field(
        None,
        description="Optional target agent role"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "target_user_id": "550e8400-e29b-41d4-a716-446655440002",
                "target_agent_role": "architect"
            }
        }


# ============================================================================
# Validation and Testing Schemas
# ============================================================================

class ValidateConfigRequest(BaseModel):
    """
    Schema for validating agent configuration.
    
    Attributes:
        agent_role: Agent role
        llm_provider: LLM provider
        llm_model: Model name
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        presence_penalty: Presence penalty
    """
    agent_role: AgentRoleEnum = Field(..., description="Agent role")
    llm_provider: LLMProviderEnum = Field(..., description="LLM provider")
    llm_model: str = Field(..., description="Model name")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Temperature")
    max_tokens: float = Field(default=2000, gt=0, description="Max tokens")
    top_p: float = Field(default=1.0, ge=0, le=1, description="Top-p")
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2, le=2, description="Presence penalty")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "agent_role": "architect",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }


class ValidateConfigResponse(BaseModel):
    """
    Schema for configuration validation response.
    
    Attributes:
        valid: Whether configuration is valid
        errors: List of validation errors
        warnings: List of warnings
    """
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Warnings")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": []
            }
        }


class TestConfigRequest(BaseModel):
    """
    Schema for testing agent configuration.
    
    Attributes:
        config_id: Configuration ID to test
        test_prompt: Test prompt to send
    """
    config_id: str = Field(..., description="Configuration ID")
    test_prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Test prompt"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "config_id": "550e8400-e29b-41d4-a716-446655440000",
                "test_prompt": "Design a simple REST API"
            }
        }


class TestConfigResponse(BaseModel):
    """
    Schema for configuration test response.
    
    Attributes:
        success: Whether test was successful
        response: LLM response
        duration_ms: Response duration in milliseconds
        error: Error message if test failed
    """
    success: bool = Field(..., description="Whether test was successful")
    response: Optional[str] = Field(None, description="LLM response")
    duration_ms: Optional[float] = Field(None, description="Response duration")
    error: Optional[str] = Field(None, description="Error message")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Here's a simple REST API design...",
                "duration_ms": 1250.5,
                "error": None
            }
        }


# ============================================================================
# Error Response Schemas
# ============================================================================

class AgentConfigErrorResponse(BaseModel):
    """
    Schema for agent configuration error response.
    
    Attributes:
        error: Error message
        detail: Detailed error information
        status_code: HTTP status code
    """
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "Configuration not found",
                "detail": "Configuration with ID 550e8400-e29b-41d4-a716-446655440000 does not exist",
                "status_code": 404
            }
        }

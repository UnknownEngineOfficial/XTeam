"""
LLM Registry and Factory

This module provides a factory pattern for creating and managing LLM clients
for different providers (OpenAI, Azure OpenAI, Groq, Ollama, etc.).
"""

from typing import Optional, Dict, Any, Union
from abc import ABC, abstractmethod
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Client Interface
# ============================================================================

class LLMClient(ABC):
    """
    Abstract base class for LLM clients.
    
    All LLM provider implementations should inherit from this class.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Generated text
        """
        pass

    @abstractmethod
    async def generate_with_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ):
        """
        Generate text with streaming.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Yields:
            str: Generated text chunks
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate that the LLM connection is working.
        
        Returns:
            bool: True if connection is valid
        """
        pass


# ============================================================================
# OpenAI Client Implementation
# ============================================================================

class OpenAIClient(LLMClient):
    """
    OpenAI LLM client implementation.
    
    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        organization: Optional[str] = None,
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-3.5-turbo)
            organization: Optional organization ID
        """
        try:
            import openai
            self.openai = openai
        except ImportError:
            raise ImportError("openai package is required for OpenAI client")
        
        self.api_key = api_key
        self.model = model
        self.organization = organization
        
        # Configure OpenAI client
        self.openai.api_key = api_key
        if organization:
            self.openai.organization = organization
        
        logger.info(f"Initialized OpenAI client with model: {model}")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        try:
            response = await self.openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_with_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ):
        """
        Generate text with streaming from OpenAI API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Yields:
            str: Generated text chunks
        """
        try:
            response = await self.openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )
            
            async for chunk in response:
                if "choices" in chunk:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                        
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise

    async def validate_connection(self) -> bool:
        """
        Validate OpenAI connection.
        
        Returns:
            bool: True if connection is valid
        """
        try:
            response = await self.openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False


# ============================================================================
# Azure OpenAI Client Implementation
# ============================================================================

class AzureOpenAIClient(LLMClient):
    """
    Azure OpenAI LLM client implementation.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview",
    ):
        """
        Initialize Azure OpenAI client.
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            deployment_name: Deployment name
            api_version: API version
        """
        try:
            import openai
            self.openai = openai
        except ImportError:
            raise ImportError("openai package is required for Azure OpenAI client")
        
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        # Configure Azure OpenAI client
        self.openai.api_type = "azure"
        self.openai.api_key = api_key
        self.openai.api_base = endpoint
        self.openai.api_version = api_version
        
        logger.info(f"Initialized Azure OpenAI client with deployment: {deployment_name}")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate text using Azure OpenAI API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        try:
            response = await self.openai.ChatCompletion.acreate(
                deployment_id=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI generation failed: {e}")
            raise

    async def generate_with_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ):
        """
        Generate text with streaming from Azure OpenAI API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Yields:
            str: Generated text chunks
        """
        try:
            response = await self.openai.ChatCompletion.acreate(
                deployment_id=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )
            
            async for chunk in response:
                if "choices" in chunk:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                        
        except Exception as e:
            logger.error(f"Azure OpenAI streaming failed: {e}")
            raise

    async def validate_connection(self) -> bool:
        """
        Validate Azure OpenAI connection.
        
        Returns:
            bool: True if connection is valid
        """
        try:
            response = await self.openai.ChatCompletion.acreate(
                deployment_id=self.deployment_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI connection validation failed: {e}")
            return False


# ============================================================================
# Groq Client Implementation
# ============================================================================

class GroqClient(LLMClient):
    """
    Groq LLM client implementation.
    
    Provides ultra-fast inference with Groq's LPU technology.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "mixtral-8x7b-32768",
    ):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key
            model: Model name (default: mixtral-8x7b-32768)
        """
        try:
            from groq import Groq, AsyncGroq
            self.Groq = Groq
            self.AsyncGroq = AsyncGroq
        except ImportError:
            raise ImportError("groq package is required for Groq client")
        
        self.api_key = api_key
        self.model = model
        self.client = self.AsyncGroq(api_key=api_key)
        
        logger.info(f"Initialized Groq client with model: {model}")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate text using Groq API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise

    async def generate_with_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ):
        """
        Generate text with streaming from Groq API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Yields:
            str: Generated text chunks
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}")
            raise

    async def validate_connection(self) -> bool:
        """
        Validate Groq connection.
        
        Returns:
            bool: True if connection is valid
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return True
        except Exception as e:
            logger.error(f"Groq connection validation failed: {e}")
            return False


# ============================================================================
# Ollama Client Implementation
# ============================================================================

class OllamaClient(LLMClient):
    """
    Ollama LLM client implementation.
    
    Provides local LLM inference using Ollama.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama base URL (default: http://localhost:11434)
            model: Model name (default: llama2)
        """
        try:
            import httpx
            self.httpx = httpx
        except ImportError:
            raise ImportError("httpx package is required for Ollama client")
        
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = self.httpx.AsyncClient(base_url=self.base_url)
        
        logger.info(f"Initialized Ollama client with model: {model}")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """
        Generate text using Ollama API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        try:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False,
                    **kwargs,
                },
            )
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def generate_with_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ):
        """
        Generate text with streaming from Ollama API.
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Yields:
            str: Generated text chunks
        """
        try:
            async with self.client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": True,
                    **kwargs,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                            
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise

    async def validate_connection(self) -> bool:
        """
        Validate Ollama connection.
        
        Returns:
            bool: True if connection is valid
        """
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection validation failed: {e}")
            return False


# ============================================================================
# LLM Registry and Factory
# ============================================================================

class LLMRegistry:
    """
    Registry for LLM clients.
    
    Manages creation and caching of LLM clients for different providers.
    """

    def __init__(self):
        """Initialize LLM registry."""
        self._clients: Dict[str, LLMClient] = {}
        self._providers = {
            "openai": self._create_openai_client,
            "azure_openai": self._create_azure_openai_client,
            "groq": self._create_groq_client,
            "ollama": self._create_ollama_client,
        }

    def _create_openai_client(
        self,
        model: str,
        api_key: str,
        **kwargs,
    ) -> OpenAIClient:
        """Create OpenAI client."""
        organization = kwargs.get("organization")
        return OpenAIClient(
            api_key=api_key,
            model=model,
            organization=organization,
        )

    def _create_azure_openai_client(
        self,
        model: str,
        api_key: str,
        **kwargs,
    ) -> AzureOpenAIClient:
        """Create Azure OpenAI client."""
        endpoint = kwargs.get("endpoint")
        deployment_name = kwargs.get("deployment_name", model)
        api_version = kwargs.get("api_version", "2024-02-15-preview")
        
        if not endpoint:
            raise ValueError("endpoint is required for Azure OpenAI client")
        
        return AzureOpenAIClient(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
        )

    def _create_groq_client(
        self,
        model: str,
        api_key: str,
        **kwargs,
    ) -> GroqClient:
        """Create Groq client."""
        return GroqClient(
            api_key=api_key,
            model=model,
        )

    def _create_ollama_client(
        self,
        model: str,
        api_key: str,
        **kwargs,
    ) -> OllamaClient:
        """Create Ollama client."""
        base_url = kwargs.get("base_url", "http://localhost:11434")
        return OllamaClient(
            base_url=base_url,
            model=model,
        )

    def get_client(
        self,
        provider: str,
        model: str,
        api_key: str,
        cache: bool = True,
        **kwargs,
    ) -> LLMClient:
        """
        Get or create an LLM client.
        
        Args:
            provider: Provider name (openai, azure_openai, groq, ollama)
            model: Model name
            api_key: API key
            cache: Whether to cache the client
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMClient: LLM client instance
            
        Raises:
            ValueError: If provider is not supported
        """
        # Generate cache key
        cache_key = f"{provider}:{model}"
        
        # Return cached client if available
        if cache and cache_key in self._clients:
            logger.debug(f"Using cached client for {cache_key}")
            return self._clients[cache_key]
        
        # Get provider factory
        if provider not in self._providers:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        factory = self._providers[provider]
        
        # Create client
        logger.info(f"Creating new {provider} client for model: {model}")
        client = factory(model=model, api_key=api_key, **kwargs)
        
        # Cache client if requested
        if cache:
            self._clients[cache_key] = client
        
        return client

    def clear_cache(self) -> None:
        """Clear all cached clients."""
        self._clients.clear()
        logger.info("Cleared LLM client cache")


# ============================================================================
# Global Registry Instance
# ============================================================================

_registry = LLMRegistry()


# ============================================================================
# Factory Functions
# ============================================================================

def get_llm_client(
    provider: str,
    model: str,
    api_key: str,
    cache: bool = True,
    **kwargs,
) -> LLMClient:
    """
    Get an LLM client for the specified provider.
    
    This is the main factory function for creating LLM clients.
    
    Args:
        provider: Provider name (openai, azure_openai, groq, ollama)
        model: Model name
        api_key: API key
        cache: Whether to cache the client (default: True)
        **kwargs: Additional provider-specific parameters
            - For OpenAI: organization
            - For Azure OpenAI: endpoint, deployment_name, api_version
            - For Ollama: base_url
        
    Returns:
        LLMClient: LLM client instance
        
    Raises:
        ValueError: If provider is not supported
        ImportError: If required package is not installed
        
    Example:
        # OpenAI
        client = get_llm_client(
            provider="openai",
            model="gpt-4",
            api_key="sk-...",
        )
        
        # Azure OpenAI
        client = get_llm_client(
            provider="azure_openai",
            model="gpt-4",
            api_key="...",
            endpoint="https://your-resource.openai.azure.com/",
            deployment_name="gpt-4",
        )
        
        # Groq
        client = get_llm_client(
            provider="groq",
            model="mixtral-8x7b-32768",
            api_key="gsk_...",
        )
        
        # Ollama
        client = get_llm_client(
            provider="ollama",
            model="llama2",
            api_key="",  # Not needed for local Ollama
            base_url="http://localhost:11434",
        )
    """
    return _registry.get_client(
        provider=provider,
        model=model,
        api_key=api_key,
        cache=cache,
        **kwargs,
    )


def get_llm_client_from_config(
    config: Dict[str, Any],
    cache: bool = True,
) -> LLMClient:
    """
    Get an LLM client from a configuration dictionary.
    
    Args:
        config: Configuration dictionary with keys:
            - provider: Provider name
            - model: Model name
            - api_key: API key
            - Additional provider-specific parameters
        cache: Whether to cache the client
        
    Returns:
        LLMClient: LLM client instance
        
    Example:
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-...",
        }
        client = get_llm_client_from_config(config)
    """
    config_copy = config.copy()
    provider = config_copy.pop("provider")
    model = config_copy.pop("model")
    api_key = config_copy.pop("api_key")
    
    return get_llm_client(
        provider=provider,
        model=model,
        api_key=api_key,
        cache=cache,
        **config_copy,
    )


def clear_llm_cache() -> None:
    """Clear all cached LLM clients."""
    _registry.clear_cache()

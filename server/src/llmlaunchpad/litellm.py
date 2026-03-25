"""LiteLLM integration for cloud model routing in LLMLaunchpad.

This module provides optional cloud routing through LiteLLM,
allowing users to fall back to cloud providers when local
inference is not available or preferred.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, AsyncIterator
from enum import Enum

from .config import get_config, save_config

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    GROQ = "groq"
    TOGETHER = "together"
    MISTRAL = "mistral"


@dataclass
class CloudModel:
    """A cloud model configuration."""
    provider: CloudProvider
    model_id: str
    display_name: str
    context_length: int
    input_cost_per_1k: float  # USD
    output_cost_per_1k: float  # USD
    
    def to_dict(self) -> dict:
        return {
            "provider": self.provider.value,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "context_length": self.context_length,
            "input_cost_per_1k": self.input_cost_per_1k,
            "output_cost_per_1k": self.output_cost_per_1k,
        }


# Popular cloud models
CLOUD_MODELS = [
    CloudModel(
        provider=CloudProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        context_length=128000,
        input_cost_per_1k=0.005,
        output_cost_per_1k=0.015,
    ),
    CloudModel(
        provider=CloudProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        context_length=128000,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
    ),
    CloudModel(
        provider=CloudProvider.ANTHROPIC,
        model_id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        context_length=200000,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
    ),
    CloudModel(
        provider=CloudProvider.ANTHROPIC,
        model_id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        context_length=200000,
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.005,
    ),
    CloudModel(
        provider=CloudProvider.GOOGLE,
        model_id="gemini/gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        context_length=2000000,
        input_cost_per_1k=0.00125,
        output_cost_per_1k=0.005,
    ),
    CloudModel(
        provider=CloudProvider.GOOGLE,
        model_id="gemini/gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        context_length=1000000,
        input_cost_per_1k=0.000075,
        output_cost_per_1k=0.0003,
    ),
    CloudModel(
        provider=CloudProvider.GROQ,
        model_id="groq/llama-3.1-70b-versatile",
        display_name="Llama 3.1 70B (Groq)",
        context_length=131072,
        input_cost_per_1k=0.00059,
        output_cost_per_1k=0.00079,
    ),
    CloudModel(
        provider=CloudProvider.GROQ,
        model_id="groq/llama-3.1-8b-instant",
        display_name="Llama 3.1 8B (Groq)",
        context_length=131072,
        input_cost_per_1k=0.00005,
        output_cost_per_1k=0.00008,
    ),
    CloudModel(
        provider=CloudProvider.TOGETHER,
        model_id="together_ai/meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
        display_name="Llama 3.2 90B Vision (Together)",
        context_length=131072,
        input_cost_per_1k=0.00088,
        output_cost_per_1k=0.00088,
    ),
    CloudModel(
        provider=CloudProvider.MISTRAL,
        model_id="mistral/mistral-large-latest",
        display_name="Mistral Large",
        context_length=128000,
        input_cost_per_1k=0.002,
        output_cost_per_1k=0.006,
    ),
]


def get_available_cloud_models() -> List[CloudModel]:
    """Get list of available cloud models."""
    return CLOUD_MODELS


def get_cloud_model(model_id: str) -> Optional[CloudModel]:
    """Get a cloud model by ID."""
    for model in CLOUD_MODELS:
        if model.model_id == model_id:
            return model
    return None


def is_litellm_available() -> bool:
    """Check if LiteLLM is installed."""
    try:
        import litellm
        return True
    except ImportError:
        return False


def get_configured_providers() -> List[str]:
    """Get list of providers with configured API keys."""
    config = get_config()
    return list(config.litellm_api_keys.keys())


def set_api_key(provider: str, api_key: str) -> None:
    """Set API key for a provider."""
    config = get_config()
    config.litellm_api_keys[provider] = api_key
    save_config(config)
    
    # Also set environment variable for LiteLLM
    _apply_api_keys()


def remove_api_key(provider: str) -> None:
    """Remove API key for a provider."""
    config = get_config()
    if provider in config.litellm_api_keys:
        del config.litellm_api_keys[provider]
        save_config(config)


def _apply_api_keys() -> None:
    """Apply API keys from config to environment."""
    import os
    config = get_config()
    
    # Map our provider names to LiteLLM environment variables
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "azure": "AZURE_API_KEY",
        "groq": "GROQ_API_KEY",
        "together": "TOGETHER_API_KEY",
        "mistral": "MISTRAL_API_KEY",
    }
    
    for provider, env_var in env_map.items():
        if provider in config.litellm_api_keys:
            os.environ[env_var] = config.litellm_api_keys[provider]


def get_models_for_provider(provider: str) -> List[CloudModel]:
    """Get available models for a specific provider."""
    try:
        p = CloudProvider(provider.lower())
    except ValueError:
        return []
    
    return [m for m in CLOUD_MODELS if m.provider == p]


class LiteLLMClient:
    """Client for LiteLLM cloud routing."""
    
    def __init__(self):
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure LiteLLM is initialized with API keys."""
        if self._initialized:
            return
        
        if not is_litellm_available():
            raise RuntimeError("LiteLLM is not installed. Run: pip install litellm")
        
        _apply_api_keys()
        self._initialized = True
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request through LiteLLM.
        
        Args:
            model: Model ID (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters passed to LiteLLM
        
        Returns:
            LiteLLM response dict
        """
        self._ensure_initialized()
        
        import litellm
        
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs,
        )
        
        return response
    
    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion response.
        
        Yields content chunks as they arrive.
        """
        self._ensure_initialized()
        
        import litellm
        
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def get_token_count(self, model: str, text: str) -> int:
        """
        Get token count for text using the model's tokenizer.
        """
        self._ensure_initialized()
        
        try:
            import litellm
            return litellm.token_counter(model=model, text=text)
        except Exception:
            # Fallback: rough estimate
            return len(text) // 4


# Global client instance
_litellm_client: Optional[LiteLLMClient] = None


def get_litellm_client() -> LiteLLMClient:
    """Get the global LiteLLM client."""
    global _litellm_client
    if _litellm_client is None:
        _litellm_client = LiteLLMClient()
    return _litellm_client


def get_litellm_status() -> Dict[str, Any]:
    """Get LiteLLM status and configuration."""
    config = get_config()
    
    return {
        "enabled": config.litellm_enabled,
        "available": is_litellm_available(),
        "configured_providers": get_configured_providers(),
        "cloud_models": [m.to_dict() for m in CLOUD_MODELS],
    }

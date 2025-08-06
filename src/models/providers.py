"""Model provider implementations."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx
from .config import ProviderType, TaskType, model_config

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Abstract base class for model providers."""
    
    def __init__(self, provider_type: ProviderType):
        self.provider_type = provider_type
        self.client = None
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Generate text using the model provider."""
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream text generation using the model provider."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class OpenRouterProvider(ModelProvider):
    """OpenRouter API provider."""
    
    def __init__(self):
        super().__init__(ProviderType.OPENROUTER)
        self.api_key = model_config.openrouter_api_key
        self.base_url = model_config.openrouter_base_url
        
        if not self.api_key:
            logger.warning("OpenRouter API key not found")
    
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Generate text using OpenRouter API."""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/theinterneti/TTA",
            "X-Title": "Therapeutic Text Adventure"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def stream_generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream text generation using OpenRouter API."""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/theinterneti/TTA",
            "X-Title": "Therapeutic Text Adventure"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            import json
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def is_available(self) -> bool:
        """Check if OpenRouter is available."""
        if not self.api_key:
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenRouter availability check failed: {e}")
            return False


class LocalProvider(ModelProvider):
    """Local model provider (Ollama, OpenHands, etc.)."""
    
    def __init__(self):
        super().__init__(ProviderType.LOCAL)
        self.endpoint = model_config.local_model_endpoint
        self.model_type = model_config.local_model_type
    
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Generate text using local model."""
        if self.model_type == "ollama":
            return await self._ollama_generate(prompt, model, temperature, max_tokens, **kwargs)
        else:
            raise NotImplementedError(f"Local model type {self.model_type} not implemented")
    
    async def _ollama_generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Generate using Ollama API."""
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs
            },
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
    
    async def stream_generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream text generation using local model."""
        if self.model_type == "ollama":
            async for chunk in self._ollama_stream_generate(prompt, model, temperature, max_tokens, **kwargs):
                yield chunk
        else:
            raise NotImplementedError(f"Local model type {self.model_type} not implemented")
    
    async def _ollama_stream_generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate using Ollama API."""
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs
            },
            "stream": True
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=120.0
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    try:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
    
    async def is_available(self) -> bool:
        """Check if local model provider is available."""
        try:
            async with httpx.AsyncClient() as client:
                if self.model_type == "ollama":
                    response = await client.get(f"{self.endpoint}/api/tags", timeout=5.0)
                    return response.status_code == 200
                else:
                    # Generic health check
                    response = await client.get(f"{self.endpoint}/health", timeout=5.0)
                    return response.status_code == 200
        except Exception as e:
            logger.warning(f"Local provider availability check failed: {e}")
            return False


class ModelProviderFactory:
    """Factory for creating model providers."""
    
    _providers: Dict[ProviderType, ModelProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_type: ProviderType) -> ModelProvider:
        """Get or create a model provider instance."""
        if provider_type not in cls._providers:
            if provider_type == ProviderType.OPENROUTER:
                cls._providers[provider_type] = OpenRouterProvider()
            elif provider_type == ProviderType.LOCAL:
                cls._providers[provider_type] = LocalProvider()
            else:
                raise NotImplementedError(f"Provider {provider_type} not implemented")
        
        return cls._providers[provider_type]
    
    @classmethod
    async def get_available_provider(cls, preferred_providers: List[ProviderType]) -> Optional[ModelProvider]:
        """Get the first available provider from a list of preferred providers."""
        for provider_type in preferred_providers:
            try:
                provider = cls.get_provider(provider_type)
                if await provider.is_available():
                    return provider
            except Exception as e:
                logger.warning(f"Failed to check provider {provider_type}: {e}")
                continue
        
        return None

"""Unified model client with intelligent provider selection and fallback."""

import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from .config import TaskType, ProviderType, model_config
from .providers import ModelProviderFactory, ModelProvider

logger = logging.getLogger(__name__)


class CostTracker:
    """Simple cost tracking for model usage."""
    
    def __init__(self):
        self.daily_cost = 0.0
        self.usage_log = []
    
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on model and token usage."""
        # Simplified cost estimation - in production, use actual pricing
        cost_per_1k_tokens = {
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.0001,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.0005,
            "gemini-pro": 0.001,
        }
        
        # Extract base model name for cost lookup
        base_model = model.split("/")[-1].split(":")[0]
        rate = cost_per_1k_tokens.get(base_model, 0.001)  # Default rate
        
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * rate
    
    def add_usage(self, model: str, input_tokens: int, output_tokens: int, cost: float):
        """Add usage to tracking."""
        self.daily_cost += cost
        self.usage_log.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })
    
    def can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford the estimated cost."""
        return (self.daily_cost + estimated_cost) <= model_config.max_daily_cost


class UnifiedModelClient:
    """Unified client for all model providers with intelligent selection."""
    
    def __init__(self):
        self.cost_tracker = CostTracker() if model_config.enable_cost_tracking else None
        self._provider_cache: Dict[ProviderType, ModelProvider] = {}
    
    async def generate(
        self,
        prompt: str,
        task_type: TaskType = TaskType.NARRATIVE,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        prefer_free: Optional[bool] = None,
        **kwargs
    ) -> str:
        """Generate text with intelligent provider and model selection."""
        
        # Determine model and parameters
        if model is None:
            model = model_config.get_model_for_task(task_type, prefer_free)
        
        if temperature is None:
            temperature = model_config.get_temperature_for_task(task_type)
        
        if max_tokens is None:
            max_tokens = model_config.get_max_tokens_for_task(task_type)
        
        # Cost check
        if self.cost_tracker:
            estimated_tokens = len(prompt.split()) * 1.3 + max_tokens  # Rough estimate
            estimated_cost = self.cost_tracker.estimate_cost(model, len(prompt.split()), max_tokens)
            
            if not self.cost_tracker.can_afford(estimated_cost):
                logger.warning(f"Daily cost limit would be exceeded. Using free model.")
                model = model_config.get_model_for_task(task_type, prefer_free=True)
        
        # Try providers in order of preference
        providers_to_try = [model_config.primary_provider] + model_config.fallback_providers
        
        for attempt, provider_type in enumerate(providers_to_try):
            try:
                provider = ModelProviderFactory.get_provider(provider_type)
                
                # Check if provider is available
                if not await provider.is_available():
                    logger.warning(f"Provider {provider_type} is not available")
                    continue
                
                # Adjust model name for provider
                adjusted_model = self._adjust_model_for_provider(model, provider_type)
                
                # Generate text
                result = await provider.generate(
                    prompt=prompt,
                    model=adjusted_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                # Track usage
                if self.cost_tracker:
                    output_tokens = len(result.split())
                    input_tokens = len(prompt.split())
                    cost = self.cost_tracker.estimate_cost(adjusted_model, input_tokens, output_tokens)
                    self.cost_tracker.add_usage(adjusted_model, input_tokens, output_tokens, cost)
                
                logger.info(f"Successfully generated text using {provider_type} with model {adjusted_model}")
                return result
                
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed (attempt {attempt + 1}): {e}")
                
                if attempt < len(providers_to_try) - 1:
                    if model_config.enable_fallback:
                        logger.info(f"Falling back to next provider...")
                        await asyncio.sleep(model_config.retry_delay)
                        continue
                    else:
                        break
                else:
                    logger.error("All providers failed")
                    raise e
        
        raise RuntimeError("No available providers could handle the request")
    
    async def stream_generate(
        self,
        prompt: str,
        task_type: TaskType = TaskType.NARRATIVE,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        prefer_free: Optional[bool] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate text with intelligent provider selection."""
        
        # Determine model and parameters (same logic as generate)
        if model is None:
            model = model_config.get_model_for_task(task_type, prefer_free)
        
        if temperature is None:
            temperature = model_config.get_temperature_for_task(task_type)
        
        if max_tokens is None:
            max_tokens = model_config.get_max_tokens_for_task(task_type)
        
        # Try providers in order of preference
        providers_to_try = [model_config.primary_provider] + model_config.fallback_providers
        
        for attempt, provider_type in enumerate(providers_to_try):
            try:
                provider = ModelProviderFactory.get_provider(provider_type)
                
                # Check if provider is available
                if not await provider.is_available():
                    logger.warning(f"Provider {provider_type} is not available")
                    continue
                
                # Adjust model name for provider
                adjusted_model = self._adjust_model_for_provider(model, provider_type)
                
                # Stream generate text
                async for chunk in provider.stream_generate(
                    prompt=prompt,
                    model=adjusted_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                ):
                    yield chunk
                
                logger.info(f"Successfully streamed text using {provider_type} with model {adjusted_model}")
                return
                
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed (attempt {attempt + 1}): {e}")
                
                if attempt < len(providers_to_try) - 1:
                    if model_config.enable_fallback:
                        logger.info(f"Falling back to next provider...")
                        await asyncio.sleep(model_config.retry_delay)
                        continue
                    else:
                        break
                else:
                    logger.error("All providers failed")
                    raise e
        
        raise RuntimeError("No available providers could handle the request")
    
    def _adjust_model_for_provider(self, model: str, provider_type: ProviderType) -> str:
        """Adjust model name based on provider requirements."""
        if provider_type == ProviderType.LOCAL:
            # For local providers, extract just the model name
            if "/" in model:
                return model.split("/")[-1].split(":")[0]
            return model
        
        # For API providers, keep the full model name
        return model
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary."""
        if not self.cost_tracker:
            return {"cost_tracking": False}
        
        return {
            "cost_tracking": True,
            "daily_cost": self.cost_tracker.daily_cost,
            "max_daily_cost": model_config.max_daily_cost,
            "remaining_budget": model_config.max_daily_cost - self.cost_tracker.daily_cost,
            "usage_count": len(self.cost_tracker.usage_log)
        }


# Global client instance
unified_client = UnifiedModelClient()

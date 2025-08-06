"""Modernized configuration for model providers."""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseSettings, Field, validator


class ProviderType(str, Enum):
    """Supported model providers."""
    OPENROUTER = "openrouter"
    LOCAL = "local"
    BYOK_OPENAI = "byok_openai"
    BYOK_ANTHROPIC = "byok_anthropic"
    BYOK_GOOGLE = "byok_google"


class ModelTier(str, Enum):
    """Model performance/cost tiers."""
    FREE = "free"
    EFFICIENT = "efficient"
    PREMIUM = "premium"


class TaskType(str, Enum):
    """Different types of AI tasks."""
    NARRATIVE = "narrative"
    TOOLS = "tools"
    REASONING = "reasoning"
    CREATIVE = "creative"


class ModelConfig(BaseSettings):
    """Configuration for model providers and selection."""
    
    # Provider Configuration
    primary_provider: ProviderType = ProviderType.OPENROUTER
    fallback_providers: List[ProviderType] = [ProviderType.LOCAL]
    
    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # BYOK Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    
    # Local Model Configuration
    local_model_endpoint: str = Field("http://localhost:11434", env="LOCAL_MODEL_ENDPOINT")
    local_model_type: str = Field("ollama", env="LOCAL_MODEL_TYPE")
    
    # Model Selection by Task
    models_by_task: Dict[TaskType, str] = {
        TaskType.NARRATIVE: "anthropic/claude-3-haiku",
        TaskType.TOOLS: "openai/gpt-4o-mini", 
        TaskType.REASONING: "google/gemini-pro",
        TaskType.CREATIVE: "anthropic/claude-3-sonnet"
    }
    
    # Free model alternatives
    free_models_by_task: Dict[TaskType, str] = {
        TaskType.NARRATIVE: "google/gemma-2-9b-it:free",
        TaskType.TOOLS: "microsoft/wizardlm-2-8x22b:free",
        TaskType.REASONING: "meta-llama/llama-3.1-8b-instruct:free",
        TaskType.CREATIVE: "google/gemma-2-27b-it:free"
    }
    
    # Model Parameters by Task
    temperature_by_task: Dict[TaskType, float] = {
        TaskType.NARRATIVE: 0.8,
        TaskType.TOOLS: 0.1,
        TaskType.REASONING: 0.3,
        TaskType.CREATIVE: 0.9
    }
    
    max_tokens_by_task: Dict[TaskType, int] = {
        TaskType.NARRATIVE: 2048,
        TaskType.TOOLS: 1024,
        TaskType.REASONING: 4096,
        TaskType.CREATIVE: 3072
    }
    
    # Cost Management
    enable_cost_tracking: bool = Field(True, env="ENABLE_COST_TRACKING")
    max_daily_cost: float = Field(10.0, env="MAX_DAILY_COST")
    prefer_free_models: bool = Field(True, env="PREFER_FREE_MODELS")
    
    # Fallback Configuration
    enable_fallback: bool = Field(True, env="ENABLE_FALLBACK")
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: float = Field(1.0, env="RETRY_DELAY")
    
    @validator('openrouter_api_key', 'openai_api_key', 'anthropic_api_key', 'google_api_key')
    def validate_api_keys(cls, v):
        """Validate API keys are not empty strings."""
        if v and len(v.strip()) == 0:
            return None
        return v
    
    def get_model_for_task(self, task_type: TaskType, prefer_free: bool = None) -> str:
        """Get the appropriate model for a given task type."""
        if prefer_free is None:
            prefer_free = self.prefer_free_models
            
        if prefer_free and task_type in self.free_models_by_task:
            return self.free_models_by_task[task_type]
        
        return self.models_by_task.get(task_type, "openai/gpt-4o-mini")
    
    def get_temperature_for_task(self, task_type: TaskType) -> float:
        """Get the appropriate temperature for a given task type."""
        return self.temperature_by_task.get(task_type, 0.7)
    
    def get_max_tokens_for_task(self, task_type: TaskType) -> int:
        """Get the appropriate max tokens for a given task type."""
        return self.max_tokens_by_task.get(task_type, 2048)
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


# Global config instance
model_config = ModelConfig()

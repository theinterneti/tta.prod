# TTA Production

This directory contains the **stable, production-ready** components of the Therapeutic Text Adventure (TTA) project. These are the core, reusable components that form the foundation of the system.

## 🎯 Purpose

- **Stable APIs**: Well-tested, stable interfaces that other projects can depend on
- **Core Components**: Essential building blocks (agents, knowledge graph, tools)
- **Reusable Libraries**: Components designed for use in future projects
- **Production Quality**: Code that meets production standards for reliability and maintainability

## 🏗️ Architecture

### Modernized Model Provider System

The production version features a completely modernized approach to LLM integration:

- **OpenRouter Integration**: Access to multiple providers (OpenAI, Anthropic, Google, etc.) through a single API
- **BYOK Support**: Bring Your Own Key for direct provider access
- **Local Model Support**: Integration with Ollama and other local model systems
- **Intelligent Fallback**: Automatic fallback between providers based on availability
- **Cost Management**: Built-in cost tracking and budget management
- **Task-Specific Models**: Different models optimized for different types of tasks

### Core Components

- **`src/agents/`**: Base agent system with modernized LLM integration
- **`src/knowledge/`**: Neo4j knowledge graph management
- **`src/models/`**: Unified model provider system
- **`src/tools/`**: Reusable tool system for agent interactions
- **`src/utils/`**: Utility functions and helpers

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Key Configuration Options**:
   - `PRIMARY_PROVIDER`: Choose between `openrouter`, `local`, or BYOK options
   - `OPENROUTER_API_KEY`: For OpenRouter access (recommended)
   - `PREFER_FREE_MODELS`: Use free models when available
   - `MAX_DAILY_COST`: Set spending limits

## 🔧 Usage

### Basic Agent Usage

```python
from tta.prod.src.agents import BaseAgent
from tta.prod.src.models import TaskType

# Create an agent optimized for narrative tasks
agent = BaseAgent(
    name="Storyteller",
    description="Creates engaging narratives",
    task_type=TaskType.NARRATIVE
)

# Generate content
response = await agent.generate_response(
    "Create a mysterious opening for a story",
    context={"setting": "ancient library", "mood": "mysterious"}
)
```

### Model Provider Usage

```python
from tta.prod.src.models import UnifiedModelClient, TaskType

client = UnifiedModelClient()

# Generate with automatic model selection
response = await client.generate(
    prompt="Explain quantum computing",
    task_type=TaskType.REASONING,
    prefer_free=True  # Use free models when possible
)
```

## 🔄 Integration with Other Projects

This production codebase is designed to be easily integrated into other projects:

1. **Modular Design**: Each component can be used independently
2. **Clean APIs**: Well-defined interfaces with minimal dependencies
3. **Configuration-Driven**: Behavior controlled through environment variables
4. **Async-First**: Built for modern async Python applications

## 📊 Cost Management

The system includes built-in cost management features:

- **Daily Budget Limits**: Automatically switch to free models when budget is reached
- **Usage Tracking**: Monitor token usage and costs
- **Provider Optimization**: Intelligent routing to cost-effective providers

## 🔒 Security

- **API Key Management**: Secure handling of multiple API keys
- **Environment-Based Config**: No hardcoded secrets
- **Validation**: Input validation and sanitization throughout

## 📈 Future-Proof Design

This codebase incorporates lessons learned and modern best practices:

- **Provider Abstraction**: Easy to add new LLM providers
- **Flexible Configuration**: Adapt to changing requirements
- **Extensible Architecture**: Built for future enhancements
- **Clean Separation**: Clear boundaries between components

## 🤝 Contributing

When contributing to the production codebase:

1. **Maintain Stability**: Changes should be backward compatible
2. **Add Tests**: All new features must include tests
3. **Document APIs**: Update documentation for any API changes
4. **Follow Standards**: Use the established coding standards

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

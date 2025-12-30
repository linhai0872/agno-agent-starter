<p align="right">
  <a href="README.md">中文</a>
</p>

# Model Configuration Guide

Unified multi-provider model configuration interface, supporting 8 major model providers.

## Directory Structure

```
models/
├── __init__.py       # Interface exports
├── config.py         # ModelConfig definitions
├── factory.py        # Model factory
├── registry.py       # Model capabilities registry
└── providers/        # Provider-specific implementations
```

## Basic Usage

```python
from app.models import ModelConfig, create_model

config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=8192,
)

model = create_model(config)
```

## Multi-Provider Support

```python
from app.models import ModelConfig, ModelProvider

# OpenRouter (Default)
config = ModelConfig(model_id="google/gemini-2.5-flash-preview-09-2025")

# OpenAI
config = ModelConfig(provider=ModelProvider.OPENAI, model_id="gpt-4o")

# Google Gemini
config = ModelConfig(provider=ModelProvider.GOOGLE, model_id="gemini-2.5-flash")

# Anthropic Claude
config = ModelConfig(provider=ModelProvider.ANTHROPIC, model_id="claude-sonnet-4")

# Alibaba DashScope
config = ModelConfig(provider=ModelProvider.DASHSCOPE, model_id="qwen-plus")

# Volcengine (ByteDance)
config = ModelConfig(provider=ModelProvider.VOLCENGINE, model_id="doubao-seed-1-6-251015")

# Ollama Local
config = ModelConfig(provider=ModelProvider.OLLAMA, model_id="llama3.2:latest")
```

## Advanced Configuration

```python
from app.models import ReasoningConfig, WebSearchConfig

# Reasoning Mode
config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    reasoning=ReasoningConfig(enabled=True, effort="medium"),
)

# Web Search
config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    web_search=WebSearchConfig(enabled=True),
)
```

## API Key Priority

```python
from app.models import ModelConfig, ProjectConfig

# 1. Agent Level (Highest)
config = ModelConfig(api_key_env="MY_AGENT_KEY")

# 2. Project Level (Shared by Team/Workflow)
project = ProjectConfig(api_key_env="MY_PROJECT_KEY")
model = create_model(config, project)

# 3. Global Level (Fallback)
# Environment variable OPENROUTER_API_KEY
```

## Supported Providers

| Provider | Description |
|----------|-------------|
| OPENROUTER | Unified gateway, 100+ models |
| OPENAI | GPT-4o, o1/o3 series |
| GOOGLE | Gemini 2.5 series |
| ANTHROPIC | Claude Sonnet 4, Opus 4 |
| DASHSCOPE | Qwen series |
| VOLCENGINE | Doubao Seed, DeepSeek |
| OLLAMA | Local deployment |
| LITELLM | Unified gateway |


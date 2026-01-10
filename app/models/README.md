<p align="right">
  <a href="README_EN.md">English</a>
</p>

# 模型配置指南

统一的多厂商模型配置接口，支持 8 大模型厂商。

## 目录结构

```
models/
├── __init__.py       # 导出接口
├── config.py         # ModelConfig 定义
├── factory.py        # 模型工厂
├── registry.py       # 模型能力注册表
└── providers/        # 各厂商实现
```

## 基础用法

```python
from app.models import ModelConfig, create_model

config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=8192,
)

model = create_model(config)
```

## 多厂商支持

```python
from app.models import ModelConfig, ModelProvider

# OpenRouter（默认）
config = ModelConfig(model_id="google/gemini-2.5-flash-preview-09-2025")

# OpenAI
config = ModelConfig(provider=ModelProvider.OPENAI, model_id="gpt-4o")

# Google Gemini
config = ModelConfig(provider=ModelProvider.GOOGLE, model_id="gemini-2.5-flash")

# Anthropic Claude
config = ModelConfig(provider=ModelProvider.ANTHROPIC, model_id="claude-sonnet-4")

# 阿里云 DashScope
config = ModelConfig(provider=ModelProvider.DASHSCOPE, model_id="qwen-plus")

# 火山方舟
config = ModelConfig(provider=ModelProvider.VOLCENGINE, model_id="doubao-seed-1-6-251015")

# Ollama 本地
config = ModelConfig(provider=ModelProvider.OLLAMA, model_id="llama3.2:latest")
```

## 高级配置

```python
from app.models import ReasoningConfig, WebSearchConfig

# 思考模式
config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    reasoning=ReasoningConfig(enabled=True, effort="medium"),
)

# 网络搜索
config = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    web_search=WebSearchConfig(enabled=True),
)
```

## API Key 优先级

```python
from app.models import ModelConfig, ProjectConfig

# 1. Agent 级（最高）
config = ModelConfig(api_key_env="MY_AGENT_KEY")

# 2. Project 级（Team/Workflow 共享）
project = ProjectConfig(api_key_env="MY_PROJECT_KEY")
model = create_model(config, project)

# 3. Global 级（兜底）
# 环境变量 OPENROUTER_API_KEY
```

## 支持厂商

| Provider | 说明 |
|----------|------|
| OPENROUTER | 统一网关，100+ 模型 |
| OPENAI | GPT-4o, o1/o3 系列 |
| GOOGLE | Gemini 2.5 系列 |
| ANTHROPIC | Claude Sonnet 4, Opus 4 |
| DASHSCOPE | Qwen 系列 |
| VOLCENGINE | 豆包 Seed, DeepSeek |
| OLLAMA | 本地部署 |
| LITELLM | 统一网关 |

## 迭代防护模型

防止 Agent 工具调用时 LLM 无限循环：

```python
from app.models import GuardedOpenRouter

# 创建带迭代防护的模型
model = GuardedOpenRouter(
    id="google/gemini-2.5-flash-preview-05-20",
    max_iterations=50,  # LLM 最多调用 50 次，超过后抛出 StopAgentRun
)

agent = Agent(model=model, tools=[...])
```

适用场景：有工具调用的 Agent 节点（如 EntityVerificationAgent、ContactDiscoveryAgent）。



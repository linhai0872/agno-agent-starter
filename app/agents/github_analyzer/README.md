# GitHub Repository Analyzer

**类型**: Agent  
**用途**: 分析 GitHub 仓库的技术栈、活跃度和核心功能

## 功能特性

- 📊 **结构化输出**: 使用 Pydantic Schema 定义输出格式
- 🔍 **智能搜索**: 集成 DuckDuckGo 获取仓库信息
- 📝 **完整分析**: 技术栈、活跃度、核心功能、使用建议

## 使用示例

```python
from agno.db.postgres import PostgresDb
from app.agents.github_analyzer import create_github_analyzer_agent

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")
agent = create_github_analyzer_agent(db)

response = agent.run("分析 https://github.com/agno-agi/agno")
print(response.content)
```

## 输出格式

```json
{
  "repo_name": "agno-agi/agno",
  "description": "多智能体框架",
  "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
  "stars": 12000,
  "forks": 800,
  "contributors": 50,
  "activity_level": "active",
  "key_features": [
    "多智能体协作",
    "知识库 RAG",
    "持久化记忆"
  ],
  "recommendations": [
    "适合构建复杂 AI 应用",
    "建议配合 AgentOS 使用"
  ]
}
```

## 技术要点

### 结构化输出模式

```python
agent = Agent(
    output_schema=GitHubRepoAnalysis,  # Pydantic Model
    use_json_mode=True,                 # 启用 JSON 模式
    markdown=False,                     # 禁用 Markdown
)
```

### 错误处理

- 搜索 API 限流时，基于已获取信息生成报告
- 未知字段返回默认值（如 `0` 或 `"unknown"`）

## 扩展指南

### 使用 Tavily 替代 DuckDuckGo

如需更强大的搜索能力，可替换为 Tavily:

```python
from agno.tools.tavily import TavilyTools

agent = Agent(
    tools=[TavilyTools()],  # 需要 TAVILY_API_KEY
    ...
)
```

# Deep Research Team

**类型**: Team (多智能体协作)  
**用途**: 深度研究任务，生成结构化研究报告

## 功能特性

- 🤝 **多智能体协作**: Planner → Researcher → Analyst → Writer
- 📊 **状态管理**: session_state 共享研究发现
- 🛡️ **迭代控制**: ToolCallGuard 限制搜索次数
- 📝 **结构化输出**: ResearchReport Schema

## 团队成员

| Agent          | 职责                 | 工具            |
| -------------- | -------------------- | --------------- |
| **Planner**    | 分解研究主题为子问题 | 无              |
| **Researcher** | 执行搜索收集信息     | DuckDuckGoTools |
| **Analyst**    | 分析综合搜索结果     | 无              |
| **Writer**     | 撰写最终报告         | 无              |

## 使用示例

```python
from agno.db.postgres import PostgresDb
from app.teams.deep_research import create_deep_research_team

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")
team = create_deep_research_team(db)

response = team.run("研究 AI Agent 框架的发展趋势")
print(response.content)  # ResearchReport 对象
```

## 状态管理

Team 使用 `session_state` 在成员间共享信息：

```python
session_state = {
    "findings": [],        # 累积的研究发现
    "topics_searched": [], # 已搜索的主题
    "sources": [],         # 来源列表
}
```

成员 Agent 通过 `RunContext` 访问和更新状态：

```python
def add_finding(run_context: RunContext, finding: str) -> str:
    run_context.session_state["findings"].append(finding)
    return "Finding added"
```

## 迭代控制

Researcher Agent 配置了 `ToolCallGuard`：

```python
guard = create_tool_call_guard(
    max_calls_per_tool=10,   # 单工具最多 10 次
    max_retries_per_tool=3,  # 最多 3 次重试
    max_total_calls=30,      # 总调用上限
)
```

超过限制时会触发 `StopAgentRun`，返回已收集的结果。

## 输出格式

```json
{
  "topic": "AI Agent 框架发展趋势",
  "executive_summary": "研究发现...",
  "findings": [
    {
      "topic": "框架对比",
      "summary": "...",
      "details": "...",
      "confidence": "high"
    }
  ],
  "sources": [
    {"title": "...", "url": "...", "type": "web"}
  ],
  "recommendations": ["建议1", "建议2"],
  "limitations": ["局限1"]
}
```

## 技术要点

### Agentic State

Team 和成员 Agent 都需要设置 `enable_agentic_state=True`：

```python
# 成员 Agent
agent = Agent(
    add_session_state_to_context=True,
    enable_agentic_state=True,
)

# Team
team = Team(
    members=[agent],
    session_state={...},
    enable_agentic_state=True,
    add_session_state_to_context=True,
    share_member_interactions=True,
)
```

### 研究流程控制

1. Planner 分解主题 → 更新 `topics_searched`
2. Researcher 搜索信息 → 更新 `findings` 和 `sources`
3. Analyst 分析结果 → 补充 `findings`
4. Writer 生成报告 → 输出 `ResearchReport`

# 工具开发指南

三层工具注册表，支持 Framework/Project/Agent 级别定制。

## 目录结构

```
tools/
├── __init__.py       # 导出接口
├── config.py         # 配置定义
├── registry.py       # 三层注册表
├── builtin/          # 内置工具
│   ├── http_client.py
│   └── web_search.py
└── mcp/              # MCP 协议集成
    └── client.py
```

## 创建工具

```python
def my_tool(query: str) -> str:
    """工具描述，模型会看到这个描述。
    
    Args:
        query: 查询内容
    
    Returns:
        查询结果
    """
    # 实现逻辑
    return f"Result for: {query}"
```

## 在 Agent 中使用

```python
agent = Agent(
    tools=[my_tool, another_tool],
)
```

## 三层注册表

```python
from app.tools import ToolRegistry, get_tool_registry

registry = get_tool_registry()

# Framework 级注册
registry.register_framework_tool(my_tool)

# 获取 Agent 工具（合并三层）
tools = registry.get_tools_for_agent(
    agent_tools=[custom_tool],
    project_id="my-project",
)
```

## 工具覆盖

```python
from app.tools import ToolOverride, ProjectToolsConfig

config = ProjectToolsConfig(
    project_id="my-project",
    overrides=[
        ToolOverride(
            tool_name="my_tool",
            mode="inherit",
            description="自定义描述",
        ),
    ],
    disabled_tools=["unwanted_tool"],
)
```

## MCP 集成

```python
from app.tools.mcp import create_mcp_tools
from app.tools.config import MCPServerConfig

tools = create_mcp_tools([
    MCPServerConfig(name="docs", url="https://docs.agno.com/mcp"),
    MCPServerConfig(name="git", command="uvx mcp-server-git"),
])

agent = Agent(tools=tools)
```

## 覆盖模式

| 模式 | 说明 |
|------|------|
| inherit | 继承原工具，修改属性 |
| wrap | 包装原工具，添加前后处理 |
| replace | 完全替换实现 |


"""
MCP 工具集成

基于 Agno 官方 MCPTools 的最佳实践封装。

支持的传输方式:
- streamable-http: HTTP 远程服务器
- stdio: 本地命令行工具

使用示例:

```python
from app.tools.mcp import create_mcp_tools, MCPServerConfig

# 单个 HTTP 服务器
tools = create_mcp_tools([
    MCPServerConfig(name="docs", url="https://docs.agno.com/mcp"),
])

# 本地命令行工具
tools = create_mcp_tools([
    MCPServerConfig(name="git", command="uvx mcp-server-git"),
])

# Agent 中使用
agent = Agent(tools=tools)
```
"""

import asyncio
import logging
from typing import Any, List, Optional

from app.tools.config import MCPServerConfig

logger = logging.getLogger(__name__)


def create_mcp_tools(
    servers: Optional[List[MCPServerConfig]] = None,
) -> List[Any]:
    """
    创建 MCP 工具列表（同步版本）
    
    封装 Agno 官方 MCPTools，支持 HTTP 和 Stdio 两种传输方式。
    
    注意：
    - AgentOS 会自动管理 MCP 的生命周期（connect/close）
    - 不要在 AgentOS 中使用 reload=True，会导致连接问题
    
    Args:
        servers: MCP 服务器配置列表
        
    Returns:
        MCPTools 实例列表，可直接传递给 Agent.tools
        
    使用示例:
    
    ```python
    from app.tools.mcp import create_mcp_tools
    from app.tools.config import MCPServerConfig
    
    # HTTP 远程服务器
    tools = create_mcp_tools([
        MCPServerConfig(
            name="context7",
            url="https://context7.com/mcp",
        ),
    ])
    
    # 本地命令行工具（如 git MCP）
    tools = create_mcp_tools([
        MCPServerConfig(
            name="git",
            command="uvx mcp-server-git",
        ),
    ])
    
    agent = Agent(
        tools=[*my_tools, *tools],
    )
    ```
    """
    if not servers:
        return []
    
    tools = []
    
    try:
        from agno.tools.mcp import MCPTools
        
        for server in servers:
            try:
                mcp = _create_single_mcp_tool(server)
                if mcp:
                    tools.append(mcp)
                    logger.info("Created MCP tool: %s", server.name)
            except Exception as e:
                logger.error(
                    "Failed to create MCP tool %s: %s",
                    server.name,
                    str(e),
                )
    except ImportError:
        logger.warning(
            "agno.tools.mcp not available. Install with: pip install agno[mcp]"
        )
    
    return tools


def _create_single_mcp_tool(server: MCPServerConfig) -> Optional[Any]:
    """
    创建单个 MCPTools 实例
    
    Args:
        server: MCP 服务器配置
        
    Returns:
        MCPTools 实例
    """
    from agno.tools.mcp import MCPTools
    
    # HTTP 传输方式（远程服务器）
    if server.url:
        mcp = MCPTools(
            transport="streamable-http",
            url=server.url,
            # 可选：添加工具名称前缀避免冲突
            tool_name_prefix=server.tool_name_prefix,
        )
        return mcp
    
    # Stdio 传输方式（本地命令）
    if server.command:
        mcp = MCPTools(
            command=server.command,
            tool_name_prefix=server.tool_name_prefix,
        )
        return mcp
    
    logger.warning(
        "MCP server %s has no url or command configured",
        server.name,
    )
    return None


async def create_mcp_tools_async(
    servers: Optional[List[MCPServerConfig]] = None,
    allow_partial_failure: bool = True,
) -> List[Any]:
    """
    创建 MCP 工具列表（异步版本）
    
    适用于需要预连接 MCP 服务器的场景（非 AgentOS 环境）。
    
    Args:
        servers: MCP 服务器配置列表
        allow_partial_failure: 是否允许部分服务器连接失败
        
    Returns:
        已连接的 MCPTools 实例列表
        
    使用示例:
    
    ```python
    import asyncio
    from app.tools.mcp import create_mcp_tools_async
    
    async def main():
        tools = await create_mcp_tools_async([
            MCPServerConfig(name="docs", url="https://docs.agno.com/mcp"),
        ])
        
        agent = Agent(tools=tools)
        await agent.aprint_response("List available tools")
        
        # 清理连接
        for tool in tools:
            await tool.close()
    
    asyncio.run(main())
    ```
    """
    if not servers:
        return []
    
    tools = []
    
    try:
        from agno.tools.mcp import MCPTools
        
        for server in servers:
            try:
                mcp = _create_single_mcp_tool(server)
                if mcp:
                    await mcp.connect()
                    tools.append(mcp)
                    logger.info("Connected to MCP server: %s", server.name)
            except Exception as e:
                logger.error(
                    "Failed to connect to MCP server %s: %s",
                    server.name,
                    str(e),
                )
                if not allow_partial_failure:
                    raise
    except ImportError:
        logger.warning(
            "agno.tools.mcp not available. Install with: pip install agno[mcp]"
        )
    
    return tools


def create_multi_mcp_tools(
    commands: List[str],
    env: Optional[dict] = None,
    timeout_seconds: int = 30,
    allow_partial_failure: bool = True,
) -> Any:
    """
    创建多服务器 MCP 工具（使用 MultiMCPTools）
    
    适用于需要同时连接多个 Stdio MCP 服务器的场景。
    
    Args:
        commands: MCP 服务器命令列表
        env: 环境变量字典
        timeout_seconds: 连接超时秒数
        allow_partial_failure: 是否允许部分连接失败
        
    Returns:
        MultiMCPTools 实例
        
    使用示例:
    
    ```python
    from app.tools.mcp import create_multi_mcp_tools
    from os import getenv
    
    mcp_tools = create_multi_mcp_tools(
        commands=[
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx -y @modelcontextprotocol/server-brave-search",
        ],
        env={
            "BRAVE_API_KEY": getenv("BRAVE_API_KEY"),
        },
        allow_partial_failure=True,
    )
    ```
    """
    try:
        from agno.tools.mcp import MultiMCPTools
        
        return MultiMCPTools(
            commands,
            env=env,
            timeout_seconds=timeout_seconds,
            allow_partial_failure=allow_partial_failure,
        )
    except ImportError:
        logger.warning(
            "agno.tools.mcp not available. Install with: pip install agno[mcp]"
        )
        return None


# ============== 使用示例（配合 AgentOS） ==============
#
# AgentOS 会自动管理 MCP 生命周期，无需手动 connect/close：
#
# ```python
# from agno.agent import Agent
# from agno.os import AgentOS
# from app.tools.mcp import create_mcp_tools
# from app.tools.config import MCPServerConfig
#
# mcp_tools = create_mcp_tools([
#     MCPServerConfig(name="docs", url="https://docs.agno.com/mcp"),
# ])
#
# agent = Agent(
#     id="mcp-agent",
#     tools=mcp_tools,
# )
#
# agent_os = AgentOS(
#     agents=[agent],
# )
#
# # 重要：不要使用 reload=True，会导致 MCP 连接问题
# agent_os.serve(app="main:app")
# ```

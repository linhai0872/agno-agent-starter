"""
MCP (Model Context Protocol) 集成

支持双向 MCP 集成：
1. Server: 暴露本框架工具给外部 Agent
2. Client: 消费外部 MCP 服务的工具
"""

from app.tools.mcp.client import (
    create_mcp_tools,
    create_mcp_tools_async,
    create_multi_mcp_tools,
)

__all__ = [
    "create_mcp_tools",
    "create_mcp_tools_async",
    "create_multi_mcp_tools",
]



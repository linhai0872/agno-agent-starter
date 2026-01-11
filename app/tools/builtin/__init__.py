"""
框架级内置工具

这些工具在框架级别注册，可被所有项目和 Agent 使用。
项目和 Agent 可以通过 ToolOverride 对这些工具进行定制。
"""

from app.tools.builtin.http_client import http_get, http_post
from app.tools.builtin.tavily import (
    TavilyToolNames,
    create_tavily_extract_tool,
    create_tavily_search_tool,
    create_tavily_tools,
    get_tavily_tools,
)
from app.tools.builtin.web_search import web_search

__all__ = [
    # 基础工具
    "web_search",
    "http_get",
    "http_post",
    # Tavily 工具
    "create_tavily_tools",
    "create_tavily_search_tool",
    "create_tavily_extract_tool",
    "get_tavily_tools",
    "TavilyToolNames",
]

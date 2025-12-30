"""
框架级内置工具

这些工具在框架级别注册，可被所有项目和 Agent 使用。
项目和 Agent 可以通过 ToolOverride 对这些工具进行定制。
"""

from app.tools.builtin.web_search import web_search
from app.tools.builtin.http_client import http_get, http_post

__all__ = [
    "web_search",
    "http_get",
    "http_post",
]



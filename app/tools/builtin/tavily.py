"""
Tavily 搜索和内容抽取工具

Agno 原生支持的 Tavily 工具集，提供：
1. tavily_search - 网络搜索
2. tavily_extract - 网页内容抽取（需要 TavilyTools extract 模式）

使用示例:

```python
from app.tools.builtin.tavily import create_tavily_tools, TAVILY_SEARCH_TOOLS

# 获取搜索工具
tools = create_tavily_tools()

# 在 Agent 中使用
agent = Agent(
    tools=tools,
)
```

环境变量:
    TAVILY_API_KEY: Tavily API 密钥（必需）
"""

import os
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def create_tavily_tools(
    api_key: Optional[str] = None,
    enable_search: bool = True,
    enable_extract: bool = True,
    max_tokens: int = 6000,
    search_depth: str = "advanced",
    extract_depth: str = "basic",
    include_answer: bool = True,
    format: str = "markdown",
) -> List[Any]:
    """
    创建 Tavily 搜索和抽取工具
    
    Args:
        api_key: Tavily API 密钥（默认从环境变量 TAVILY_API_KEY 获取）
        enable_search: 是否启用搜索功能 (web_search_using_tavily)
        enable_extract: 是否启用内容抽取功能 (extract_content_from_urls)
        max_tokens: 最大 token 数
        search_depth: 搜索深度 - "basic" 或 "advanced"
        extract_depth: 抽取深度 - "basic" 或 "advanced"
        include_answer: 是否包含 AI 生成的答案
        format: 输出格式 - "markdown" 或 "json"
        
    Returns:
        TavilyTools 实例列表，可直接传递给 Agent.tools
        
    使用示例:
    
    ```python
    from app.tools.builtin.tavily import create_tavily_tools
    
    # 使用默认配置（搜索 + 抽取）
    tools = create_tavily_tools()
    
    # 仅搜索
    tools = create_tavily_tools(enable_extract=False)
    
    # 自定义配置
    tools = create_tavily_tools(
        search_depth="basic",
        max_tokens=4000,
    )
    
    agent = Agent(
        tools=tools,
    )
    ```
    """
    try:
        from agno.tools.tavily import TavilyTools
        
        tavily_key = api_key or os.getenv("TAVILY_API_KEY")
        
        if not tavily_key:
            logger.warning("TAVILY_API_KEY not set. Tavily tools will not work.")
            return []
        
        tavily = TavilyTools(
            api_key=tavily_key,
            enable_search=enable_search,
            enable_extract=enable_extract,
            max_tokens=max_tokens,
            search_depth=search_depth,
            extract_depth=extract_depth,
            include_answer=include_answer,
            format=format,
        )
        
        logger.info(
            "Created Tavily tools: search=%s, extract=%s, depth=%s",
            enable_search, enable_extract, search_depth
        )
        return [tavily]
        
    except ImportError:
        logger.warning(
            "agno.tools.tavily not available. "
            "Install with: pip install agno tavily-python"
        )
        return []
    except Exception as e:
        logger.error("Failed to create Tavily tools: %s", str(e))
        return []


def create_tavily_search_tool(
    api_key: Optional[str] = None,
    search_depth: str = "advanced",
    max_tokens: int = 6000,
) -> List[Any]:
    """
    创建 Tavily 搜索工具（仅搜索，不含抽取）
    
    Args:
        api_key: Tavily API 密钥
        search_depth: 搜索深度
        max_tokens: 最大 token 数
        
    Returns:
        TavilyTools 实例列表
    """
    return create_tavily_tools(
        api_key=api_key,
        enable_search=True,
        enable_extract=False,
        search_depth=search_depth,
        max_tokens=max_tokens,
    )


def create_tavily_extract_tool(
    api_key: Optional[str] = None,
    extract_depth: str = "basic",
    max_tokens: int = 6000,
) -> List[Any]:
    """
    创建 Tavily 内容抽取工具（仅抽取，不含搜索）
    
    Args:
        api_key: Tavily API 密钥
        extract_depth: 抽取深度
        max_tokens: 最大 token 数
        
    Returns:
        TavilyTools 实例列表
    """
    return create_tavily_tools(
        api_key=api_key,
        enable_search=False,
        enable_extract=True,
        extract_depth=extract_depth,
        max_tokens=max_tokens,
    )


# 预配置的工具实例（延迟加载）
_tavily_tools_cache: Optional[List[Any]] = None


def get_tavily_tools() -> List[Any]:
    """
    获取全局 Tavily 工具实例（缓存）
    
    Returns:
        TavilyTools 实例列表
    """
    global _tavily_tools_cache
    if _tavily_tools_cache is None:
        _tavily_tools_cache = create_tavily_tools()
    return _tavily_tools_cache


# 工具名称常量
class TavilyToolNames:
    """Tavily 工具名称常量（Agno TavilyTools 的实际工具名）"""
    
    # 搜索工具
    WEB_SEARCH = "web_search_using_tavily"
    
    # 抽取工具
    EXTRACT = "extract_url_content"


# 导出列表
TAVILY_SEARCH_TOOLS = create_tavily_tools


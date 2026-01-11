"""
内容安全检查护栏

框架级内置护栏，用于检测和过滤不安全的内容。
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# 严格模式下的阻止词列表
STRICT_BLOCKED_PATTERNS = [
    r"\b(violence|violent|kill|murder|attack|weapon)\b",
    r"\b(illegal|crime|criminal|drug|drugs)\b",
    r"\b(hate|racist|discrimination)\b",
    r"\b(exploit|abuse|harm)\b",
]

# 中等模式下的阻止词列表
MODERATE_BLOCKED_PATTERNS = [
    r"\b(kill|murder|attack|weapon)\b",
    r"\b(illegal|crime)\b",
    r"\b(hate|racist)\b",
]

# 宽松模式下的阻止词列表
PERMISSIVE_BLOCKED_PATTERNS = [
    r"\b(murder|weapon)\b",
    r"\b(hate|racist)\b",
]


def content_safety_check(
    run_output: Any,
    level: str = "moderate",
) -> None:
    """
    框架级内容安全检查

    Args:
        run_output: Agent 的输出（RunOutput 对象或字符串）
        level: 安全级别 - "strict", "moderate", "permissive"

    Raises:
        ValueError: 当内容包含不安全模式时
    """
    # 获取内容字符串
    content = str(run_output.content) if hasattr(run_output, "content") else str(run_output)

    content_lower = content.lower()

    # 根据级别选择模式列表
    if level == "strict":
        patterns = STRICT_BLOCKED_PATTERNS
    elif level == "permissive":
        patterns = PERMISSIVE_BLOCKED_PATTERNS
    else:
        patterns = MODERATE_BLOCKED_PATTERNS

    # 检查阻止模式
    for pattern in patterns:
        match = re.search(pattern, content_lower)
        if match:
            matched_text = match.group()
            logger.warning(
                "Content safety check failed: found blocked pattern '%s'",
                matched_text,
            )
            raise ValueError(f"Content contains blocked pattern: {matched_text}")

    logger.debug("Content safety check passed")

"""
输出验证护栏

框架级内置护栏，用于验证输出质量和长度。
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def quality_check(
    run_output: Any,
    min_length: int = 10,
    max_empty_ratio: float = 0.5,
) -> None:
    """
    输出质量检查
    
    Args:
        run_output: Agent 的输出（RunOutput 对象或字符串）
        min_length: 最小内容长度
        max_empty_ratio: 最大空白字符比例
        
    Raises:
        ValueError: 当输出质量不达标时
    """
    # 获取内容字符串
    if hasattr(run_output, "content"):
        content = str(run_output.content)
    else:
        content = str(run_output)
    
    # 检查长度
    if len(content) < min_length:
        message = f"Output too short: {len(content)} < {min_length}"
        logger.warning("Quality check failed: %s", message)
        raise ValueError(message)
    
    # 检查空白字符比例
    if content:
        whitespace_count = sum(1 for c in content if c.isspace())
        empty_ratio = whitespace_count / len(content)
        
        if empty_ratio > max_empty_ratio:
            message = f"Output has too much whitespace: {empty_ratio:.2%} > {max_empty_ratio:.2%}"
            logger.warning("Quality check failed: %s", message)
            raise ValueError(message)
    
    logger.debug("Quality check passed")


def length_check(
    run_output: Any,
    max_length: Optional[int] = None,
) -> None:
    """
    输出长度检查
    
    Args:
        run_output: Agent 的输出（RunOutput 对象或字符串）
        max_length: 最大内容长度
        
    Raises:
        ValueError: 当输出超过最大长度时
    """
    if max_length is None:
        return
    
    # 获取内容字符串
    if hasattr(run_output, "content"):
        content = str(run_output.content)
    else:
        content = str(run_output)
    
    if len(content) > max_length:
        message = f"Output too long: {len(content)} > {max_length}"
        logger.warning("Length check failed: %s", message)
        raise ValueError(message)
    
    logger.debug("Length check passed")



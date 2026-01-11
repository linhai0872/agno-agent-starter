"""
PII (个人身份信息) 过滤护栏

框架级内置护栏，用于检测和过滤敏感的个人信息。
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# PII 检测模式
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
}


def pii_filter_check(
    run_output: Any,
    pii_types: list[str] | None = None,
    action: str = "warn",
) -> None:
    """
    框架级 PII 过滤检查

    Args:
        run_output: Agent 的输出（RunOutput 对象或字符串）
        pii_types: 要检测的 PII 类型列表，如 ["email", "phone", "ssn"]
                   None 表示检测所有类型
        action: 检测到 PII 时的行为 - "warn" 或 "raise"

    Raises:
        ValueError: 当 action="raise" 且检测到 PII 时
    """
    # 获取内容字符串
    content = str(run_output.content) if hasattr(run_output, "content") else str(run_output)

    # 确定要检测的 PII 类型
    if pii_types is None:
        pii_types = list(PII_PATTERNS.keys())

    # 检测 PII
    found_pii = []
    for pii_type in pii_types:
        if pii_type not in PII_PATTERNS:
            continue

        pattern = PII_PATTERNS[pii_type]
        matches = re.findall(pattern, content)
        if matches:
            found_pii.append(
                {
                    "type": pii_type,
                    "count": len(matches),
                }
            )

    if found_pii:
        pii_summary = ", ".join(f"{item['type']}({item['count']})" for item in found_pii)
        message = f"PII detected in output: {pii_summary}"

        if action == "raise":
            logger.warning("PII filter check failed: %s", pii_summary)
            raise ValueError(message)
        else:
            logger.warning("PII filter warning: %s", pii_summary)
    else:
        logger.debug("PII filter check passed")

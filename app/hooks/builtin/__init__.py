"""
框架级内置护栏

这些护栏在框架级别注册，可被所有项目和 Agent 使用。
项目和 Agent 可以通过 HookOverride 对这些护栏进行定制。
"""

from app.hooks.builtin.content_safety import content_safety_check
from app.hooks.builtin.pii_filter import pii_filter_check
from app.hooks.builtin.output_validator import quality_check, length_check

__all__ = [
    "content_safety_check",
    "pii_filter_check",
    "quality_check",
    "length_check",
]



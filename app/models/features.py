"""
模型能力枚举 (借鉴 Dify ModelFeature)

统一定义模型支持的能力，替代分散的布尔字段。
"""

from enum import Enum


class ModelFeature(str, Enum):
    """模型能力枚举"""

    # 工具调用
    TOOL_CALL = "tool-call"
    MULTI_TOOL_CALL = "multi-tool-call"
    STREAM_TOOL_CALL = "stream-tool-call"

    # 多模态
    VISION = "vision"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"

    # 高级能力
    REASONING = "reasoning"
    WEB_SEARCH = "web-search"
    STRUCTURED_OUTPUT = "structured-output"
    AGENT_THOUGHT = "agent-thought"

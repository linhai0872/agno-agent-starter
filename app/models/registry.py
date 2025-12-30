"""
模型能力注册表

基于 OpenRouter API 数据，记录常用模型的能力和支持的参数。
可通过 API 动态更新，也可以硬编码常用模型作为缓存。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Set


@dataclass
class ModelCapabilities:
    """模型能力描述"""
    
    # 模型 ID
    model_id: str
    
    # 模型名称
    name: str
    
    # 上下文窗口大小
    context_length: int
    
    # 支持的参数
    supported_parameters: List[str] = field(default_factory=list)
    
    # 输入模态: text, image, file, audio, video
    input_modalities: List[str] = field(default_factory=lambda: ["text"])
    
    # 输出模态: text, audio
    output_modalities: List[str] = field(default_factory=lambda: ["text"])
    
    # 定价 (每百万 token)
    pricing_prompt: float = 0.0  # 输入价格
    pricing_completion: float = 0.0  # 输出价格
    
    # 能力标记
    supports_reasoning: bool = False  # 支持思考模式
    supports_tools: bool = False  # 支持工具调用
    supports_structured_output: bool = False  # 支持结构化输出
    supports_vision: bool = False  # 支持视觉输入
    supports_file: bool = False  # 支持文件输入
    supports_audio: bool = False  # 支持音频输入
    supports_video: bool = False  # 支持视频输入
    
    # 思考模式类型: effort / max_tokens / none
    reasoning_type: Literal["effort", "max_tokens", "none"] = "none"
    
    def __post_init__(self):
        """根据 supported_parameters 和 input_modalities 推断能力"""
        params = set(self.supported_parameters)
        modalities = set(self.input_modalities)
        
        self.supports_reasoning = "reasoning" in params
        self.supports_tools = "tools" in params
        self.supports_structured_output = "structured_outputs" in params
        self.supports_vision = "image" in modalities
        self.supports_file = "file" in modalities
        self.supports_audio = "audio" in modalities
        self.supports_video = "video" in modalities
        
        # 推断思考模式类型
        if self.supports_reasoning:
            # Gemini 系列使用 max_tokens
            if "gemini" in self.model_id.lower():
                self.reasoning_type = "max_tokens"
            # OpenAI o 系列使用 effort
            elif any(x in self.model_id.lower() for x in ["o1", "o3", "gpt-5"]):
                self.reasoning_type = "effort"
            # Anthropic 使用 max_tokens
            elif "anthropic" in self.model_id.lower():
                self.reasoning_type = "max_tokens"
            # DeepSeek 使用 max_tokens
            elif "deepseek" in self.model_id.lower():
                self.reasoning_type = "max_tokens"
            # 其他默认使用 effort
            else:
                self.reasoning_type = "effort"


# 常用模型能力注册表（基于 OpenRouter API 数据）
MODEL_REGISTRY: Dict[str, ModelCapabilities] = {
    # ============== Google Gemini 系列 ==============
    "google/gemini-3-pro-preview": ModelCapabilities(
        model_id="google/gemini-3-pro-preview",
        name="Google: Gemini 3 Pro Preview",
        context_length=1048576,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "seed", "stop", "structured_outputs", "temperature", "tool_choice",
            "tools", "top_p"
        ],
        input_modalities=["text", "image", "file", "audio", "video"],
        pricing_prompt=2.00,
        pricing_completion=12.00,
    ),
    "google/gemini-3-flash-preview": ModelCapabilities(
        model_id="google/gemini-3-flash-preview",
        name="Google: Gemini 3 Flash Preview",
        context_length=1048576,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "seed", "stop", "structured_outputs", "temperature", "tool_choice",
            "tools", "top_p"
        ],
        input_modalities=["text", "image", "file", "audio", "video"],
        pricing_prompt=0.50,
        pricing_completion=3.00,
    ),
    "google/gemini-2.5-flash-preview-09-2025": ModelCapabilities(
        model_id="google/gemini-2.5-flash-preview-09-2025",
        name="Google: Gemini 2.5 Flash Preview",
        context_length=1048576,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "seed", "stop", "structured_outputs", "temperature", "tool_choice",
            "tools", "top_p"
        ],
        input_modalities=["image", "file", "text", "audio", "video"],
        pricing_prompt=0.30,
        pricing_completion=2.50,
    ),
    "google/gemini-2.5-flash-lite-preview-09-2025": ModelCapabilities(
        model_id="google/gemini-2.5-flash-lite-preview-09-2025",
        name="Google: Gemini 2.5 Flash Lite Preview",
        context_length=1048576,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "seed", "stop", "structured_outputs", "temperature", "tool_choice",
            "tools", "top_p"
        ],
        input_modalities=["text", "image", "file", "audio", "video"],
        pricing_prompt=0.10,
        pricing_completion=0.40,
    ),
    
    # ============== Anthropic Claude 系列 ==============
    "anthropic/claude-sonnet-4": ModelCapabilities(
        model_id="anthropic/claude-sonnet-4",
        name="Anthropic: Claude Sonnet 4",
        context_length=1000000,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "stop",
            "temperature", "tool_choice", "tools", "top_k", "top_p"
        ],
        input_modalities=["image", "text", "file"],
        pricing_prompt=3.00,
        pricing_completion=15.00,
    ),
    "anthropic/claude-sonnet-4.5": ModelCapabilities(
        model_id="anthropic/claude-sonnet-4.5",
        name="Anthropic: Claude Sonnet 4.5",
        context_length=1000000,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "stop", "structured_outputs", "temperature", "tool_choice",
            "tools", "top_k", "top_p"
        ],
        input_modalities=["text", "image", "file"],
        pricing_prompt=3.00,
        pricing_completion=15.00,
    ),
    "anthropic/claude-3.5-haiku": ModelCapabilities(
        model_id="anthropic/claude-3.5-haiku",
        name="Anthropic: Claude 3.5 Haiku",
        context_length=200000,
        supported_parameters=[
            "max_tokens", "stop", "temperature", "tool_choice", "tools",
            "top_k", "top_p"
        ],
        input_modalities=["text", "image"],
        pricing_prompt=0.80,
        pricing_completion=4.00,
    ),
    
    # ============== OpenAI 系列 ==============
    "openai/gpt-4.1": ModelCapabilities(
        model_id="openai/gpt-4.1",
        name="OpenAI: GPT-4.1",
        context_length=1047576,
        supported_parameters=[
            "max_tokens", "response_format", "seed", "structured_outputs",
            "tool_choice", "tools"
        ],
        input_modalities=["image", "text", "file"],
        pricing_prompt=2.00,
        pricing_completion=8.00,
    ),
    "openai/gpt-4.1-mini": ModelCapabilities(
        model_id="openai/gpt-4.1-mini",
        name="OpenAI: GPT-4.1 Mini",
        context_length=1047576,
        supported_parameters=[
            "max_tokens", "response_format", "seed", "structured_outputs",
            "tool_choice", "tools"
        ],
        input_modalities=["image", "text", "file"],
        pricing_prompt=0.40,
        pricing_completion=1.60,
    ),
    "openai/gpt-4.1-nano": ModelCapabilities(
        model_id="openai/gpt-4.1-nano",
        name="OpenAI: GPT-4.1 Nano",
        context_length=1047576,
        supported_parameters=[
            "max_tokens", "response_format", "seed", "structured_outputs",
            "tool_choice", "tools"
        ],
        input_modalities=["image", "text", "file"],
        pricing_prompt=0.10,
        pricing_completion=0.40,
    ),
    "openai/gpt-5.2-pro": ModelCapabilities(
        model_id="openai/gpt-5.2-pro",
        name="OpenAI: GPT-5.2 Pro",
        context_length=400000,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "seed", "structured_outputs", "tool_choice", "tools"
        ],
        input_modalities=["image", "text", "file"],
        pricing_prompt=21.00,
        pricing_completion=168.00,
    ),
    
    # ============== 其他模型 ==============
    "minimax/minimax-m2.1": ModelCapabilities(
        model_id="minimax/minimax-m2.1",
        name="MiniMax: MiniMax M2.1",
        context_length=204800,
        supported_parameters=[
            "include_reasoning", "max_tokens", "reasoning", "response_format",
            "temperature", "tool_choice", "tools", "top_p"
        ],
        input_modalities=["text"],
        pricing_prompt=0.30,
        pricing_completion=1.20,
    ),
    "z-ai/glm-4.7": ModelCapabilities(
        model_id="z-ai/glm-4.7",
        name="Z.AI: GLM 4.7",
        context_length=202752,
        supported_parameters=[
            "frequency_penalty", "include_reasoning", "logit_bias", "max_tokens",
            "min_p", "presence_penalty", "reasoning", "repetition_penalty",
            "response_format", "seed", "stop", "structured_outputs", "temperature",
            "tool_choice", "tools", "top_k", "top_p"
        ],
        input_modalities=["text"],
        pricing_prompt=0.40,
        pricing_completion=1.50,
    ),
    "deepseek/deepseek-v3.2": ModelCapabilities(
        model_id="deepseek/deepseek-v3.2",
        name="DeepSeek: DeepSeek V3.2",
        context_length=163840,
        supported_parameters=[
            "frequency_penalty", "include_reasoning", "logit_bias", "logprobs",
            "max_tokens", "min_p", "presence_penalty", "reasoning",
            "repetition_penalty", "response_format", "seed", "stop",
            "structured_outputs", "temperature", "tool_choice", "tools",
            "top_k", "top_logprobs", "top_p"
        ],
        input_modalities=["text"],
        pricing_prompt=0.27,
        pricing_completion=0.40,
    ),
}


def get_model_capabilities(model_id: str) -> Optional[ModelCapabilities]:
    """获取模型能力信息"""
    return MODEL_REGISTRY.get(model_id)


def is_parameter_supported(model_id: str, parameter: str) -> bool:
    """检查模型是否支持某个参数"""
    caps = get_model_capabilities(model_id)
    if caps:
        return parameter in caps.supported_parameters
    return True  # 未知模型默认支持


def get_supported_modalities(model_id: str) -> Set[str]:
    """获取模型支持的输入模态"""
    caps = get_model_capabilities(model_id)
    if caps:
        return set(caps.input_modalities)
    return {"text"}  # 未知模型默认只支持文本


def list_models_by_capability(
    supports_reasoning: Optional[bool] = None,
    supports_vision: Optional[bool] = None,
    supports_file: Optional[bool] = None,
    max_price: Optional[float] = None,
) -> List[ModelCapabilities]:
    """按能力筛选模型"""
    results = []
    for caps in MODEL_REGISTRY.values():
        if supports_reasoning is not None and caps.supports_reasoning != supports_reasoning:
            continue
        if supports_vision is not None and caps.supports_vision != supports_vision:
            continue
        if supports_file is not None and caps.supports_file != supports_file:
            continue
        if max_price is not None and caps.pricing_prompt > max_price:
            continue
        results.append(caps)
    return results



"""
模型配置数据类

统一的多厂商模型配置接口，支持：
- OpenRouter (统一网关)
- OpenAI (原生直连)
- Google Gemini (原生直连)
- Anthropic Claude (原生直连)
- DashScope 阿里云百炼 (原生 SDK)
- Volcengine 火山方舟 (原生 SDK)
- Ollama (本地部署)
- LiteLLM (统一网关)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class ModelProvider(str, Enum):
    """
    模型提供商枚举

    支持的厂商:
    - OPENROUTER: 统一网关，支持 100+ 模型
    - OPENAI: OpenAI 原生 API
    - GOOGLE: Google Gemini API
    - ANTHROPIC: Anthropic Claude API
    - DASHSCOPE: 阿里云百炼 (Qwen 系列)
    - VOLCENGINE: 火山方舟 (豆包系列)
    - OLLAMA: 本地部署开源模型
    - LITELLM: 统一网关，支持多厂商
    """

    OPENROUTER = "openrouter"
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    DASHSCOPE = "dashscope"
    VOLCENGINE = "volcengine"
    OLLAMA = "ollama"
    LITELLM = "litellm"


# 各厂商默认 API Key 环境变量名
PROVIDER_DEFAULT_ENV_VARS: dict[ModelProvider, str | None] = {
    ModelProvider.OPENROUTER: "OPENROUTER_API_KEY",
    ModelProvider.OPENAI: "OPENAI_API_KEY",
    ModelProvider.GOOGLE: "GOOGLE_API_KEY",
    ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    ModelProvider.DASHSCOPE: "DASHSCOPE_API_KEY",
    ModelProvider.VOLCENGINE: "ARK_API_KEY",
    ModelProvider.OLLAMA: None,  # 本地部署无需 API Key
    ModelProvider.LITELLM: "LITELLM_API_KEY",
}


@dataclass
class ReasoningConfig:
    """
    思考模式配置 (多厂商支持)

    各厂商思考模式实现方式:
    - OpenRouter: reasoning.effort 或 reasoning.max_tokens
    - OpenAI: reasoning_effort (o1/o3/gpt-5 系列)
    - Google Gemini: thinking_budget / thinking_level
    - Anthropic Claude: thinking.budget_tokens
    - DashScope: enable_thinking (Qwen3-Thinking)
    - 火山方舟: thinking.type (豆包 Seed 系列)
    - Ollama: 不支持
    - LiteLLM: 透传底层模型参数
    """

    # 是否启用思考模式
    enabled: bool = False

    # 思考努力等级: none / minimal / low / medium / high / xhigh
    # OpenRouter/OpenAI 统一支持
    effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = "medium"

    # 思考最大 token 数 (Gemini/Anthropic/DeepSeek 使用)
    max_tokens: int | None = None

    # 是否在响应中包含推理过程
    include_reasoning: bool = False

    # ============== 厂商特有配置 ==============

    # Anthropic Claude: thinking 配置类型
    anthropic_thinking_type: Literal["enabled", "disabled"] = "enabled"

    # Google Gemini: thinking_level 简化配置
    google_thinking_level: Literal["low", "high"] | None = None

    # 火山方舟: thinking 类型 (doubao-seed 仅支持 enabled/disabled)
    volcengine_thinking_type: Literal["auto", "enabled", "disabled"] = "enabled"

    def to_openrouter_params(self) -> dict[str, Any]:
        """转换为 OpenRouter API 参数"""
        if not self.enabled:
            return {}

        params = {}
        reasoning = {}
        if self.max_tokens is not None:
            reasoning["max_tokens"] = self.max_tokens
        elif self.effort != "none":
            reasoning["effort"] = self.effort

        if reasoning:
            params["reasoning"] = reasoning

        if self.include_reasoning:
            params["include_reasoning"] = True

        return params

    def to_provider_params(self, provider: "ModelProvider") -> dict[str, Any]:
        """转换为指定厂商的 API 参数"""
        if not self.enabled:
            return {}

        if provider == ModelProvider.OPENROUTER:
            return self.to_openrouter_params()
        elif provider == ModelProvider.OPENAI:
            return {"reasoning_effort": self.effort} if self.effort != "none" else {}
        elif provider == ModelProvider.GOOGLE:
            params = {}
            if self.max_tokens:
                params["thinking_budget"] = self.max_tokens
            if self.google_thinking_level:
                params["thinking_level"] = self.google_thinking_level
            if self.include_reasoning:
                params["include_thoughts"] = True
            return params
        elif provider == ModelProvider.ANTHROPIC:
            return {
                "thinking": {
                    "type": self.anthropic_thinking_type,
                    "budget_tokens": self.max_tokens or 1024,
                }
            }
        elif provider == ModelProvider.VOLCENGINE:
            return {"thinking": {"type": self.volcengine_thinking_type}}
        elif provider == ModelProvider.DASHSCOPE:
            return {"enable_thinking": True}
        else:
            return {}


@dataclass
class WebSearchConfig:
    """
    网络搜索配置 (多厂商支持)

    各厂商网络搜索实现方式:
    - OpenRouter: plugins 参数或 :online 后缀
    - OpenAI: 需要通过工具调用实现
    - Google Gemini: search=True 原生参数
    - Anthropic: 需要通过工具调用实现
    - DashScope: enable_search=True
    - 火山方舟: tools=[{"type": "web_search"}]
    - Ollama: 需要通过工具调用实现
    - LiteLLM: 透传底层模型参数
    """

    # 是否启用网络搜索
    enabled: bool = False

    # ============== OpenRouter 配置 ==============

    # 搜索引擎: auto / native / exa
    engine: Literal["auto", "native", "exa"] = "auto"

    # 最大搜索结果数 (1-10)
    max_results: int = 5

    # 搜索上下文大小 (仅原生搜索支持): low / medium / high
    search_context_size: Literal["low", "medium", "high"] = "medium"

    # 自定义搜索提示
    search_prompt: str | None = None

    # ============== DashScope 配置 ==============

    # 搜索策略: standard / pro
    dashscope_search_strategy: Literal["standard", "pro"] = "standard"

    # 是否强制联网搜索
    dashscope_forced_search: bool = False

    # ============== 火山方舟配置 ==============

    # 最大搜索关键词数 (1-50)
    volcengine_max_keyword: int = 3

    # 搜索结果数量限制
    volcengine_limit: int = 10

    # 搜索来源: ["toutiao", "douyin", "moji"] 等
    volcengine_sources: list[str] | None = None

    def to_openrouter_params(self) -> dict[str, Any]:
        """转换为 OpenRouter API 参数"""
        if not self.enabled:
            return {}

        plugin = {"id": "web"}

        if self.engine != "auto":
            plugin["engine"] = self.engine

        if self.max_results != 5:
            plugin["max_results"] = self.max_results

        if self.search_prompt:
            plugin["search_prompt"] = self.search_prompt

        params = {"plugins": [plugin]}

        # 原生搜索的上下文大小控制
        if self.engine == "native" and self.search_context_size != "medium":
            params["web_search_options"] = {"search_context_size": self.search_context_size}

        return params

    def get_model_suffix(self) -> str:
        """获取模型 ID 后缀（使用 :online 方式时）"""
        return ":online" if self.enabled else ""

    def to_provider_params(self, provider: "ModelProvider") -> dict[str, Any]:
        """转换为指定厂商的 API 参数"""
        if not self.enabled:
            return {}

        if provider == ModelProvider.OPENROUTER:
            return self.to_openrouter_params()
        elif provider == ModelProvider.GOOGLE:
            return {"search": True}
        elif provider == ModelProvider.DASHSCOPE:
            params = {"enable_search": True}
            if self.dashscope_search_strategy != "standard" or self.dashscope_forced_search:
                params["search_options"] = {
                    "search_strategy": self.dashscope_search_strategy,
                    "forced_search": self.dashscope_forced_search,
                }
            return params
        elif provider == ModelProvider.VOLCENGINE:
            tool = {"type": "web_search", "max_keyword": self.volcengine_max_keyword}
            if self.volcengine_limit != 10:
                tool["limit"] = self.volcengine_limit
            if self.volcengine_sources:
                tool["sources"] = self.volcengine_sources
            return {"tools": [tool]}
        else:
            # OpenAI/Anthropic/Ollama/LiteLLM 需要通过工具调用实现
            return {}


@dataclass
class MultimodalConfig:
    """
    多模态配置 (多厂商支持)

    支持的输入模态:
    - text: 纯文本 (所有厂商)
    - image: 图片 (GPT-4V, Claude 3, Gemini, Qwen-VL, 豆包视觉)
    - file: 文件 PDF (OpenAI Files API, Gemini, Anthropic, qwen-long)
    - video: 视频 (Gemini, 火山方舟)
    """

    # 是否启用 PDF 增强（让非原生支持的模型也能处理 PDF）
    enable_pdf_enhancement: bool = False

    # 图片详细程度: auto / low / high
    image_detail: Literal["auto", "low", "high"] = "auto"

    # ============== 火山方舟配置 ==============

    # 图片像素限制
    volcengine_max_pixels: int | None = None
    volcengine_min_pixels: int | None = None


@dataclass
class StructuredOutputConfig:
    """
    结构化输出配置 (多厂商支持)

    各厂商结构化输出实现方式:
    - OpenRouter: 透传底层模型
    - OpenAI: response_format json_schema
    - Google Gemini: response_mime_type + response_schema
    - Anthropic: 不支持
    - DashScope: response_format json_object
    - 火山方舟: response_format json_schema
    - Ollama: output_schema (Pydantic)
    - LiteLLM: 透传底层模型
    """

    # 是否启用结构化输出
    enabled: bool = False

    # 输出格式类型: json_object / json_schema
    response_type: Literal["json_object", "json_schema"] = "json_object"

    # JSON Schema 定义 (json_schema 模式下使用)
    json_schema: dict[str, Any] | None = None

    # Schema 名称 (部分厂商需要)
    schema_name: str = "response"

    # 严格模式 (仅部分厂商支持)
    strict: bool = False

    def to_provider_params(self, provider: "ModelProvider") -> dict[str, Any]:
        """转换为指定厂商的 API 参数"""
        if not self.enabled:
            return {}

        if provider in (ModelProvider.OPENAI, ModelProvider.OPENROUTER, ModelProvider.LITELLM):
            if self.response_type == "json_object":
                return {"response_format": {"type": "json_object"}}
            else:
                return {
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": self.schema_name,
                            "schema": self.json_schema or {},
                            "strict": self.strict,
                        },
                    }
                }
        elif provider == ModelProvider.GOOGLE:
            return {"response_mime_type": "application/json"}
        elif provider == ModelProvider.DASHSCOPE:
            return {"response_format": {"type": "json_object"}}
        elif provider == ModelProvider.VOLCENGINE:
            if self.response_type == "json_object":
                return {"response_format": {"type": "json_object"}}
            else:
                return {
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": self.schema_name,
                            "schema": self.json_schema or {},
                            "strict": self.strict,
                        },
                    }
                }
        else:
            return {}


@dataclass
class ProjectConfig:
    """
    项目级配置

    用于 Workflow/Team 统一管理 API Key，使内部所有 Agent 共享同一个 Key。

    优先级（从高到低）：
    1. Agent 级 api_key_env (ModelConfig.api_key_env)
    2. Project 级 api_key_env (ProjectConfig.api_key_env)
    3. Global OPENROUTER_API_KEY

    使用示例:

    ```python
    # .env
    CONTENT_PIPELINE_KEY = sk - pipeline - xxx

    # workflow.py
    PROJECT_CONFIG = ProjectConfig(api_key_env="CONTENT_PIPELINE_KEY")

    # 所有 Agent 共用 Project Key
    researcher = Agent(model=create_model(CONFIG, PROJECT_CONFIG))
    writer = Agent(model=create_model(CONFIG, PROJECT_CONFIG))
    ```
    """

    # API Key 环境变量名（如 "CONTENT_PIPELINE_KEY"）
    api_key_env: str | None = None


@dataclass
class ModelConfig:
    """
    统一模型配置 (多厂商支持)

    支持 8 大模型厂商的统一配置接口，通过 provider 字段切换厂商。

    使用示例:

    ```python
    # OpenRouter (默认)
    config = ModelConfig(
        model_id="google/gemini-2.5-flash-preview-09-2025",
        temperature=0.1,
    )

    # OpenAI 直连
    config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o",
        api_key_env="OPENAI_API_KEY",
    )

    # Google Gemini 直连
    config = ModelConfig(
        provider=ModelProvider.GOOGLE,
        model_id="gemini-2.5-flash",
        reasoning=ReasoningConfig(enabled=True, max_tokens=2048),
        web_search=WebSearchConfig(enabled=True),  # 原生支持
    )

    # 阿里云 DashScope
    config = ModelConfig(
        provider=ModelProvider.DASHSCOPE,
        model_id="qwen-plus",
        web_search=WebSearchConfig(enabled=True, dashscope_search_strategy="pro"),
    )

    # 火山方舟
    config = ModelConfig(
        provider=ModelProvider.VOLCENGINE,
        model_id="doubao-seed-1-6-251015",
        reasoning=ReasoningConfig(enabled=True),
    )

    # Ollama 本地
    config = ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_id="llama3.2:latest",
        ollama_host="http://localhost:11434",
    )

    # LiteLLM 网关
    config = ModelConfig(
        provider=ModelProvider.LITELLM,
        model_id="gpt-4o",
    )
    ```
    """

    # ============== 基础配置 ==============

    # 模型提供商
    provider: ModelProvider = ModelProvider.OPENROUTER

    # 模型 ID
    # - OpenRouter: provider/model-name (如 "google/gemini-2.5-flash")
    # - OpenAI: model name (如 "gpt-4o")
    # - Google: model name (如 "gemini-2.5-flash")
    # - Anthropic: model name (如 "claude-sonnet-4")
    # - DashScope: model name (如 "qwen-plus")
    # - 火山方舟: endpoint id 或 model name (如 "doubao-seed-1-6-251015")
    # - Ollama: model:tag (如 "llama3.2:latest")
    # - LiteLLM: provider/model (如 "openai/gpt-4o")
    model_id: str = "google/gemini-2.5-flash-preview-09-2025"

    # API Key 环境变量名（可选）
    # 三层优先级: Agent 级 > Project 级 > Global 级
    api_key_env: str | None = None

    # ============== 通用参数 ==============

    # 温度参数 (0.0 - 2.0)
    # 控制输出随机性，0 = 确定性，2 = 最大随机
    temperature: float | None = None

    # 最大输出 token 数
    max_tokens: int | None = None

    # Top-P 采样 (0.0 - 1.0)
    # 控制多样性，与 temperature 二选一使用效果更好
    top_p: float | None = None

    # Top-K 采样 (部分模型支持)
    top_k: int | None = None

    # 频率惩罚 (-2.0 - 2.0)
    # 减少重复内容
    frequency_penalty: float | None = None

    # 存在惩罚 (-2.0 - 2.0)
    # 鼓励新主题
    presence_penalty: float | None = None

    # 随机种子 (用于可复现输出)
    seed: int | None = None

    # 停止序列
    stop: list[str] | None = None

    # ============== 高级配置 ==============

    # 思考模式配置
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)

    # 网络搜索配置
    web_search: WebSearchConfig = field(default_factory=WebSearchConfig)

    # 多模态配置
    multimodal: MultimodalConfig = field(default_factory=MultimodalConfig)

    # 结构化输出配置
    structured_output: StructuredOutputConfig = field(default_factory=StructuredOutputConfig)

    # ============== Ollama 特有配置 ==============

    # Ollama 服务地址
    ollama_host: str = "http://localhost:11434"

    # Ollama Host 环境变量名（三层优先级）
    ollama_host_env: str | None = None

    # ============== LiteLLM 特有配置 ==============

    # LiteLLM API Base URL
    litellm_api_base: str | None = None

    # LiteLLM API Base 环境变量名
    litellm_api_base_env: str | None = None

    # ============== 工具调用 ==============

    # 最大工具调用次数 (Agno Agent 参数)
    tool_call_limit: int = 20

    # 启用并行工具调用
    # 允许 LLM 在一次响应中请求多个工具调用，框架会并行执行
    # 注意：需要模型支持，OpenAI 系列模型默认支持，Gemini 通过 OpenRouter 需要显式启用
    parallel_tool_calls: bool = True

    # ============== 调试 ==============

    # 调试模式
    debug_mode: bool = False

    def get_effective_model_id(self) -> str:
        """获取有效的模型 ID（包含后缀）"""
        model_id = self.model_id

        # 添加 :online 后缀（如果启用网络搜索且使用后缀方式）
        # 注意：使用 plugins 方式时不需要后缀
        # if self.web_search.enabled and self.web_search.engine == "auto":
        #     model_id += ":online"

        return model_id

    def to_openrouter_params(self) -> dict[str, Any]:
        """转换为 OpenRouter API 参数"""
        params = {}

        # 通用参数
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.top_k is not None:
            params["top_k"] = self.top_k
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            params["seed"] = self.seed
        if self.stop:
            params["stop"] = self.stop

        # 思考模式参数
        params.update(self.reasoning.to_openrouter_params())

        # 网络搜索参数
        params.update(self.web_search.to_openrouter_params())

        return params

    def to_agno_params(self) -> dict[str, Any]:
        """转换为 Agno OpenRouter 模型参数"""
        params = {
            "id": self.get_effective_model_id(),
        }

        # 通用参数
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            params["seed"] = self.seed
        if self.stop:
            params["stop"] = self.stop

        # 思考模式 - Agno 使用 reasoning_effort 参数
        if self.reasoning.enabled:
            if self.reasoning.max_tokens:
                # 某些模型使用 max_tokens
                params["reasoning"] = {"max_tokens": self.reasoning.max_tokens}
            elif self.reasoning.effort != "none":
                # 其他模型使用 effort
                params["reasoning_effort"] = self.reasoning.effort

        # 并行工具调用 - 通过 request_params 传递给 OpenAI API
        # 允许 LLM 在一次响应中请求多个工具调用，框架会并行执行
        if self.parallel_tool_calls:
            params["request_params"] = {"parallel_tool_calls": True}

        return params

    def get_common_params(self) -> dict[str, Any]:
        """获取通用模型参数（所有厂商共享）"""
        params = {}
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.top_k is not None:
            params["top_k"] = self.top_k
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            params["seed"] = self.seed
        if self.stop:
            params["stop"] = self.stop
        return params

    def to_provider_params(self) -> dict[str, Any]:
        """转换为当前 provider 的 API 参数"""
        params = self.get_common_params()

        # 添加 Reasoning 参数
        params.update(self.reasoning.to_provider_params(self.provider))

        # 添加 Web Search 参数
        params.update(self.web_search.to_provider_params(self.provider))

        # 添加 Structured Output 参数
        params.update(self.structured_output.to_provider_params(self.provider))

        return params


@dataclass
class MemoryConfig:
    """
    Agent 记忆配置

    Agno 支持两种记忆模式（互斥，不可同时启用）：
    1. 自动模式 (enable_user_memories): 每次响应后自动管理记忆
    2. 自主模式 (enable_agentic_memory): Agent 自行决定何时创建/更新记忆

    使用示例:

    ```python
    # 自动记忆模式
    memory = MemoryConfig(
        enable_user_memories=True,
        enable_session_summaries=True,
    )

    # 自主记忆模式
    memory = MemoryConfig(
        enable_agentic_memory=True,
    )
    ```
    """

    # ============== 记忆模式（二选一） ==============

    # 启用用户记忆（自动模式）
    # 每次响应后自动创建/更新用户记忆
    enable_user_memories: bool = False

    # 启用自主记忆管理
    # Agent 自行决定何时管理记忆（与 enable_user_memories 互斥）
    enable_agentic_memory: bool = False

    # ============== 会话配置 ==============

    # 启用会话摘要
    # 自动生成会话摘要，帮助保持上下文
    enable_session_summaries: bool = False

    # ============== 上下文配置 ==============

    # 将记忆添加到上下文
    # 在响应中引用相关记忆
    add_memories_to_context: bool = True

    def to_agent_params(self) -> dict[str, Any]:
        """转换为 Agno Agent 参数"""
        params = {}

        # 记忆模式（互斥检查）
        if self.enable_agentic_memory and self.enable_user_memories:
            # agentic_memory 优先级更高，会覆盖 user_memories
            params["enable_agentic_memory"] = True
        elif self.enable_agentic_memory:
            params["enable_agentic_memory"] = True
        elif self.enable_user_memories:
            params["enable_user_memories"] = True

        # 会话摘要
        if self.enable_session_summaries:
            params["enable_session_summaries"] = True

        # 记忆上下文
        if self.add_memories_to_context:
            params["add_memories_to_context"] = True

        return params


@dataclass
class KnowledgeConfig:
    """
    知识库配置

    支持两种 RAG 模式：
    1. Agentic RAG (search_knowledge=True): Agent 主动搜索知识库
    2. Traditional RAG (add_knowledge_to_context=True): 自动将相关知识注入上下文

    使用示例:

    ```python
    # Agentic RAG（推荐）
    knowledge = KnowledgeConfig(
        enabled=True,
        search_knowledge=True,
    )

    # Traditional RAG
    knowledge = KnowledgeConfig(
        enabled=True,
        search_knowledge=False,
        add_knowledge_to_context=True,
    )
    ```
    """

    # 是否启用知识库
    enabled: bool = False

    # ============== 向量数据库配置 ==============

    # 向量数据库表名
    vector_db_table: str = "knowledge_embeddings"

    # 搜索类型: vector (纯向量) / hybrid (向量 + 关键词)
    search_type: Literal["vector", "hybrid"] = "hybrid"

    # ============== Embedder 配置 ==============

    # Embedder 模型 ID
    embedder_model: str = "text-embedding-3-small"

    # Embedder 提供商
    embedder_provider: Literal["openai", "cohere", "sentence_transformer"] = "openai"

    # ============== Reranker 配置 ==============

    # 是否启用 Reranker
    enable_reranker: bool = False

    # Reranker 模型
    reranker_model: str = "rerank-v3.5"

    # Reranker 提供商
    reranker_provider: Literal["cohere", "sentence_transformer"] = "cohere"

    # ============== RAG 模式配置 ==============

    # Agentic RAG: Agent 主动搜索知识库
    # 当提供 knowledge 参数时默认启用
    search_knowledge: bool = True

    # Traditional RAG: 自动将相关知识注入上下文
    # 与 search_knowledge 通常二选一
    add_knowledge_to_context: bool = False

    # ============== 检索配置 ==============

    # 检索结果数量
    num_results: int = 5

    def to_agent_params(self) -> dict[str, Any]:
        """转换为 Agno Agent 参数"""
        if not self.enabled:
            return {}

        params = {
            "search_knowledge": self.search_knowledge,
        }

        if self.add_knowledge_to_context:
            params["add_knowledge_to_context"] = True

        return params

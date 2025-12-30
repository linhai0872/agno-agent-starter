"""
阿里云 DashScope 模型适配器

使用 dashscope 官方 SDK。
支持: Qwen-Plus, Qwen-Max, Qwen-VL, qwen-long
特性: 联网搜索, 多模态, 文档理解
"""

import logging
import os
from typing import Any, Dict, Iterator, List, Optional, Union

from app.models.config import ModelConfig, ModelProvider, ProjectConfig, PROVIDER_DEFAULT_ENV_VARS

logger = logging.getLogger(__name__)


def _get_api_key(
    config: ModelConfig,
    project_config: Optional[ProjectConfig],
) -> Optional[str]:
    """三层 API Key 优先级获取"""
    # 1. Agent 级
    if config.api_key_env:
        api_key = os.environ.get(config.api_key_env)
        if api_key:
            return api_key
    
    # 2. Project 级
    if project_config and project_config.api_key_env:
        api_key = os.environ.get(project_config.api_key_env)
        if api_key:
            return api_key
    
    # 3. Global 级
    default_env = PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.DASHSCOPE)
    if default_env:
        return os.environ.get(default_env)
    
    return None


class DashScopeModel:
    """
    阿里云 DashScope 模型适配器
    
    特性:
    - 联网搜索: enable_search + search_options
    - 多模态: Qwen-VL 支持图片/视频
    - 文档理解: qwen-long 支持 PDF (通过 OpenAI 兼容接口)
    - 思考模式: Qwen3-Thinking
    
    PDF 文件处理:
    - 使用 upload_file() 上传 PDF 获取 file_id
    - 在 system message 中使用 fileid://{file_id} 引用
    - 使用 qwen-long 模型处理文档
    """
    
    def __init__(
        self,
        model_id: str,
        api_key: str,
        config: ModelConfig,
    ):
        self.api_key = api_key
        try:
            import dashscope
        except ImportError:
            raise ImportError(
                "dashscope package not found. Install with: pip install dashscope"
            )
        
        # 设置 API Key (DashScope SDK 使用全局设置)
        dashscope.api_key = api_key
        
        self.model_id = model_id
        self.config = config
        self._dashscope = dashscope
    
    def _build_params(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建 DashScope API 参数"""
        params = {
            "model": self.model_id,
            "messages": messages,
        }
        
        # 通用参数
        if self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            params["max_tokens"] = self.config.max_tokens
        if self.config.top_p is not None:
            params["top_p"] = self.config.top_p
        if self.config.top_k is not None:
            params["top_k"] = self.config.top_k
        if self.config.seed is not None:
            params["seed"] = self.config.seed
        if self.config.stop:
            params["stop"] = self.config.stop
        
        # 联网搜索
        if self.config.web_search.enabled:
            params["enable_search"] = True
            search_options = {}
            if self.config.web_search.dashscope_search_strategy != "standard":
                search_options["search_strategy"] = self.config.web_search.dashscope_search_strategy
            if self.config.web_search.dashscope_forced_search:
                search_options["forced_search"] = True
            if search_options:
                params["search_options"] = search_options
        
        # 思考模式 (Qwen3-Thinking)
        if self.config.reasoning.enabled:
            params["extra_body"] = {"enable_thinking": True}
        
        # 结构化输出
        if self.config.structured_output.enabled:
            params["response_format"] = {"type": "json_object"}
        
        return params
    
    def _is_multimodal(self, messages: List[Dict[str, Any]]) -> bool:
        """检测消息是否包含多模态内容（图片/视频）"""
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and ("image" in item or "video" in item):
                        return True
        return False
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        发送聊天请求
        
        自动检测多模态消息并使用对应 API:
        - 多模态消息 (图片/视频): MultiModalConversation
        - 纯文本消息: Generation
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
        
        Returns:
            响应对象或流式迭代器
        """
        # 检测是否为多模态消息
        if self._is_multimodal(messages):
            return self._chat_multimodal(messages, stream)
        else:
            return self._chat_text(messages, stream)
    
    def _chat_text(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """纯文本对话 - 使用 Generation API"""
        from dashscope import Generation
        
        params = self._build_params(messages)
        
        if stream:
            params["stream"] = True
            params["incremental_output"] = True
            responses = Generation.call(**params)
            return self._handle_stream(responses)
        else:
            response = Generation.call(**params)
            return self._handle_response(response)
    
    def _chat_multimodal(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """多模态对话 - 使用 MultiModalConversation API"""
        from dashscope import MultiModalConversation
        
        # 多模态 API 使用不同的模型名称
        model_id = self.model_id
        if not model_id.startswith("qwen-vl"):
            model_id = "qwen-vl-max"  # 默认使用 qwen-vl-max
        
        if stream:
            responses = MultiModalConversation.call(
                model=model_id,
                messages=messages,
                stream=True,
                incremental_output=True,
            )
            return self._handle_multimodal_stream(responses)
        else:
            response = MultiModalConversation.call(
                model=model_id,
                messages=messages,
            )
            return self._handle_multimodal_response(response)
    
    def _handle_multimodal_response(self, response) -> Dict[str, Any]:
        """处理多模态非流式响应"""
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope API error: {response.code} - {response.message}"
            )
        
        content = response.output.choices[0].message.content
        # 多模态响应的 content 可能是 list 格式
        if isinstance(content, list):
            text = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
        else:
            text = content
        
        return {
            "content": text,
            "usage": {
                "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                "completion_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            },
            "raw": response,
        }
    
    def _handle_multimodal_stream(self, responses) -> Iterator[Dict[str, Any]]:
        """处理多模态流式响应"""
        for response in responses:
            if response.status_code != 200:
                raise RuntimeError(
                    f"DashScope API error: {response.code} - {response.message}"
                )
            
            content = response.output.choices[0].message.content
            if isinstance(content, list):
                text = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
            else:
                text = content or ""
            
            yield {
                "content": text,
                "raw": response,
            }
    
    def _handle_response(self, response) -> Dict[str, Any]:
        """处理非流式响应"""
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope API error: {response.code} - {response.message}"
            )
        
        return {
            "content": response.output.text if hasattr(response.output, "text") else response.output.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "raw": response,
        }
    
    def _handle_stream(self, responses) -> Iterator[Dict[str, Any]]:
        """处理流式响应"""
        for response in responses:
            if response.status_code != 200:
                raise RuntimeError(
                    f"DashScope API error: {response.code} - {response.message}"
                )
            
            content = ""
            if hasattr(response.output, "text"):
                content = response.output.text
            elif hasattr(response.output, "choices") and response.output.choices:
                content = response.output.choices[0].message.content
            
            yield {
                "content": content,
                "usage": {
                    "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                    "completion_tokens": getattr(response.usage, "output_tokens", 0),
                },
                "raw": response,
            }
    
    # ============== PDF 文件处理 (使用 OpenAI 兼容接口) ==============
    
    def _get_openai_client(self):
        """获取 OpenAI 兼容客户端"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not found. Install with: pip install openai")
        
        return OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    
    def upload_file(self, file_path: str) -> str:
        """
        上传文件到 DashScope (用于 qwen-long 文档理解)
        
        Args:
            file_path: 本地文件路径
        
        Returns:
            file_id: 文件 ID，用于后续调用
        """
        client = self._get_openai_client()
        
        with open(file_path, "rb") as f:
            file_object = client.files.create(file=f, purpose="file-extract")
        
        logger.info("Uploaded file to DashScope: %s -> %s", file_path, file_object.id)
        return file_object.id
    
    def chat_with_file(
        self,
        file_id: str,
        query: str,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用 qwen-long 处理已上传的文件
        
        Args:
            file_id: 上传文件返回的 file_id
            query: 用户问题
            model_id: 模型 ID，默认使用 qwen-long
        
        Returns:
            响应字典
        """
        client = self._get_openai_client()
        
        response = client.chat.completions.create(
            model=model_id or "qwen-long",
            messages=[
                {"role": "system", "content": f"fileid://{file_id}"},
                {"role": "user", "content": query},
            ],
        )
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "raw": response,
        }
    
    def chat_with_pdf(
        self,
        file_path: str,
        query: str,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        便捷方法：上传 PDF 并提问
        
        Args:
            file_path: PDF 文件路径
            query: 用户问题
            model_id: 模型 ID，默认使用 qwen-long
        
        Returns:
            响应字典
        """
        file_id = self.upload_file(file_path)
        return self.chat_with_file(file_id, query, model_id)


def create_dashscope_model(
    config: ModelConfig,
    project_config: Optional[ProjectConfig] = None,
) -> DashScopeModel:
    """
    创建 DashScope 模型实例
    
    Args:
        config: 模型配置
        project_config: 项目级配置
    
    Returns:
        DashScope 模型适配器实例
    """
    api_key = _get_api_key(config, project_config)
    
    if not api_key:
        raise ValueError(
            "DashScope API Key not found. Please set one of: "
            f"config.api_key_env, project_config.api_key_env, or {PROVIDER_DEFAULT_ENV_VARS.get(ModelProvider.DASHSCOPE)}"
        )
    
    logger.info("Creating DashScope model: %s", config.model_id)
    
    return DashScopeModel(
        model_id=config.model_id,
        api_key=api_key,
        config=config,
    )


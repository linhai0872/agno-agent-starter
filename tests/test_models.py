"""
模型配置测试示例

运行测试:
    pytest tests/test_models.py -v
"""

from app.models.config import (
    KnowledgeConfig,
    MemoryConfig,
    ModelConfig,
    ModelProvider,
    ReasoningConfig,
    WebSearchConfig,
)


class TestModelConfig:
    """ModelConfig 单元测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ModelConfig()

        assert config.provider == ModelProvider.OPENROUTER
        assert config.model_id == "google/gemini-2.5-flash-preview-09-2025"
        assert config.temperature is None
        assert config.max_tokens is None

    def test_custom_config(self):
        """测试自定义配置"""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-4o",
            temperature=0.7,
            max_tokens=4096,
        )

        assert config.provider == ModelProvider.OPENAI
        assert config.model_id == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_reasoning_config(self):
        """测试思考模式配置"""
        reasoning = ReasoningConfig(
            enabled=True,
            effort="high",
            max_tokens=2048,
        )

        assert reasoning.enabled is True
        assert reasoning.effort == "high"
        assert reasoning.max_tokens == 2048

        # 测试 OpenRouter 参数转换
        params = reasoning.to_openrouter_params()
        assert "reasoning" in params
        assert params["reasoning"]["max_tokens"] == 2048

    def test_web_search_config(self):
        """测试网络搜索配置"""
        web_search = WebSearchConfig(
            enabled=True,
            max_results=3,
        )

        assert web_search.enabled is True
        assert web_search.max_results == 3

        # 测试 OpenRouter 参数转换
        params = web_search.to_openrouter_params()
        assert "plugins" in params


class TestMemoryConfig:
    """MemoryConfig 单元测试"""

    def test_default_memory(self):
        """测试默认记忆配置"""
        memory = MemoryConfig()

        assert memory.enable_user_memories is False
        assert memory.enable_agentic_memory is False

    def test_user_memories(self):
        """测试用户记忆模式"""
        memory = MemoryConfig(
            enable_user_memories=True,
            enable_session_summaries=True,
        )

        params = memory.to_agent_params()
        assert params.get("enable_user_memories") is True
        assert params.get("enable_session_summaries") is True

    def test_agentic_memory(self):
        """测试自主记忆模式"""
        memory = MemoryConfig(enable_agentic_memory=True)

        params = memory.to_agent_params()
        assert params.get("enable_agentic_memory") is True


class TestKnowledgeConfig:
    """KnowledgeConfig 单元测试"""

    def test_agentic_rag(self):
        """测试 Agentic RAG 配置"""
        knowledge = KnowledgeConfig(
            enabled=True,
            search_knowledge=True,
        )

        params = knowledge.to_agent_params()
        assert params.get("search_knowledge") is True

    def test_traditional_rag(self):
        """测试 Traditional RAG 配置"""
        knowledge = KnowledgeConfig(
            enabled=True,
            search_knowledge=False,
            add_knowledge_to_context=True,
        )

        params = knowledge.to_agent_params()
        assert params.get("add_knowledge_to_context") is True

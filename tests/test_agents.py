"""
Agent 集成测试

运行测试:
    pytest tests/test_agents.py -v

注意: 这些测试需要数据库连接，运行前确保:
1. PostgreSQL 已启动: docker compose up -d agno-postgres
2. 环境变量已配置: OPENROUTER_API_KEY
"""

import pytest
from unittest.mock import MagicMock, patch

from app.agents.structured_output.schemas import (
    EntityInfo,
    MovieScript,
    ResearchReport,
)


class TestStructuredOutputSchemas:
    """Structured Output Schema 单元测试"""

    def test_movie_script_schema(self):
        """测试电影剧本 Schema"""
        movie = MovieScript(
            name="测试电影",
            genre="科幻",
            setting="未来城市",
            characters=["主角 - 英雄", "反派 - 恶棍"],
            storyline="这是一个关于英雄的故事...",
            ending="英雄获胜",
        )
        
        assert movie.name == "测试电影"
        assert movie.genre == "科幻"
        assert len(movie.characters) == 2
        
        # 测试序列化
        data = movie.model_dump()
        assert data["name"] == "测试电影"
        assert "characters" in data

    def test_research_report_schema(self):
        """测试研究报告 Schema"""
        report = ResearchReport(
            title="测试报告",
            summary="这是一份测试报告",
            key_findings=["发现1", "发现2"],
            analysis="详细分析内容...",
            recommendations=["建议1"],
            sources=["来源1"],
            confidence_score=0.85,
        )
        
        assert report.title == "测试报告"
        assert report.confidence_score == 0.85
        assert len(report.key_findings) == 2

    def test_entity_info_schema(self):
        """测试实体信息 Schema"""
        entity = EntityInfo(
            name="测试公司",
            type="company",
            description="这是一家测试公司",
            attributes={"industry": "科技", "founded": "2020"},
            verified=True,
            sources=["官网"],
        )
        
        assert entity.name == "测试公司"
        assert entity.type == "company"
        assert entity.verified is True
        assert entity.attributes["industry"] == "科技"

    def test_entity_info_defaults(self):
        """测试实体信息默认值"""
        entity = EntityInfo(
            name="最小实体",
            type="person",
        )
        
        assert entity.description == ""
        assert entity.attributes == {}
        assert entity.verified is False
        assert entity.sources == []


class TestStructuredOutputAgent:
    """Structured Output Agent 单元测试"""

    def test_agent_creation(self):
        """测试 Agent 创建（模拟数据库和模型）"""
        from agno.agent import Agent
        from app.agents.structured_output.agent import create_structured_output_agent
        from agno.models.openai import OpenAIChat
        
        # Mock 数据库
        mock_db = MagicMock()
        
        # Mock 整个 Agent 类避免模型验证
        with patch("app.agents.structured_output.agent.Agent") as MockAgent:
            mock_agent_instance = MagicMock()
            MockAgent.return_value = mock_agent_instance
            
            with patch("app.agents.structured_output.agent.create_model") as mock_create_model:
                mock_create_model.return_value = "gpt-4o"  # 返回字符串模型 ID
                
                # 电影 Agent
                create_structured_output_agent(mock_db, output_type="movie")
                call_kwargs = MockAgent.call_args[1]
                assert call_kwargs["id"] == "structured-movie"
                assert call_kwargs["output_schema"] == MovieScript
                
                # 研究报告 Agent
                create_structured_output_agent(mock_db, output_type="research")
                call_kwargs = MockAgent.call_args[1]
                assert call_kwargs["id"] == "structured-research"
                assert call_kwargs["output_schema"] == ResearchReport
                
                # 实体信息 Agent
                create_structured_output_agent(mock_db, output_type="entity")
                call_kwargs = MockAgent.call_args[1]
                assert call_kwargs["id"] == "structured-entity"
                assert call_kwargs["output_schema"] == EntityInfo


class TestMCPTools:
    """MCP 工具测试"""

    def test_mcp_server_config(self):
        """测试 MCP 服务器配置"""
        from app.tools.config import MCPServerConfig
        
        # HTTP 模式
        http_config = MCPServerConfig(
            name="docs",
            url="https://docs.agno.com/mcp",
        )
        assert http_config.url == "https://docs.agno.com/mcp"
        assert http_config.command is None
        
        # Stdio 模式
        stdio_config = MCPServerConfig(
            name="git",
            command="uvx mcp-server-git",
        )
        assert stdio_config.command == "uvx mcp-server-git"
        assert stdio_config.url is None
        
        # 带前缀
        prefixed_config = MCPServerConfig(
            name="dev",
            url="https://example.com/mcp",
            tool_name_prefix="dev",
        )
        assert prefixed_config.tool_name_prefix == "dev"

    def test_create_mcp_tools_empty(self):
        """测试空配置"""
        from app.tools.mcp.client import create_mcp_tools
        
        tools = create_mcp_tools(None)
        assert tools == []
        
        tools = create_mcp_tools([])
        assert tools == []


class TestToolRegistry:
    """工具注册表测试"""

    def test_registry_singleton(self):
        """测试注册表单例"""
        from app.tools.registry import get_tool_registry
        
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        
        assert registry1 is registry2

    def test_framework_tool_registration(self):
        """测试框架工具注册"""
        from app.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        
        def sample_tool(query: str) -> str:
            """Sample tool for testing"""
            return f"Result: {query}"
        
        registry.register_framework_tool(sample_tool)
        
        tools = registry.list_framework_tools()
        assert "sample_tool" in tools
        
        tool_info = registry.get_tool_info("sample_tool")
        assert tool_info is not None
        assert tool_info.name == "sample_tool"


class TestHooksRegistry:
    """Hooks 注册表测试"""

    def test_hooks_config(self):
        """测试 Hooks 配置"""
        from app.hooks.config import HooksConfig, HookConfig
        
        def sample_hook(output):
            return output
        
        config = HooksConfig(
            enable_content_safety=True,
            content_safety_level="strict",
            post_hooks=[
                HookConfig(
                    name="sample",
                    hook_fn=sample_hook,
                    level="project",
                ),
            ],
        )
        
        assert config.enable_content_safety is True
        assert config.content_safety_level == "strict"
        assert len(config.post_hooks) == 1

    def test_content_safety_hook(self):
        """测试内容安全护栏"""
        from app.hooks.builtin.content_safety import content_safety_check
        
        # 安全内容应通过
        content_safety_check("This is a normal message", level="strict")
        
        # 不安全内容应抛出异常
        with pytest.raises(ValueError, match="blocked pattern"):
            content_safety_check("murder weapon attack", level="strict")


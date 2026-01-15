"""
Agent 集成测试

运行测试:
    pytest tests/test_agents.py -v

注意: 这些测试需要数据库连接，运行前确保:
1. PostgreSQL 已启动: docker compose up -d agno-postgres
2. 环境变量已配置: OPENROUTER_API_KEY
"""

import pytest

# 经典模板测试已迁移到 tests/agents/, tests/teams/, tests/workflows/
# 此文件保留通用工具和 Hooks 测试


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
        from app.hooks.config import HookConfig, HooksConfig

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

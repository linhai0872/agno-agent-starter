"""
ToolRegistry 冲突检测测试

测试 ToolRegistry 的同层级冲突检测和跨层级覆盖行为。
"""

import pytest

from app.core.registry import RegistryConflictError, RegistryLevel
from app.tools import ToolRegistry, get_tool_registry


def dummy_tool_a(x: str) -> str:
    """Dummy tool A"""
    return f"a: {x}"


def dummy_tool_b(x: str) -> str:
    """Dummy tool B"""
    return f"b: {x}"


def dummy_tool_c(x: str) -> str:
    """Dummy tool C"""
    return f"c: {x}"


class TestToolRegistryConflictDetection:
    """ToolRegistry 冲突检测测试"""

    def test_framework_same_name_raises_conflict(self):
        # Arrange
        registry = ToolRegistry()
        registry.register_framework_tool(dummy_tool_a, name="shared_tool")

        # Act & Assert
        with pytest.raises(RegistryConflictError) as exc_info:
            registry.register_framework_tool(dummy_tool_b, name="shared_tool")

        assert exc_info.value.name == "shared_tool"
        assert exc_info.value.level == RegistryLevel.FRAMEWORK

    def test_different_names_no_conflict(self):
        # Arrange
        registry = ToolRegistry()

        # Act
        registry.register_framework_tool(dummy_tool_a, name="tool_a")
        registry.register_framework_tool(dummy_tool_b, name="tool_b")

        # Assert
        tools = registry.list_framework_tools()
        assert "tool_a" in tools
        assert "tool_b" in tools


class TestToolRegistryCrossLevelOverride:
    """跨层级覆盖测试"""

    def test_agent_tool_overrides_framework(self):
        # Arrange
        registry = ToolRegistry()
        registry.register_framework_tool(dummy_tool_a, name="web_search")

        # Act
        tools = registry.get_tools_for_agent(
            agent_tools=[dummy_tool_b],  # dummy_tool_b.__name__ != "web_search"
        )

        # Assert - 两个工具都存在
        assert len(tools) == 2

    def test_agent_same_name_overrides_framework(self):
        # Arrange
        registry = ToolRegistry()
        registry.register_framework_tool(dummy_tool_a, name="my_tool")

        # 创建同名 agent 工具
        def my_tool(x: str) -> str:
            return f"agent: {x}"

        # Act
        tools = registry.get_tools_for_agent(agent_tools=[my_tool])

        # Assert - Agent 级覆盖 Framework 级
        assert len(tools) == 1
        assert tools[0]("test") == "agent: test"


class TestToolRegistryIntegration:
    """集成测试"""

    def test_get_tool_registry_singleton_pattern(self):
        # 注意：这会影响全局状态，需要小心
        # 这只是验证单例模式工作正常
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()

        assert registry1 is registry2

    def test_list_framework_tools_returns_correct_list(self):
        # Arrange
        registry = ToolRegistry()
        registry.register_framework_tool(dummy_tool_a, name="alpha")
        registry.register_framework_tool(dummy_tool_b, name="beta")

        # Act
        tools = registry.list_framework_tools()

        # Assert
        assert sorted(tools) == ["alpha", "beta"]

    def test_get_tool_info(self):
        # Arrange
        registry = ToolRegistry()
        registry.register_framework_tool(dummy_tool_a, name="info_test")

        # Act
        info = registry.get_tool_info("info_test")
        missing = registry.get_tool_info("nonexistent")

        # Assert
        assert info is not None
        assert info.name == "info_test"
        assert info.func is dummy_tool_a
        assert missing is None

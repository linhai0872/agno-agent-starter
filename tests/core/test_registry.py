"""
PriorityRegistry 基类测试

测试 PriorityRegistry 抽象基类的共享功能：
- 冲突检测机制
- 辅助方法
"""

import pytest

from app.core.registry import (
    PriorityRegistry,
    RegistryConflictError,
    RegistryLevel,
)


class DummyItem:
    """测试用简单项目类型"""

    def __init__(self, value: str):
        self.value = value


class ConcreteRegistry(PriorityRegistry[DummyItem]):
    """测试用具体注册表实现"""

    def register_framework_item(self, name: str, item: DummyItem) -> None:
        self._check_conflict(self._framework_items, name, RegistryLevel.FRAMEWORK)
        self._framework_items[name] = item

    def register_project_item(
        self, project_id: str, name: str, item: DummyItem
    ) -> None:
        if project_id not in self._project_items:
            self._project_items[project_id] = {}

        self._check_conflict(
            self._project_items[project_id], name, RegistryLevel.PROJECT
        )
        self._project_items[project_id][name] = item


class TestRegistryConflictError:
    """RegistryConflictError 异常测试"""

    def test_error_message_contains_name_and_level(self):
        # Arrange
        name = "my_item"
        level = RegistryLevel.FRAMEWORK

        # Act
        error = RegistryConflictError(name, level)

        # Assert
        assert "my_item" in str(error)
        assert "framework" in str(error)
        assert error.name == name
        assert error.level == level


class TestPriorityRegistryConflictDetection:
    """冲突检测测试"""

    def test_framework_conflict_raises_error(self):
        # Arrange
        registry = ConcreteRegistry()
        registry.register_framework_item("item_a", DummyItem("first"))

        # Act & Assert
        with pytest.raises(RegistryConflictError) as exc_info:
            registry.register_framework_item("item_a", DummyItem("second"))

        assert exc_info.value.name == "item_a"
        assert exc_info.value.level == RegistryLevel.FRAMEWORK

    def test_project_conflict_raises_error(self):
        # Arrange
        registry = ConcreteRegistry()
        registry.register_project_item("proj1", "item_b", DummyItem("first"))

        # Act & Assert
        with pytest.raises(RegistryConflictError) as exc_info:
            registry.register_project_item("proj1", "item_b", DummyItem("second"))

        assert exc_info.value.name == "item_b"
        assert exc_info.value.level == RegistryLevel.PROJECT

    def test_different_names_no_conflict(self):
        # Arrange
        registry = ConcreteRegistry()

        # Act
        registry.register_framework_item("item_a", DummyItem("a"))
        registry.register_framework_item("item_b", DummyItem("b"))

        # Assert
        assert len(registry.list_framework_items()) == 2

    def test_same_name_different_projects_no_conflict(self):
        # Arrange
        registry = ConcreteRegistry()

        # Act
        registry.register_project_item("proj1", "shared_name", DummyItem("a"))
        registry.register_project_item("proj2", "shared_name", DummyItem("b"))

        # Assert
        assert len(registry.list_project_ids()) == 2


class TestPriorityRegistryHelperMethods:
    """辅助方法测试"""

    def test_list_framework_items(self):
        # Arrange
        registry = ConcreteRegistry()
        registry.register_framework_item("item_x", DummyItem("x"))
        registry.register_framework_item("item_y", DummyItem("y"))

        # Act
        items = registry.list_framework_items()

        # Assert
        assert sorted(items) == ["item_x", "item_y"]

    def test_list_project_ids(self):
        # Arrange
        registry = ConcreteRegistry()
        registry.register_project_item("proj_alpha", "a", DummyItem("a"))
        registry.register_project_item("proj_beta", "b", DummyItem("b"))

        # Act
        project_ids = registry.list_project_ids()

        # Assert
        assert sorted(project_ids) == ["proj_alpha", "proj_beta"]

    def test_get_framework_item(self):
        # Arrange
        registry = ConcreteRegistry()
        registry.register_framework_item("my_item", DummyItem("value"))

        # Act
        item = registry.get_framework_item("my_item")
        missing = registry.get_framework_item("nonexistent")

        # Assert
        assert item is not None
        assert item.value == "value"
        assert missing is None

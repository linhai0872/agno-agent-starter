"""
优先级注册表抽象基类

实现三层优先级系统的共享逻辑：
1. Framework 级：框架内置项目（最低优先级）
2. Project 级：项目专属项目
3. Agent 级：单个 Agent 的项目（最高优先级）

子类负责实现具体的 get_for_agent() 方法。
"""

from abc import ABC
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class RegistryLevel(Enum):
    """注册表优先级层"""

    FRAMEWORK = "framework"
    PROJECT = "project"
    AGENT = "agent"


class RegistryConflictError(Exception):
    """
    同层级注册冲突异常

    当尝试在同一层级注册已存在的同名项目时抛出。
    跨层级同名允许（这是优先级覆盖的设计意图）。
    """

    def __init__(self, name: str, level: RegistryLevel):
        super().__init__(f"'{name}' already registered at {level.value} level")
        self.name = name
        self.level = level


class PriorityRegistry(ABC, Generic[T]):
    """
    三层优先级注册表抽象基类

    提供共享的存储结构和冲突检测逻辑。
    子类需实现具体的 get_for_agent() 方法。

    使用示例（子类）：

    ```python
    class MyRegistry(PriorityRegistry[MyItem]):
        def register_framework_item(self, name: str, item: MyItem) -> None:
            self._check_conflict(self._framework_items, name, RegistryLevel.FRAMEWORK)
            self._framework_items[name] = item
    ```
    """

    def __init__(self):
        self._framework_items: dict[str, T] = {}
        self._project_items: dict[str, dict[str, T]] = {}

    def _check_conflict(
        self,
        registry: dict[str, T],
        name: str,
        level: RegistryLevel,
    ) -> None:
        """
        检测同层级冲突

        Args:
            registry: 目标注册字典
            name: 待注册项名称
            level: 注册层级

        Raises:
            RegistryConflictError: 如果同层级已存在同名项目
        """
        if name in registry:
            raise RegistryConflictError(name, level)

    def list_framework_items(self) -> list[str]:
        """列出所有 Framework 级项目名称"""
        return list(self._framework_items.keys())

    def list_project_ids(self) -> list[str]:
        """列出所有已注册的 Project ID"""
        return list(self._project_items.keys())

    def get_framework_item(self, name: str) -> T | None:
        """获取指定 Framework 级项目"""
        return self._framework_items.get(name)

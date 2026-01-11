"""
HooksRegistry 冲突检测测试

测试 HooksRegistry 的同层级冲突检测。
"""

import pytest

from app.core.registry import RegistryConflictError, RegistryLevel
from app.hooks import HookConfig, HooksConfig, HooksRegistry


def dummy_hook_a(output):
    """Dummy hook A"""
    return output


def dummy_hook_b(output):
    """Dummy hook B"""
    return output


def dummy_hook_c(output):
    """Dummy hook C"""
    return output


class TestHooksRegistryConflictDetection:
    """HooksRegistry 冲突检测测试"""

    def test_framework_pre_hook_conflict_raises_error(self):
        # Arrange
        registry = HooksRegistry()
        registry.register_framework_hooks(
            HooksConfig(
                pre_hooks=[
                    HookConfig(name="my_hook", hook_fn=dummy_hook_a, hook_type="pre")
                ]
            )
        )

        # Act & Assert
        with pytest.raises(RegistryConflictError) as exc_info:
            registry.register_framework_hooks(
                HooksConfig(
                    pre_hooks=[
                        HookConfig(name="my_hook", hook_fn=dummy_hook_b, hook_type="pre")
                    ]
                )
            )

        assert exc_info.value.name == "my_hook"
        assert exc_info.value.level == RegistryLevel.FRAMEWORK

    def test_framework_post_hook_conflict_raises_error(self):
        # Arrange
        registry = HooksRegistry()
        registry.register_framework_hooks(
            HooksConfig(
                post_hooks=[
                    HookConfig(name="validator", hook_fn=dummy_hook_a, hook_type="post")
                ]
            )
        )

        # Act & Assert
        with pytest.raises(RegistryConflictError) as exc_info:
            registry.register_framework_hooks(
                HooksConfig(
                    post_hooks=[
                        HookConfig(name="validator", hook_fn=dummy_hook_b, hook_type="post")
                    ]
                )
            )

        assert exc_info.value.name == "validator"
        assert exc_info.value.level == RegistryLevel.FRAMEWORK

    def test_project_hook_conflict_raises_error(self):
        # Arrange
        registry = HooksRegistry()
        registry.register_project_hooks(
            "proj1",
            HooksConfig(
                pre_hooks=[
                    HookConfig(name="checker", hook_fn=dummy_hook_a, hook_type="pre")
                ]
            ),
        )

        # Act & Assert
        with pytest.raises(RegistryConflictError) as exc_info:
            registry.register_project_hooks(
                "proj1",
                HooksConfig(
                    pre_hooks=[
                        HookConfig(name="checker", hook_fn=dummy_hook_b, hook_type="pre")
                    ]
                ),
            )

        assert exc_info.value.name == "checker"
        assert exc_info.value.level == RegistryLevel.PROJECT

    def test_same_name_different_projects_no_conflict(self):
        # Arrange
        registry = HooksRegistry()

        # Act
        registry.register_project_hooks(
            "proj1",
            HooksConfig(
                pre_hooks=[
                    HookConfig(name="shared", hook_fn=dummy_hook_a, hook_type="pre")
                ]
            ),
        )
        registry.register_project_hooks(
            "proj2",
            HooksConfig(
                pre_hooks=[
                    HookConfig(name="shared", hook_fn=dummy_hook_b, hook_type="pre")
                ]
            ),
        )

        # Assert
        assert len(registry.list_project_ids()) == 2

    def test_different_names_no_conflict(self):
        # Arrange
        registry = HooksRegistry()

        # Act
        registry.register_framework_hooks(
            HooksConfig(
                pre_hooks=[
                    HookConfig(name="hook_a", hook_fn=dummy_hook_a, hook_type="pre"),
                    HookConfig(name="hook_b", hook_fn=dummy_hook_b, hook_type="pre"),
                ]
            )
        )

        # Assert
        hooks = registry.list_framework_hooks()
        assert "hook_a" in hooks
        assert "hook_b" in hooks


class TestHooksRegistryHelperMethods:
    """辅助方法测试"""

    def test_list_framework_hooks(self):
        # Arrange
        registry = HooksRegistry()
        registry.register_framework_hooks(
            HooksConfig(
                post_hooks=[
                    HookConfig(name="alpha", hook_fn=dummy_hook_a, hook_type="post"),
                    HookConfig(name="beta", hook_fn=dummy_hook_b, hook_type="post"),
                ]
            )
        )

        # Act
        hooks = registry.list_framework_hooks()

        # Assert
        assert sorted(hooks) == ["alpha", "beta"]

    def test_get_hook_info(self):
        # Arrange
        registry = HooksRegistry()
        registry.register_framework_hooks(
            HooksConfig(
                post_hooks=[
                    HookConfig(name="info_test", hook_fn=dummy_hook_a, hook_type="post")
                ]
            )
        )

        # Act
        info = registry.get_hook_info("info_test")
        missing = registry.get_hook_info("nonexistent")

        # Assert
        assert info is not None
        assert info.name == "info_test"
        assert info.hook_fn is dummy_hook_a
        assert missing is None

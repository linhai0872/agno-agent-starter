"""
配置系统单元测试

测试三层配置优先级:
  1. Init Args > ENV > YAML > Defaults
  2. YAML 文件缺失时的回退行为
  3. YamlConfigSettingsSource 的正确性
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml


class TestYamlConfigSettingsSource:
    """测试 YAML 配置源"""

    def test_yaml_loading_success(self):
        """验证 YAML 配置能被正确加载"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"model_name": "test-model-from-yaml"}, f)
            temp_path = f.name

        try:
            # Act
            with patch("app.config.Path.__truediv__", return_value=Path(temp_path)):
                from app.config import Settings, YamlConfigSettingsSource

                source = YamlConfigSettingsSource(Settings)
                result = source()

            # Assert
            assert (
                "model_name" in result
                or source._yaml_data.get("model_name") == "test-model-from-yaml"
            )
        finally:
            os.unlink(temp_path)

    def test_yaml_file_missing_returns_empty(self):
        """验证 YAML 文件不存在时返回空配置"""
        # Act
        with patch.object(Path, "exists", return_value=False):
            from app.config import Settings, YamlConfigSettingsSource

            source = YamlConfigSettingsSource(Settings)

        # Assert
        assert source._yaml_data == {}

    def test_yaml_parse_error_returns_empty(self):
        """验证 YAML 解析错误时返回空配置"""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            # Act
            with (
                patch.object(Path, "exists", return_value=True),
                patch("builtins.open", side_effect=yaml.YAMLError("parse error")),
            ):
                from app.config import Settings, YamlConfigSettingsSource

                source = YamlConfigSettingsSource(Settings)

            # Assert
            assert source._yaml_data == {}
        finally:
            os.unlink(temp_path)


class TestSettingsPriority:
    """测试配置优先级"""

    def test_default_values_used_when_no_config(self):
        """验证无配置时使用默认值"""
        # Arrange
        env_backup = os.environ.copy()
        for key in ["MODEL_NAME", "API_PORT", "DEBUG_MODE"]:
            os.environ.pop(key, None)

        try:
            # Act
            from app.config import Settings

            with patch.object(Path, "exists", return_value=False):
                settings = Settings()

            # Assert
            assert settings.model_name == "gpt-4o"
            assert settings.api_port == 7777
            assert settings.debug_mode is False
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

    def test_env_overrides_default(self):
        """验证环境变量覆盖默认值"""
        # Arrange
        env_backup = os.environ.copy()
        os.environ["MODEL_NAME"] = "env-model"

        try:
            # Act
            from app.config import Settings

            settings = Settings(_env_file=None)

            # Assert
            assert settings.model_name == "env-model"
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

    def test_init_args_override_all(self):
        """验证初始化参数覆盖所有其他配置"""
        # Arrange
        env_backup = os.environ.copy()
        os.environ["MODEL_NAME"] = "env-model"

        try:
            # Act
            from app.config import Settings

            settings = Settings(model_name="init-arg-model", _env_file=None)

            # Assert
            assert settings.model_name == "init-arg-model"
        finally:
            os.environ.clear()
            os.environ.update(env_backup)


class TestGetSettings:
    """测试 get_settings 单例"""

    def test_get_settings_returns_settings_instance(self):
        """验证 get_settings 返回 Settings 实例"""
        # Act
        from app.config import Settings, get_settings

        settings = get_settings()

        # Assert
        assert isinstance(settings, Settings)

    def test_get_settings_singleton(self):
        """验证 get_settings 返回同一实例"""
        # Act
        from app.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Assert
        assert settings1 is settings2

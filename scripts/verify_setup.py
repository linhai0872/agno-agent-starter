#!/usr/bin/env python3
"""
环境验证脚本 - 检查开发环境是否正确配置

检查项:
1. Python 版本 >= 3.11
2. 必需环境变量 (API Keys)
3. 数据库连接
4. 核心依赖已安装
5. Docker 可用
6. 端口 7777 未被占用

前置条件:
    pip install -r requirements.txt

使用方式:
    python scripts/verify_setup.py
"""

import os
import socket
import subprocess
import sys
from pathlib import Path


def check_python_version() -> tuple[bool, str]:
    version = sys.version_info
    if version >= (3, 11):
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"需要 Python >= 3.11，当前: {version.major}.{version.minor}"


def check_env_variables() -> tuple[bool, str]:
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return False, ".env 文件不存在，请复制 .env.example 并配置"

    api_keys = [
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
    ]

    found_keys = [k for k in api_keys if os.getenv(k)]
    if found_keys:
        return True, f"Found: {', '.join(found_keys)}"

    from dotenv import load_dotenv

    load_dotenv(env_file)
    found_keys = [k for k in api_keys if os.getenv(k)]

    if found_keys:
        return True, f"Found: {', '.join(found_keys)}"
    return False, "需要至少一个 API Key: OPENROUTER_API_KEY, OPENAI_API_KEY, 或 GOOGLE_API_KEY"


def check_database() -> tuple[bool, str]:
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")

    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=agno-postgres", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "Up" in result.stdout:
            return True, "PostgreSQL 容器运行中"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        import psycopg

        conn_str = database_url.replace("postgresql+psycopg://", "postgresql://")
        with psycopg.connect(conn_str, connect_timeout=3):
            return True, "数据库连接成功"
    except ImportError:
        return False, "psycopg 未安装，无法验证数据库连接"
    except Exception as e:
        return False, f"数据库连接失败: {e}"


def check_dependencies() -> tuple[bool, str]:
    required = ["agno", "fastapi", "pydantic", "pydantic_settings", "yaml"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        return False, f"缺失依赖: {', '.join(missing)}，运行: pip install -r requirements.txt"
    return True, f"已安装: {', '.join(required)}"


def check_docker() -> tuple[bool, str]:
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "Docker 命令执行失败"
    except FileNotFoundError:
        return False, "Docker 未安装，请安装 Docker Desktop"
    except subprocess.TimeoutExpired:
        return False, "Docker 命令超时"


def check_port_available() -> tuple[bool, str]:
    port = 7777
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(("127.0.0.1", port))
        if result == 0:
            try:
                lsof = subprocess.run(
                    ["lsof", "-i", f":{port}"], capture_output=True, text=True, timeout=3
                )
                return False, f"端口 {port} 被占用:\n{lsof.stdout}"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return False, f"端口 {port} 被占用"
        return True, f"端口 {port} 可用"


def main() -> int:
    print("\n🔍 Agno Agent Starter 环境验证\n")
    print("=" * 50)

    checks = [
        ("Python 版本", check_python_version),
        ("环境变量", check_env_variables),
        ("核心依赖", check_dependencies),
        ("Docker", check_docker),
        ("端口 7777", check_port_available),
        ("数据库连接", check_database),
    ]

    all_passed = True
    results = []

    for name, check_fn in checks:
        try:
            passed, message = check_fn()
        except Exception as e:
            passed, message = False, f"检查异常: {e}"

        status = "✅" if passed else "❌"
        results.append((status, name, message, passed))
        if not passed:
            all_passed = False

    for status, name, message, _ in results:
        print(f"{status} {name}")
        print(f"   {message}")
        print()

    print("=" * 50)

    if all_passed:
        print("✅ 环境验证通过！可以开始开发。\n")
        print("开发模式启动:")
        print("  docker compose -f docker-compose.dev.yml up -d")
        print("  uvicorn app.main:app --reload --port 7777")
        return 0
    else:
        print("❌ 环境验证失败，请修复上述问题后重试。\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

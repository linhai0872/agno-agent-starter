#!/usr/bin/env python3
"""
OpenAPI Schema Export Script

从 AgentOS 应用导出 OpenAPI 规格到 api/openapi.json。
使用 Mock 方式绕过数据库连接。

Usage:
    python scripts/export_openapi.py

Note:
    需要运行中的 dev server。脚本从服务器获取 OpenAPI schema。
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None


def fetch_from_server(base_url: str = "http://localhost:7777") -> dict:
    """从运行中的服务器获取 OpenAPI schema"""
    if httpx is None:
        raise RuntimeError("httpx not installed. Run: pip install httpx")

    response = httpx.get(f"{base_url}/openapi.json", timeout=10)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI schema from AgentOS")
    parser.add_argument(
        "--url",
        default="http://localhost:7777",
        help="AgentOS server URL (default: http://localhost:7777)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    output_dir = project_root / "api"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "openapi.json"

    print(f"Fetching OpenAPI schema from {args.url}...")
    try:
        schema = fetch_from_server(args.url)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the dev server is running: docker compose up -d")
        sys.exit(1)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI schema exported to: {output_file}")
    print(f"Endpoints: {len(schema.get('paths', {}))}")


if __name__ == "__main__":
    main()

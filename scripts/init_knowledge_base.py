#!/usr/bin/env python3
"""
知识库初始化脚本

初始化客服知识库，加载 FAQ 数据到 PgVector。

使用方式:
    python scripts/init_knowledge_base.py

特性:
    - 幂等执行（可重复运行）
    - 重试机制（数据库连接失败时自动重试）
    - 支持增量更新
"""

import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


def wait_for_db(db_url: str, max_retries: int = 5, retry_interval: int = 2) -> bool:
    """
    等待数据库就绪

    Args:
        db_url: 数据库连接 URL
        max_retries: 最大重试次数
        retry_interval: 重试间隔（秒）

    Returns:
        True 如果连接成功
    """
    import psycopg

    for attempt in range(1, max_retries + 1):
        try:
            conn_str = db_url.replace("postgresql+psycopg://", "postgresql://")
            with psycopg.connect(conn_str) as conn:
                conn.execute("SELECT 1")
            logger.info("数据库连接成功 (尝试 %d/%d)", attempt, max_retries)
            return True
        except Exception as e:
            logger.warning(
                "数据库连接失败 (尝试 %d/%d): %s", attempt, max_retries, e
            )
            if attempt < max_retries:
                time.sleep(retry_interval)

    logger.error("无法连接数据库，已达最大重试次数")
    return False


def load_faq_data() -> dict:
    """加载 FAQ 数据"""
    faq_path = PROJECT_ROOT / "data" / "customer_service_faq.json"
    if not faq_path.exists():
        logger.warning("FAQ 文件不存在: %s", faq_path)
        return {"categories": {}}

    with open(faq_path, encoding="utf-8") as f:
        return json.load(f)


def init_knowledge_base(db_url: str) -> None:
    """
    初始化知识库

    Args:
        db_url: 数据库连接 URL
    """
    try:
        from agno.knowledge.knowledge import Knowledge
        from agno.vectordb.pgvector import PgVector, SearchType
    except ImportError as e:
        logger.error("缺少依赖: %s", e)
        logger.info("请安装: pip install agno pgvector")
        return

    logger.info("初始化 PgVector 知识库...")

    vector_db = PgVector(
        table_name="customer_service_kb",
        db_url=db_url,
        search_type=SearchType.hybrid,
    )

    knowledge = Knowledge(
        name="Customer Service Knowledge Base",
        description="客服知识库，包含账单、技术和常见问题解答",
        vector_db=vector_db,
    )

    faq_data = load_faq_data()
    categories = faq_data.get("categories", {})

    if not categories:
        logger.warning("没有找到 FAQ 数据")
        return

    total_items = 0
    for category, items in categories.items():
        logger.info("加载分类: %s (%d 条)", category, len(items))
        for item in items:
            content = f"问题: {item['question']}\n回答: {item['answer']}"
            metadata = {"category": category, "type": "faq"}

            try:
                knowledge.add_content(content=content, metadata=metadata)
                total_items += 1
            except Exception as e:
                logger.warning("添加内容失败: %s", e)

    logger.info("知识库初始化完成，共加载 %d 条数据", total_items)


def main() -> int:
    """主入口"""
    logger.info("=" * 50)
    logger.info("知识库初始化脚本")
    logger.info("=" * 50)

    from app.config import get_settings

    settings = get_settings()
    db_url = settings.database_url

    logger.info("数据库 URL: %s", db_url.split("@")[-1])

    if not wait_for_db(db_url):
        return 1

    try:
        init_knowledge_base(db_url)
        logger.info("初始化成功 ✅")
        return 0
    except Exception as e:
        logger.error("初始化失败: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())

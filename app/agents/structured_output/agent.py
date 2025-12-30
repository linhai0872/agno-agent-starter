"""
Structured Output Agent

展示 Agno 官方推荐的结构化输出最佳实践。

支持两种模式（官方推荐）：
1. output_schema + use_json_mode=True: JSON 模式，兼容性更好
2. output_schema only: 增强模式，验证更严格

使用 Pydantic BaseModel 定义输出 Schema，Agent 返回的 response.content
会是对应的 Pydantic 对象，可直接访问属性。
"""

from typing import Optional, Type

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from pydantic import BaseModel

from app.agents.structured_output.prompts import (
    ENTITY_INFO_PROMPT,
    MOVIE_SCRIPT_PROMPT,
    RESEARCH_REPORT_PROMPT,
)
from app.agents.structured_output.schemas import (
    EntityInfo,
    MovieScript,
    ResearchReport,
)
from app.models import ModelConfig, ReasoningConfig, create_model


# ============== Agent 模型配置 ==============

AGENT_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.3,
    max_tokens=8192,
    reasoning=ReasoningConfig(enabled=False),
)


def create_structured_output_agent(
    db: PostgresDb,
    output_type: str = "movie",
) -> Agent:
    """
    创建结构化输出 Agent
    
    展示官方推荐的 Structured Output 模式：
    - 使用 Pydantic BaseModel 定义 output_schema
    - 使用 use_json_mode=True 确保输出格式
    - response.content 直接返回 Pydantic 对象
    
    Args:
        db: PostgreSQL 数据库连接
        output_type: 输出类型
            - "movie": 电影剧本 (MovieScript)
            - "research": 研究报告 (ResearchReport)
            - "entity": 实体信息 (EntityInfo)
        
    Returns:
        配置好的 Agent 实例
        
    使用示例:
    
    ```python
    # 创建电影剧本 Agent
    agent = create_structured_output_agent(db, output_type="movie")
    
    # 调用 Agent
    response = agent.run("东京")
    
    # response.content 是 MovieScript 对象
    print(response.content.name)       # 电影标题
    print(response.content.genre)      # 电影类型
    print(response.content.storyline)  # 剧情概要
    ```
    """
    # 根据类型选择 Schema 和 Prompt
    schema: Type[BaseModel]
    prompt: str
    agent_id: str
    description: str
    
    if output_type == "research":
        schema = ResearchReport
        prompt = RESEARCH_REPORT_PROMPT
        agent_id = "structured-research"
        description = "研究报告生成 Agent，输出结构化的研究分析报告"
    elif output_type == "entity":
        schema = EntityInfo
        prompt = ENTITY_INFO_PROMPT
        agent_id = "structured-entity"
        description = "实体信息提取 Agent，输出结构化的实体信息"
    else:
        # 默认电影剧本
        schema = MovieScript
        prompt = MOVIE_SCRIPT_PROMPT
        agent_id = "structured-movie"
        description = "电影剧本生成 Agent，输出结构化的电影概念"
    
    model = create_model(AGENT_MODEL_CONFIG)
    
    agent = Agent(
        id=agent_id,
        name=f"Structured Output Agent ({output_type})",
        description=description,
        model=model,
        db=db,
        instructions=prompt,
        # ========== 核心配置：结构化输出 ==========
        output_schema=schema,     # Pydantic Model
        use_json_mode=True,       # 官方推荐：启用 JSON 模式
        # ==========================================
        markdown=False,  # 结构化输出不需要 Markdown
        add_history_to_context=True,
        num_history_runs=3,
    )
    
    return agent


# ============== 便捷工厂函数 ==============

def create_movie_script_agent(db: PostgresDb) -> Agent:
    """创建电影剧本 Agent"""
    return create_structured_output_agent(db, output_type="movie")


def create_research_report_agent(db: PostgresDb) -> Agent:
    """创建研究报告 Agent"""
    return create_structured_output_agent(db, output_type="research")


def create_entity_info_agent(db: PostgresDb) -> Agent:
    """创建实体信息 Agent"""
    return create_structured_output_agent(db, output_type="entity")


# ============== 使用示例 ==============
#
# API 调用方式（通过 AgentOS）：
#
# POST /agents/structured-movie/runs
# {
#   "message": "东京"
# }
#
# 响应示例：
# {
#   "content": {
#     "name": "霓虹迷途",
#     "genre": "科幻惊悚",
#     "setting": "2089年的东京新宿，霓虹灯与全息投影交织...",
#     "characters": [
#       "林晓 - 神秘的记忆商人",
#       "田中美咲 - 寻找失忆丈夫的妻子",
#       ...
#     ],
#     "storyline": "在记忆可以买卖的未来东京...",
#     "ending": "..."
#   }
# }
#
# Python 调用示例：
#
# ```python
# from app.agents.structured_output import create_movie_script_agent
#
# agent = create_movie_script_agent(db)
# response = agent.run("东京")
#
# # response.content 是 MovieScript 对象
# movie = response.content
# print(f"电影名称: {movie.name}")
# print(f"电影类型: {movie.genre}")
# print(f"剧情: {movie.storyline}")
# ```


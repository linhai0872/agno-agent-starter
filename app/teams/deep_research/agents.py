"""
Deep Research Team 成员 Agents

包含四个专业化 Agent：Planner、Researcher、Analyst、Writer
"""

import logging

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools

from app.config import get_settings
from app.hooks.builtin.tool_call_guard import create_tool_call_guard

logger = logging.getLogger(__name__)


def create_planner_agent() -> Agent:
    """
    创建规划 Agent

    职责：将研究主题分解为可搜索的子问题
    """
    settings = get_settings()

    return Agent(
        name="Research Planner",
        role="将研究主题分解为具体的子问题和搜索策略",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        instructions="""\
你是研究规划专家。你的任务是：
1. 理解用户的研究主题
2. 将主题分解为 3-5 个可搜索的子问题
3. 为每个子问题设计搜索关键词

输出格式：
- 子问题1: [问题描述] | 搜索关键词: [关键词1, 关键词2]
- 子问题2: ...

不要执行搜索，只做规划。
""",
        add_session_state_to_context=True,
        enable_agentic_state=True,
        markdown=True,
    )


def create_researcher_agent() -> Agent:
    """
    创建搜索 Agent

    职责：执行搜索，收集原始信息
    特性：带有 ToolCallGuard 防止过度搜索
    """
    settings = get_settings()
    guard = create_tool_call_guard(
        max_calls_per_tool=10,
        max_retries_per_tool=3,
        max_total_calls=30,
    )

    return Agent(
        name="Researcher",
        role="执行搜索收集信息",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        instructions="""\
你是信息收集专家。你的任务是：
1. 根据 Planner 给出的子问题执行搜索
2. 从搜索结果中提取关键信息
3. 记录来源 URL 以供引用

注意：
- 每个子问题搜索 2-3 次即可，不要过度搜索
- 如果搜索失败或限流，基于已有信息继续
- 将发现的信息添加到 session_state["findings"]
""",
        tools=[DuckDuckGoTools()],
        tool_hooks=[guard],
        add_session_state_to_context=True,
        enable_agentic_state=True,
        markdown=True,
    )


def create_analyst_agent() -> Agent:
    """
    创建分析 Agent

    职责：分析和综合搜索结果
    """
    settings = get_settings()

    return Agent(
        name="Analyst",
        role="分析和综合研究发现",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        instructions="""\
你是研究分析专家。你的任务是：
1. 审查 Researcher 收集的信息
2. 识别关键模式和趋势
3. 评估信息的可信度
4. 发现信息缺口和矛盾

输出：
- 核心发现总结
- 可信度评估
- 需要进一步研究的领域
""",
        add_session_state_to_context=True,
        enable_agentic_state=True,
        markdown=True,
    )


def create_writer_agent() -> Agent:
    """
    创建撰写 Agent

    职责：生成最终研究报告
    """
    settings = get_settings()

    return Agent(
        name="Writer",
        role="撰写研究报告",
        model=OpenRouter(
            id=settings.model_name,
            api_key=settings.openrouter_api_key,
        ),
        instructions="""\
你是研究报告撰写专家。你的任务是：
1. 基于分析结果撰写结构化报告
2. 确保逻辑清晰、论证有力
3. 包含具体的行动建议

报告结构：
1. 执行摘要（200-300字）
2. 主要发现（3-5条）
3. 建议（1-3条）
4. 局限性（1-3条）
""",
        add_session_state_to_context=True,
        enable_agentic_state=True,
        markdown=True,
    )

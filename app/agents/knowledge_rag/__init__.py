"""
Knowledge RAG Agent

展示如何使用 Agno 的知识库功能实现 RAG（检索增强生成）。
支持两种模式：
1. Agentic RAG: Agent 主动搜索知识库
2. Traditional RAG: 自动将相关知识注入上下文
"""

from app.agents.knowledge_rag.agent import (
    create_knowledge_rag_agent,
    AGENT_MODEL_CONFIG,
    AGENT_KNOWLEDGE_CONFIG,
)

__all__ = [
    "create_knowledge_rag_agent",
    "AGENT_MODEL_CONFIG",
    "AGENT_KNOWLEDGE_CONFIG",
]



"""
Knowledge RAG Agent

展示如何集成 Agno 知识库功能的示例 Agent。
使用 PostgresDb 作为向量存储，支持 Agentic RAG 模式。
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb

from app.config import get_settings
from app.agents.knowledge_rag.prompts import SYSTEM_PROMPT
from app.models import (
    KnowledgeConfig,
    ModelConfig,
    ReasoningConfig,
    create_model,
)


# ============== Agent 模型配置 ==============

AGENT_MODEL_CONFIG = ModelConfig(
    model_id="google/gemini-2.5-flash-preview-09-2025",
    temperature=0.2,
    max_tokens=8192,
    reasoning=ReasoningConfig(enabled=False),
)


# ============== Knowledge 配置 ==============

AGENT_KNOWLEDGE_CONFIG = KnowledgeConfig(
    # 启用知识库
    enabled=True,
    
    # 向量数据库配置
    vector_db_table="knowledge_rag_embeddings",
    search_type="hybrid",
    
    # Embedder 配置
    embedder_model="text-embedding-3-small",
    embedder_provider="openai",
    
    # Reranker 配置（可选）
    enable_reranker=False,
    reranker_model="rerank-v3.5",
    reranker_provider="cohere",
    
    # RAG 模式
    # Agentic RAG: Agent 主动搜索
    search_knowledge=True,
    # Traditional RAG: 自动注入上下文
    add_knowledge_to_context=False,
    
    # 检索配置
    num_results=5,
)


def create_knowledge_rag_agent(db: PostgresDb) -> Agent:
    """
    创建 Knowledge RAG Agent
    
    注意：实际使用时需要配置知识库：
    1. 创建 AgentKnowledge 实例
    2. 加载文档到知识库
    3. 将知识库关联到 Agent
    
    Args:
        db: PostgreSQL 数据库连接
        
    Returns:
        配置好的 Agent 实例
    """
    settings = get_settings()
    
    model = create_model(AGENT_MODEL_CONFIG)
    knowledge_params = AGENT_KNOWLEDGE_CONFIG.to_agent_params()
    
    # 注意：以下是知识库配置的示例代码
    # 实际使用时需要取消注释并配置
    #
    # from agno.embedder.openai import OpenAIEmbedder
    # from agno.knowledge.agent import AgentKnowledge
    # from agno.vectordb.pgvector import PgVector
    #
    # embedder = OpenAIEmbedder(
    #     id="knowledge-embedder",
    #     api_key=settings.openai_api_key,
    #     model=AGENT_KNOWLEDGE_CONFIG.embedder_model,
    # )
    #
    # vector_db = PgVector(
    #     db_url=settings.database_url,
    #     table_name=AGENT_KNOWLEDGE_CONFIG.vector_db_table,
    #     embedder=embedder,
    # )
    #
    # knowledge = AgentKnowledge(
    #     vector_db=vector_db,
    #     num_documents=AGENT_KNOWLEDGE_CONFIG.num_results,
    # )
    
    agent = Agent(
        id="knowledge-rag",
        name="Knowledge RAG Agent",
        description="知识库问答 Agent，支持从文档中检索信息回答问题",
        model=model,
        db=db,
        instructions=SYSTEM_PROMPT,
        # 知识库配置（取消注释以启用）
        # knowledge=knowledge,
        # 知识库参数
        **knowledge_params,
        # 其他配置
        markdown=True,
        add_history_to_context=True,
        num_history_runs=5,
        debug_mode=settings.debug_mode,
    )
    
    return agent


# ============== 知识库使用示例 ==============
#
# 1. 加载文档到知识库:
#
# from agno.document.reader.pdf_reader import PDFReader
#
# reader = PDFReader()
# documents = reader.read("path/to/document.pdf")
# knowledge.load_documents(documents)
#
# 2. 使用 URL 加载:
#
# from agno.document.reader.website_reader import WebsiteReader
#
# reader = WebsiteReader()
# documents = reader.read("https://example.com/docs")
# knowledge.load_documents(documents)
#
# 3. 查询知识库:
#
# results = knowledge.search("如何配置数据库连接?")
# for doc in results:
#     print(doc.content)



# Smart Customer Service Workflow

**类型**: Workflow (步骤化流程)  
**用途**: 智能客服，支持问题分类和知识库检索

## 功能特性

- 🏷️ **智能分类**: Agent 自动分类客户问题
- 🔀 **条件路由**: 根据分类决定处理流程
- 📚 **知识库 RAG**: PgVector 混合搜索
- 📝 **结构化输出**: ServiceResponse Schema

## 工作流程

```
用户问题 → [分类] → [条件路由] → [知识库检索] → [响应生成] → 回复
                         ↓
              billing/technical/general → 查询知识库
              other → 直接响应
```

## 使用示例

```python
from agno.db.postgres import PostgresDb
from app.workflows.customer_service import create_customer_service_workflow

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")
workflow = create_customer_service_workflow(db)

response = workflow.run("如何查看我的账单？")
print(response.content)  # ServiceResponse 对象
```

## 问题分类

| 类别        | 描述             | 示例               |
| ----------- | ---------------- | ------------------ |
| `billing`   | 账单、付款、订阅 | "如何查看账单？"   |
| `technical` | 技术问题、故障   | "产品无法启动"     |
| `general`   | 一般咨询         | "产品有哪些功能？" |
| `other`     | 其他问题         | "你们公司在哪？"   |

## 输出格式

```json
{
  "answer": "您好！查看账单请访问...",
  "category": "billing",
  "confidence": 0.95,
  "sources": ["billing-faq.md"],
  "requires_human": false
}
```

## 知识库配置

### 初始化知识库

运行 `docker compose up` 时自动执行初始化脚本：

```bash
python scripts/init_knowledge_base.py
```

### 知识库表结构

```sql
-- 自动创建 (由 PgVector 管理)
CREATE TABLE customer_service_kb (
    id SERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536)
);
```

### 添加知识内容

```python
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector, SearchType

kb = Knowledge(
    vector_db=PgVector(
        table_name="customer_service_kb",
        db_url="...",
        search_type=SearchType.hybrid,
    ),
)

# 添加 PDF 文档
kb.add_content(url="https://example.com/faq.pdf")

# 添加文本
kb.add_content(content="Q: 如何重置密码？\nA: 请访问...")
```

## 技术要点

### 条件路由

```python
def route_to_knowledge_base(step_input: StepInput) -> bool:
    """决定是否查询知识库"""
    category = step_input.previous_step_content.category
    return category in ["billing", "technical", "general"]

workflow = Workflow(
    steps=[
        classify_step,
        Condition(
            evaluator=route_to_knowledge_base,
            steps=[rag_step],  # 条件为 True 时执行
        ),
        respond_step,
    ],
)
```

### 混合搜索

```python
vector_db=PgVector(
    table_name="customer_service_kb",
    search_type=SearchType.hybrid,  # 向量 + 关键词
)
```

## 扩展指南

### 添加新的问题类别

1. 在 `schemas.py` 中扩展 `QueryCategory` 枚举
2. 更新分类 Agent 的 instructions
3. 调整路由逻辑

### 接入其他知识库

可替换 PgVector 为其他向量数据库：

```python
from agno.vectordb.milvus import Milvus

vector_db = Milvus(collection_name="customer_service")
```

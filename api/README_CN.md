# API 参考

本目录包含 Agno Agent Starter 的 OpenAPI 规格文件。

## 交互式文档

服务运行时，可通过以下链接访问交互式 API 文档：

- **Swagger UI**: http://localhost:7777/docs
- **ReDoc**: http://localhost:7777/redoc

## OpenAPI 规格

[`openapi.json`](./openapi.json) 文件包含 OpenAPI 3.1 格式的完整 API 规格。

### AI 工具读取

```python
# 编程方式读取规格
import json
with open("api/openapi.json") as f:
    spec = json.load(f)
```

### 核心端点

| 资源      | 端点                                 | 说明          |
| --------- | ------------------------------------ | ------------- |
| Agents    | `POST /agents/{agent_id}/runs`       | 运行 Agent    |
| Teams     | `POST /teams/{team_id}/runs`         | 运行 Team     |
| Workflows | `POST /workflows/{workflow_id}/runs` | 运行 Workflow |
| Sessions  | `GET /sessions`                      | 会话列表      |
| Health    | `GET /health`                        | 健康检查      |

### 导出最新规格

```bash
python scripts/export_openapi.py
```

## 相关链接

- [Agno 文档](https://docs.agno.com)
- [AgentOS 概述](https://docs.agno.com/agent-os/overview)

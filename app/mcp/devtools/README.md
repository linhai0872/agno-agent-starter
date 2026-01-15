# Agno DevTools MCP Server

提供 MCP 工具，让 AI Agent 能够测试和调试 Agno 应用（Agent、Team、Workflow）。

## 零配置设计

MCP DevTools **自动复用项目已有的环境变量**，无需额外配置：

| 配置项       | 自动派生自     | 默认值                                         |
| ------------ | -------------- | ---------------------------------------------- |
| API URL      | `API_PORT`     | `http://127.0.0.1:7777`                        |
| Database URL | `DATABASE_URL` | `postgresql+psycopg://ai:ai@localhost:5532/ai` |

只需确保项目 `.env` 中已配置好这些变量（`docker-compose up` 后即可），MCP DevTools 即可开箱即用。

## 提供的工具

| 工具            | 功能             | 使用场景                       |
| --------------- | ---------------- | ------------------------------ |
| `agno_list`     | 列出已注册的应用 | 发现可用的 agent/team/workflow |
| `agno_run`      | 运行应用（异步） | 执行测试，立即返回 session_id  |
| `agno_trace`    | 查询执行结果     | 轮询直到 COMPLETED/FAILED      |
| `agno_sessions` | 查看历史记录     | 定位之前的执行记录             |

## IDE 配置

### Cursor

在项目根目录创建或编辑 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "agno-devtools": {
      "command": "python",
      "args": ["-m", "app.mcp.devtools.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### Claude Code (CLI)

在项目根目录创建或编辑 `.mcp.json`：

```json
{
  "mcpServers": {
    "agno-devtools": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "app.mcp.devtools.server"],
      "cwd": "/absolute/path/to/agno-agent-starter",
      "env": {
        "PYTHONPATH": "/absolute/path/to/agno-agent-starter"
      }
    }
  }
}
```

> **注意**: Claude Code 需要**绝对路径**，将 `/absolute/path/to/agno-agent-starter` 替换为你的实际路径。

### Antigravity (Gemini Code)

编辑 `~/.gemini/antigravity/mcp_config.json`：

```json
{
  "mcpServers": {
    "agno-devtools": {
      "command": "python",
      "args": ["-m", "app.mcp.devtools.server"],
      "cwd": "/absolute/path/to/agno-agent-starter",
      "env": {
        "PYTHONPATH": "/absolute/path/to/agno-agent-starter"
      }
    }
  }
}
```

### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 或 `%APPDATA%\Claude\claude_desktop_config.json` (Windows)：

```json
{
  "mcpServers": {
    "agno-devtools": {
      "command": "python",
      "args": ["-m", "app.mcp.devtools.server"],
      "cwd": "/absolute/path/to/agno-agent-starter",
      "env": {
        "PYTHONPATH": "/absolute/path/to/agno-agent-starter"
      }
    }
  }
}
```

## 使用示例

### 1. 发现应用

```
调用 agno_list 工具
```

返回：
```json
{
  "agents": [{"id": "github-analyzer", "name": "GitHub Analyzer"}],
  "teams": [{"id": "deep-research-team", "name": "Deep Research Team"}],
  "workflows": [{"id": "customer-service", "name": "Customer Service"}]
}
```

### 2. 运行工作流

```
调用 agno_run：
  app_type: "workflow"
  app_id: "customer-service"
  message: '{"query": "How to reset password?"}'
```

返回 `session_id`。

### 3. 查询结果

```
调用 agno_trace：
  session_id: "返回的session_id"
  detail_level: "summary"
```

轮询直到 `status` 为 `COMPLETED` 或 `FAILED`。

## 与 CLI 的关系

| 维度         | CLI (`./scripts/agno`)           | MCP DevTools   |
| ------------ | -------------------------------- | -------------- |
| **使用者**   | 开发者终端                       | AI Agent       |
| **交互方式** | 人工执行                         | Agent 自动调用 |
| **输出格式** | 彩色终端友好                     | 结构化 JSON    |
| **功能覆盖** | 更丰富 (health, errors, --usage) | 核心 4 个      |

两者互补，不冲突。

## 高级配置

如需覆盖自动派生的配置，可设置环境变量：

```bash
# 在 .env 中
MCP_DEVTOOLS_API_URL=http://custom-host:8080
MCP_DEVTOOLS_DB_URL=postgresql+psycopg://user:pass@host:5432/db
```

## 故障排除

### MCP Server 无法启动

1. 确保已安装依赖：`pip install fastmcp psycopg-pool`
2. 确保在项目根目录运行
3. 检查 `PYTHONPATH` 是否正确设置

### 无法连接 API

1. 确保 Agno 服务已启动：`docker-compose up -d`
2. 验证健康检查：`curl http://127.0.0.1:7777/health`

### 无法连接数据库

1. 确保 PostgreSQL 容器运行中：`docker ps | grep agno-postgres`
2. 检查 `DATABASE_URL` 配置

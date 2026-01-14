# Agno CLI - Agent-Native 测试与调试工具

一个统一的命令行工具，用于运行和调试 Agno 框架中的 Agent、Team、Workflow 应用。

## 快速开始

```bash
# 列出所有已注册的应用
./scripts/agno list

# 运行一个 workflow
./scripts/agno run workflow customer-service '{"query":"How to reset password?"}'

# 查看执行 Trace
./scripts/agno trace <session_id>
```

## 命令参考

### `agno list [type]` - 列出应用

```bash
./scripts/agno list              # 列出所有类型
./scripts/agno list agent        # 只列出 Agents
./scripts/agno list team         # 只列出 Teams
./scripts/agno list workflow     # 只列出 Workflows
```

### `agno run <type> <id> '<message>'` - 运行应用

```bash
# Workflow
./scripts/agno run workflow customer-service '{"query":"How can I help you?"}'

# Agent
./scripts/agno run agent github-analyzer '{"repo":"owner/repo"}'

# Team
./scripts/agno run team deep-research-team '{"query":"AI trends"}'
```

### `agno trace <session_id> [mode]` - 查询 Trace

```bash
./scripts/agno trace abc123              # 摘要 (默认)
./scripts/agno trace abc123 --metrics    # 执行指标
./scripts/agno trace abc123 --steps      # 节点结果
./scripts/agno trace abc123 --content    # 最终输出
./scripts/agno trace abc123 --usage      # 工具成本统计 (FinOps)
./scripts/agno trace abc123 --full       # 完整数据
```

### `agno sessions [type] [id] [limit]` - 查看历史

```bash
./scripts/agno sessions                              # 所有类型，最近 5 条
./scripts/agno sessions workflow customer-service 10  # 特定 workflow，最近 10 条
```

### `agno errors [--limit N]` - 查看失败的 Runs

```bash
./scripts/agno errors              # 最近 10 条失败
./scripts/agno errors --limit 5    # 最近 5 条失败
```

### `agno health` - 系统健康检查

```bash
./scripts/agno health    # 检查 API、数据库、成功率、最近失败
```

## 环境变量

| 变量                | 默认值        | 说明              |
| ------------------- | ------------- | ----------------- |
| `AGNO_PORT`         | 7777          | API 端口          |
| `AGNO_DB_CONTAINER` | agno-postgres | PostgreSQL 容器名 |
| `AGNO_DB_USER`      | ai            | 数据库用户        |
| `AGNO_DB_NAME`      | ai            | 数据库名          |

## 为什么需要这个工具？

在 AI-native 开发中，AI Agent 经常需要：
1. 运行工作流进行测试
2. 查看执行结果和 Trace 日志
3. 分析执行指标和节点状态

传统方式需要多个复杂的 curl + jq 命令组合，容易出错。

`agno` CLI 将这些操作封装成简单的子命令，让 Agent 一次就能正确执行。

## AI Agent 使用指南

如果你是 AI Agent，使用 `/test-agno-workflow` slash command 可以获取标准化的测试流程指引。

或者直接使用以下命令：

```bash
# Step 1: 确认应用存在
./scripts/agno list

# Step 2: 运行并获取 Trace
./scripts/agno run workflow <id> '<json>'

# Step 3: 如需更多细节
./scripts/agno trace <session_id> --steps
```

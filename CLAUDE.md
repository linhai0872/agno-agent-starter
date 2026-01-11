# Claude Code 开发规范

本文档为 Claude Code 专用配置。完整开发规范请参阅 **[AGENTS.md](AGENTS.md)**。

---

## 引用主规范

所有开发规范、命名约定、模型配置、常见任务等内容，请参考：

→ **[AGENTS.md](AGENTS.md)**

---

## Claude 专用说明

### 文件编辑

- 编辑代码时遵循 AGENTS.md 中的命名规则和代码风格
- 新建 Agent/Team/Workflow 后，务必在 `__init__.py` 注册

### 命令执行

- 开发服务器假设已运行，不要执行 `docker compose up` 或 `uvicorn` 启动命令
- 可安全执行：`ruff check .`、`mypy app/`、`pytest tests/`

### 项目上下文

如需了解项目架构和实现规则，请参阅：
- [项目上下文](_bmad-output/project-context.md)
- [架构文档](_bmad-output/planning-artifacts/architecture.md)

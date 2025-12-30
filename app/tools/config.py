"""
工具配置数据类

定义工具的配置、覆盖和 MCP 集成相关的数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional


class _UnsetType:
    """特殊标记类型，用于区分 None 和未设置"""
    
    def __repr__(self) -> str:
        return "UNSET"
    
    def __bool__(self) -> bool:
        return False


# 特殊标记，用于区分 None（显式设为空）和未设置（保持原值）
UNSET = _UnsetType()


@dataclass
class ToolConfig:
    """
    单个工具配置
    
    用于配置工具的元数据和行为。
    """
    
    # 工具名称
    name: str = ""
    
    # 工具描述
    description: str = ""
    
    # 优先级层: framework / project / agent
    level: Literal["framework", "project", "agent"] = "agent"
    
    # 是否异步执行
    async_execution: bool = True
    
    # 是否需要用户确认
    requires_confirmation: bool = False
    
    # 是否在工具调用后停止 Agent
    stop_after_tool_call: bool = False
    
    # 是否显示工具结果
    show_result: bool = True
    
    # 缓存配置
    cache_results: bool = False
    cache_dir: str = "/tmp/agno_cache"
    cache_ttl: int = 3600  # 秒


@dataclass
class ParamOverride:
    """
    参数覆盖配置
    
    用于在继承模式下修改工具参数的属性。
    """
    
    # 参数描述覆盖（适配业务场景）
    description: Optional[str] = None
    
    # 默认值覆盖
    # 使用 UNSET 表示不覆盖，None 表示显式设为空
    default: Any = UNSET
    
    # 是否隐藏此参数（对 Agent 不可见）
    hidden: bool = False


@dataclass
class ParamConfig:
    """
    新增参数配置
    
    用于在继承模式下为工具添加新参数。
    """
    
    # 参数名称
    name: str
    
    # 参数类型
    type: type = str
    
    # 参数描述
    description: str = ""
    
    # 默认值
    default: Any = None
    
    # 是否必需
    required: bool = False


@dataclass
class ToolOverride:
    """
    工具覆盖配置 - 支持继承/包装/替换三种模式
    
    使用示例:
    
    ```python
    # 1. 继承模式：修改描述和参数
    override = ToolOverride(
        tool_name="company_enrichment",
        mode="inherit",
        description="针对日本市场的公司信息查询",
        param_overrides={
            "domain": ParamOverride(description="日本公司域名"),
        },
        additional_params=[
            ParamConfig(name="country", default="JP"),
        ],
    )
    
    # 2. 包装模式：添加前后处理
    override = ToolOverride(
        tool_name="tavily_search",
        mode="wrap",
        pre_hook=lambda args: {**args, "query": f"[JP] {args['query']}"},
        post_hook=lambda result: log_result(result),
    )
    
    # 3. 替换模式：完全自定义
    override = ToolOverride(
        tool_name="tavily_search",
        mode="replace",
        replacement=my_custom_search,
    )
    ```
    """
    
    # 目标工具名称（要覆盖的框架级工具）
    tool_name: str
    
    # 覆盖模式
    # - inherit: 继承原工具，仅修改指定属性
    # - wrap: 包装原工具，在调用前后添加自定义逻辑
    # - replace: 完全替换原工具实现
    mode: Literal["inherit", "wrap", "replace"] = "inherit"
    
    # ============== inherit 模式配置 ==============
    
    # 工具描述覆盖（适配业务场景）
    description: Optional[str] = None
    
    # 参数级覆盖
    param_overrides: Dict[str, ParamOverride] = field(default_factory=dict)
    
    # 新增参数（扩展原工具）
    additional_params: List[ParamConfig] = field(default_factory=list)
    
    # 隐藏参数列表
    hidden_params: List[str] = field(default_factory=list)
    
    # ============== wrap 模式配置 ==============
    
    # 前置处理函数: (args: Dict) -> Dict
    # 在调用原工具前修改参数
    pre_hook: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    
    # 后置处理函数: (result: Any) -> Any
    # 在调用原工具后处理结果
    post_hook: Optional[Callable[[Any], Any]] = None
    
    # ============== replace 模式配置 ==============
    
    # 替换函数（完全替代原工具）
    replacement: Optional[Callable] = None


@dataclass
class ProjectToolsConfig:
    """
    项目级工具配置
    
    用于在项目级别统一管理工具的覆盖、自定义和禁用。
    
    使用示例:
    
    ```python
    config = ProjectToolsConfig(
        project_id="japan-sales",
        overrides=[
            ToolOverride(
                tool_name="company_enrichment",
                mode="inherit",
                description="日本市场公司查询",
            ),
        ],
        custom_tools=[my_japan_tool],
        disabled_tools=["global_search"],
    )
    ```
    """
    
    # 项目 ID
    project_id: str
    
    # 工具覆盖列表
    overrides: List[ToolOverride] = field(default_factory=list)
    
    # 项目专属工具（不在框架级）
    custom_tools: List[Callable] = field(default_factory=list)
    
    # 禁用的框架工具
    disabled_tools: List[str] = field(default_factory=list)


@dataclass
class MCPServerConfig:
    """
    外部 MCP 服务器配置
    
    用于配置要消费的外部 MCP 服务。
    
    支持两种传输方式（官方最佳实践）：
    - streamable-http: 远程 HTTP 服务器
    - stdio: 本地命令行工具
    
    使用示例:
    
    ```python
    # HTTP 远程服务器
    config = MCPServerConfig(
        name="docs",
        url="https://docs.agno.com/mcp",
    )
    
    # 本地命令行工具
    config = MCPServerConfig(
        name="git",
        command="uvx mcp-server-git",
    )
    
    # 带前缀避免工具名冲突
    config = MCPServerConfig(
        name="dev-docs",
        url="https://docs.agno.com/mcp",
        tool_name_prefix="dev",
    )
    ```
    """
    
    # 服务名称
    name: str
    
    # HTTP 模式: MCP 服务 URL（streamable-http 传输）
    url: Optional[str] = None
    
    # Stdio 模式: 启动 MCP 服务的命令
    command: Optional[str] = None
    
    # 工具名称前缀（避免多服务器工具名冲突）
    # 例如 prefix="dev" 时，tool_name 变为 "dev_tool_name"
    tool_name_prefix: Optional[str] = None
    
    # 要导入的工具名称（None = 全部）
    tool_names: Optional[List[str]] = None
    
    # 连接超时（秒）
    timeout: int = 30


@dataclass
class MCPConfig:
    """
    MCP 协议配置
    
    支持双向 MCP 集成：
    1. 暴露工具: 将本框架工具通过 MCP 协议暴露给外部 Agent
    2. 消费工具: 连接外部 MCP 服务，使用其提供的工具
    """
    
    # ============== 暴露工具（Server 模式） ==============
    
    # 是否启用 MCP Server（暴露工具给外部）
    enable_mcp_server: bool = False
    
    # 要暴露的工具名称（None = 全部框架级工具）
    exposed_tools: Optional[List[str]] = None
    
    # ============== 消费工具（Client 模式） ==============
    
    # 外部 MCP 服务器列表
    mcp_servers: List[MCPServerConfig] = field(default_factory=list)



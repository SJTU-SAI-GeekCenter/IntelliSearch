"""
IntelliSearch 异常类体系（简化版）

提供统一的错误处理机制，基于严重级别进行错误分类。
通过错误码前缀区分不同领域（如 MCP_###, SEC_###, AGT_### 等）。

设计原则：
- 简洁：只有6个严重级别的异常类
- 灵活：通过错误码区分领域
- 可扩展：新增错误类型只需定义错误码即可
- 易用：ErrorCode 对象自动映射错误码到严重级别
"""

from enum import Enum
from typing import Optional, Dict, Any, Set, ClassVar
import re


class ErrorSeverity(Enum):
    """错误严重级别"""

    FATAL = "FATAL"  # 致命错误：立即终止程序
    CRITICAL = "CRITICAL"  # 严重错误：阻断当前操作，需要用户干预
    ERROR = "ERROR"  # 错误：记录错误，返回给调用方
    WARNING = "WARNING"  # 警告：UI警告但不阻止流程
    NOTICE = "NOTICE"  # 通知：需要用户注意但允许执行
    INFO = "INFO"  # 信息：仅记录日志


class IntelliSearchError(Exception):
    """IntelliSearch 异常基类"""

    # 默认错误码（子类可覆盖）
    error_code: str = "UNKNOWN"

    # 默认用户友好的错误消息
    default_message: str = "An unknown error occurred in IntelliSearch"

    # 严重级别（子类必须定义）
    severity: ErrorSeverity = ErrorSeverity.ERROR

    def __init__(
        self,
        error_code: Optional[str] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        recovery_suggestion: Optional[str] = None,
    ) -> None:
        """
        初始化异常

        Args:
            error_code: 错误码（格式：XXX_###，如 MCP_001）
            message: 错误消息（覆盖默认消息）
            context: 上下文信息字典
            cause: 原始异常（用于异常链）
            recovery_suggestion: 恢复建议（可选）
        """
        # 使用传入的错误码或类定义的默认值
        self.error_code = error_code or self.error_code or "UNKNOWN"
        self.message = message or self.default_message
        self.context = context or {}
        self.cause = cause
        self.recovery_suggestion = recovery_suggestion
        super().__init__(self.message)

    def __init_subclass__(cls, **kwargs):
        """在子类创建时验证严重级别"""
        super().__init_subclass__(**kwargs)

        if cls is IntelliSearchError:
            return  # 跳过基类本身

        # 验证子类是否定义了 severity
        if not hasattr(cls, "severity") or not isinstance(cls.severity, ErrorSeverity):
            raise TypeError(
                f"{cls.__name__} 必须定义 severity 属性（ErrorSeverity 类型）"
            )

    def add_context(self, key: str, value: Any) -> "IntelliSearchError":
        """添加上下文信息"""
        self.context[key] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于日志和API响应）"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "recovery_suggestion": self.recovery_suggestion,
        }

    def format_user_message(self) -> str:
        """生成用户友好的格式化消息"""
        msg = f"[{self.error_code}] {self.message}"
        if self.context and self.severity == ErrorSeverity.ERROR:
            details = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg += f"\n详情: {details}"
        if self.recovery_suggestion:
            msg += f"\n💡 建议: {self.recovery_suggestion}"
        return msg

    def format_debug_message(self) -> str:
        """生成包含技术细节的调试消息"""
        msg = f"{self.__class__.__name__} [{self.error_code}]: {self.message}"
        if self.context:
            msg += f"\nContext: {self.context}"
        if self.cause:
            msg += f"\nCaused by: {type(self.cause).__name__}: {self.cause}"
        return msg


# ============ 6个严重级别的异常类 ============


class FatalError(IntelliSearchError):
    """
    致命错误：立即终止程序

    适用场景：
    - 配置文件损坏或缺失
    - 系统初始化失败
    - 无法恢复的系统错误

    错误码示例：CFG_001, SYS_001
    """

    severity = ErrorSeverity.FATAL
    default_message = "A fatal error occurred, program will exit"


class CriticalError(IntelliSearchError):
    """
    严重错误：阻断当前操作，需要用户干预

    适用场景：
    - MCP 连接失败
    - Agent 执行失败
    - 安全验证失败

    错误码示例：MCP_001, AGT_002, SEC_005
    """

    severity = ErrorSeverity.CRITICAL
    default_message = "A critical error occurred, operation blocked"


class Error(IntelliSearchError):
    """
    普通错误：记录错误，返回给调用方

    适用场景：
    - 工具参数错误
    - 工具执行失败
    - 配置验证失败
    - 超时错误

    错误码示例：TOL_002, TOL_003, CFG_002, AGT_003
    """

    severity = ErrorSeverity.ERROR
    default_message = "An error occurred during operation"


class Warning(IntelliSearchError):
    """
    警告：UI警告但不阻止流程

    适用场景：
    - 权限不足
    - 敏感数据泄露风险
    - 工具不可用

    错误码示例：SEC_001, SEC_004, TOL_001, MCP_002
    """

    severity = ErrorSeverity.WARNING
    default_message = "A warning occurred, operation continues"


class Notice(IntelliSearchError):
    """
    通知：需要用户注意但允许执行

    适用场景：
    - 智能体配置问题
    - 必需配置缺失

    错误码示例：AGT_004, CFG_003
    """

    severity = ErrorSeverity.NOTICE
    default_message = "A notice occurred, please review"


class Info(IntelliSearchError):
    """
    信息：仅记录日志

    适用场景：
    - 一般性通知
    - 调试信息

    错误码示例：INF_001, INF_002
    """

    severity = ErrorSeverity.INFO
    default_message = "Informational message"


# ============ 其他异常 ============


class OtherError(Error):
    """
    其他异常（用于包装非 IntelliSearchError 的原生异常）

    当捕获到非 IntelliSearchError 的原生异常时，会自动包装为 OtherError
    """

    error_code = "OTH_001"
    default_message = "An unexpected error occurred"

    @classmethod
    def from_exception(cls, exc: Exception) -> "OtherError":
        """
        从原始异常创建 OtherError

        Args:
            exc: 原始异常

        Returns:
            OtherError 实例，包含原始异常信息
        """
        import traceback

        # 提取异常信息
        exc_type = type(exc).__name__
        exc_msg = str(exc)

        # 自动推断 domain
        domain = cls._infer_domain_from_exception(exc)

        # 生成唯一的错误码（运行时）
        error_code = cls._generate_runtime_error_code()

        # 构建友好的错误消息
        message = f"{exc_type}: {exc_msg}"

        # 构建上下文信息
        context = {
            "original_type": exc_type,
            "original_message": exc_msg,
            "domain": domain,
            "traceback": "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)[-3:]
            ),
        }

        # 如果是标准库异常，添加更多信息
        if hasattr(exc, "__module__"):
            context["module"] = exc.__module__

        # 创建 OtherError 实例并设置错误码
        instance = cls(
            error_code=error_code, message=message, context=context, cause=exc
        )
        return instance

    @staticmethod
    def _infer_domain_from_exception(exc: Exception) -> str:
        """
        从异常堆栈推断 domain

        Args:
            exc: 原始异常

        Returns:
            推断的 domain 字符串
        """
        import traceback

        # 分析堆栈信息
        tb_str = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_text = "".join(tb_str).lower()

        # 根据堆栈中的关键词推断 domain
        if "agent" in tb_text:
            return "AGENT"
        elif "tool" in tb_text:
            return "TOOL"
        elif "server" in tb_text:
            return "SERVER"
        elif "mcp" in tb_text:
            return "MCP"
        elif "security" in tb_text:
            return "SECURITY"
        elif "ui" in tb_text:
            return "UI"
        else:
            return "UNKNOWN"

    @staticmethod
    def _generate_runtime_error_code() -> str:
        """
        生成运行时唯一的错误码

        Returns:
            格式为 OTH_XXX 的错误码
        """
        import time

        timestamp = int(time.time() * 1000) % 1000
        return f"OTH_{timestamp:03d}"


# ============ 便捷工厂函数（可选）============


def create_error(
    severity: ErrorSeverity,
    error_code: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    cause: Optional[Exception] = None,
) -> IntelliSearchError:
    """
    根据严重级别创建异常的便捷函数

    Args:
        severity: 严重级别
        error_code: 错误码（格式：XXX_###）
        message: 错误消息
        context: 上下文信息
        cause: 原始异常

    Returns:
        对应严重级别的异常实例
    """
    error_classes = {
        ErrorSeverity.FATAL: FatalError,
        ErrorSeverity.CRITICAL: CriticalError,
        ErrorSeverity.ERROR: Error,
        ErrorSeverity.WARNING: Warning,
        ErrorSeverity.NOTICE: Notice,
        ErrorSeverity.INFO: Info,
    }

    error_class = error_classes.get(severity, Error)
    return error_class(
        error_code=error_code,
        message=message,
        context=context,
        cause=cause,
    )


# ============ 错误码对象（推荐使用）============


class ErrorCode:
    """
    错误码对象，包含错误码、严重级别、默认消息和恢复建议

    这是推荐的方式，提供了最优雅的错误抛出接口。
    使用示例：
        ErrorCodes.MCP_CONNECTION.raise_error("无法连接")
        ErrorCodes.SEC_PERMISSION_DENIED.raise_error("权限不足")
    """

    # 用于检测重复错误码的类变量
    _registered_codes: ClassVar[Set[str]] = set()

    def __init__(
        self,
        code: str,
        severity: ErrorSeverity,
        default_message: str,
        recovery_suggestion: Optional[str] = None,
    ):
        """
        初始化错误码对象

        Args:
            code: 错误码（格式：XXX_###）
            severity: 严重级别
            default_message: 默认错误消息
            recovery_suggestion: 恢复建议（可选）

        Raises:
            ValueError: 如果错误码格式不正确或重复
        """
        # 验证错误码格式：XXX_###（3个字母 + 下划线 + 3个数字）
        if not re.match(r"^[A-Z]{3}_\d{3}$", code):
            raise ValueError(
                f"错误码格式错误：{code}。正确格式应为 XXX_###（如 MCP_001）"
            )

        # 检查错误码是否重复
        if code in self._registered_codes:
            raise ValueError(f"错误码重复：{code} 已被注册")

        # 注册错误码
        self._registered_codes.add(code)

        self.code = code
        self.severity = severity
        self.default_message = default_message
        self.recovery_suggestion = recovery_suggestion

    def raise_error(
        self,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        recovery_suggestion: Optional[str] = None,
    ) -> None:
        """
        抛出异常，自动使用正确的严重级别

        Args:
            message: 错误消息（可选，使用默认消息）
            context: 上下文信息
            cause: 原始异常
            recovery_suggestion: 恢复建议（可选，默认使用 ErrorCode 的恢复建议）

        Raises:
            对应严重级别的 IntelliSearchError
        """
        error = create_error(
            self.severity,
            self.code,
            message or self.default_message,
            context,
            cause,
        )
        # 设置恢复建议（优先使用传入的，否则使用默认的）
        error.recovery_suggestion = recovery_suggestion or self.recovery_suggestion
        raise error

    def create_error(
        self,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        recovery_suggestion: Optional[str] = None,
    ) -> IntelliSearchError:
        """
        创建异常对象（不抛出）

        Args:
            message: 错误消息（可选，使用默认消息）
            context: 上下文信息
            cause: 原始异常
            recovery_suggestion: 恢复建议（可选，默认使用 ErrorCode 的恢复建议）

        Returns:
            对应严重级别的 IntelliSearchError 对象
        """
        error = create_error(
            self.severity,
            self.code,
            message or self.default_message,
            context,
            cause,
        )
        # 设置恢复建议（优先使用传入的，否则使用默认的）
        error.recovery_suggestion = recovery_suggestion or self.recovery_suggestion
        return error

    def __str__(self) -> str:
        """返回错误码字符串"""
        return self.code

    def __repr__(self) -> str:
        """返回详细表示"""
        return f"ErrorCode(code={self.code}, severity={self.severity.value}, message={self.default_message})"


class ErrorCodes:
    """
    错误码常量定义

    使用 ErrorCode 对象封装了错误码、严重级别和默认消息。

    域名前缀：
    - MCP: MCP 相关错误
    - SEC: 安全相关错误
    - AGT: Agent 相关错误
    - CFG: 配置相关错误
    - TOL: 工具相关错误
    - UIR: UI 相关错误
    - SYS: 系统相关错误
    - OTH: 其他错误

    使用示例：
        # 方式1：最简单，使用默认消息
        ErrorCodes.MCP_CONNECTION.raise_error()

        # 方式2：自定义消息
        ErrorCodes.MCP_CONNECTION.raise_error("无法连接到服务器")

        # 方式3：添加上下文
        ErrorCodes.SEC_PERMISSION_DENIED.raise_error(
            "权限不足",
            context={"file": "/etc/passwd"}
        )

        # 方式4：创建异常对象（不抛出）
        error = ErrorCodes.MCP_CONNECTION.create_error("连接失败")
    """

    # MCP 相关
    MCP_CONNECTION = ErrorCode(
        "MCP_001",
        ErrorSeverity.CRITICAL,
        "MCP 连接失败",
        "请检查 MCP 服务器是否正常运行，确认配置中的服务器地址和端口正确",
    )
    MCP_TOOL_NOT_FOUND = ErrorCode(
        "MCP_002",
        ErrorSeverity.WARNING,
        "MCP 工具未找到",
        "请确认工具名称拼写正确，或检查 MCP 服务器是否已注册该工具",
    )
    MCP_EXECUTION = ErrorCode(
        "MCP_003",
        ErrorSeverity.ERROR,
        "MCP 工具执行失败",
        "请检查工具参数是否正确，或查看详细错误信息了解失败原因",
    )
    MCP_TIMEOUT = ErrorCode(
        "MCP_004",
        ErrorSeverity.ERROR,
        "MCP 执行超时",
        "请稍后重试，或考虑增加超时时间配置",
    )
    MCP_INVALID_RESPONSE = ErrorCode(
        "MCP_005",
        ErrorSeverity.ERROR,
        "MCP 响应格式错误",
        "这可能是 MCP 服务器版本不兼容导致的，请检查服务器版本",
    )

    # 安全相关
    SEC_PERMISSION_DENIED = ErrorCode(
        "SEC_001",
        ErrorSeverity.WARNING,
        "权限不足",
        "请检查您的权限配置，或联系管理员获取所需权限",
    )
    SEC_INVALID_PATH = ErrorCode(
        "SEC_002",
        ErrorSeverity.ERROR,
        "无效路径",
        "请确保路径格式正确，且不包含非法字符或相对路径",
    )
    SEC_DANGEROUS_OPERATION = ErrorCode(
        "SEC_003",
        ErrorSeverity.CRITICAL,
        "危险操作被阻止",
        "该操作可能对系统造成破坏，请确认操作的安全性或联系管理员",
    )
    SEC_SENSITIVE_DATA = ErrorCode(
        "SEC_004",
        ErrorSeverity.WARNING,
        "敏感数据泄露风险",
        "请注意不要在日志或输出中包含敏感信息（如密码、密钥等）",
    )
    SEC_VALIDATION_FAILED = ErrorCode(
        "SEC_005",
        ErrorSeverity.ERROR,
        "安全验证失败",
        "请检查您的操作是否符合安全规则，或联系管理员了解详情",
    )

    # Agent 相关
    AGT_INITIALIZATION = ErrorCode(
        "AGT_001",
        ErrorSeverity.ERROR,
        "Agent 初始化失败",
        "请检查 Agent 配置是否正确，确认必需的配置项都已设置",
    )
    AGT_EXECUTION = ErrorCode(
        "AGT_002",
        ErrorSeverity.CRITICAL,
        "Agent 执行失败",
        "请查看详细错误信息，或尝试重新初始化 Agent",
    )
    AGT_TIMEOUT = ErrorCode(
        "AGT_003",
        ErrorSeverity.ERROR,
        "Agent 响应超时",
        "请稍后重试，或考虑增加超时时间配置",
    )
    AGT_CONFIGURATION = ErrorCode(
        "AGT_004",
        ErrorSeverity.NOTICE,
        "Agent 配置问题",
        "建议检查配置文件，确保所有必需的配置项都已正确设置",
    )

    # 配置相关
    CFG_LOAD = ErrorCode(
        "CFG_001",
        ErrorSeverity.FATAL,
        "配置文件加载失败",
        "请检查配置文件是否存在、格式是否正确、是否可读",
    )
    CFG_VALIDATION = ErrorCode(
        "CFG_002",
        ErrorSeverity.ERROR,
        "配置验证失败",
        "请检查配置文件内容是否符合要求，参考配置示例文件",
    )
    CFG_MISSING = ErrorCode(
        "CFG_003",
        ErrorSeverity.NOTICE,
        "必需配置缺失",
        "请检查配置文件，确保所有必需的配置项都已设置",
    )

    # 工具相关
    TOL_NOT_AVAILABLE = ErrorCode(
        "TOL_001",
        ErrorSeverity.WARNING,
        "工具不可用",
        "该工具当前不可用，请稍后重试或使用替代工具",
    )
    TOL_ARGUMENT = ErrorCode(
        "TOL_002",
        ErrorSeverity.ERROR,
        "工具参数错误",
        "请检查工具参数是否符合要求，参考工具文档",
    )
    TOL_EXECUTION = ErrorCode(
        "TOL_003",
        ErrorSeverity.ERROR,
        "工具执行失败",
        "请查看详细错误信息，或尝试使用不同的参数",
    )

    # UI 相关
    UIR_RENDERING = ErrorCode(
        "UIR_001", ErrorSeverity.ERROR, "UI 渲染失败", "请尝试刷新页面或重新启动应用"
    )
    UIR_USER_INTERACTION = ErrorCode(
        "UIR_002", ErrorSeverity.ERROR, "用户交互错误", "请重试操作，或联系技术支持"
    )
    UIR_EVENT_PIPELINE = ErrorCode(
        "UIR_003",
        ErrorSeverity.ERROR,
        "事件管线错误",
        "请检查事件配置，或重新初始化事件管线",
    )

    # 系统相关
    SYS_INIT = ErrorCode(
        "SYS_001",
        ErrorSeverity.FATAL,
        "系统初始化失败",
        "这可能是严重的系统错误，请检查系统日志或联系技术支持",
    )
    SYS_IO = ErrorCode(
        "SYS_002",
        ErrorSeverity.ERROR,
        "IO 错误",
        "请检查文件或目录是否存在，以及是否有读写权限",
    )
    SYS_NETWORK = ErrorCode(
        "SYS_003", ErrorSeverity.ERROR, "网络错误", "请检查网络连接是否正常，或稍后重试"
    )

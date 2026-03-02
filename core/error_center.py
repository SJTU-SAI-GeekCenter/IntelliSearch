"""
错误中心处理器

统一处理所有异常，基于严重级别做技术决策：
- 是否退出程序
- 是否阻断当前操作
- 是否通知 MCP

设计原则：零业务逻辑，只做技术层面的处理决策。
UI 交互通过事件管线对接，不在此模块处理。
"""

import logging
from typing import Optional, Dict, Any

from .exceptions import IntelliSearchError, OtherError, ErrorSeverity


# 配置日志
logger = logging.getLogger(__name__)


class ErrorDecision:
    """错误处理决策对象"""

    def __init__(
        self,
        should_exit: bool,
        should_block: bool,
        notify_mcp: bool,
        recovery_suggestion: Optional[str] = None,
    ):
        """
        初始化决策对象

        Args:
            should_exit: 是否退出程序
            should_block: 是否阻断当前操作
            notify_mcp: 是否通知 MCP
            recovery_suggestion: 恢复建议（可选）
        """
        self.should_exit = should_exit
        self.should_block = should_block
        self.notify_mcp = notify_mcp
        self.recovery_suggestion = recovery_suggestion

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "should_exit": self.should_exit,
            "should_block": self.should_block,
            "notify_mcp": self.notify_mcp,
            "recovery_suggestion": self.recovery_suggestion,
        }


class ErrorCenter:
    """错误中心处理器"""

    def __init__(self):
        """初始化错误中心"""
        self.error_count = 0  # 错误计数器（用于测试）
        self.last_error: Optional[IntelliSearchError] = None  # 最后的错误（用于测试）

    def handle(self, exception: Exception) -> ErrorDecision:
        """
        处理异常并返回决策对象

        Args:
            exception: 异常对象

        Returns:
            错误决策对象
        """
        # 如果是原生异常，包装为 OtherError
        if not isinstance(exception, IntelliSearchError):
            exception = OtherError.from_exception(exception)

        # 保存最后错误（用于测试）
        self.last_error = exception
        self.error_count += 1

        # 记录日志
        self._log_error(exception)

        # 生成决策
        return self._make_decision(exception)

    def _log_error(self, error: IntelliSearchError) -> None:
        """
        记录错误日志

        Args:
            error: IntelliSearchError 异常对象
        """
        # 获取日志级别
        log_level = self._severity_to_log_level(error.severity)

        # 记录日志
        logger.log(
            log_level,
            f"[{error.error_code}] {error.message}",
            extra={
                "error_code": error.error_code,
                "severity": error.severity.value,
                "context": error.context,
            },
        )

        # 如果有原始异常，记录详细信息
        if error.cause:
            logger.debug(
                f"Caused by: {type(error.cause).__name__}: {error.cause}",
                extra={"original_exception": error.cause},
            )

    def _make_decision(self, error: IntelliSearchError) -> ErrorDecision:
        """
        基于严重级别生成处理决策

        Args:
            error: IntelliSearchError 异常对象

        Returns:
            错误决策对象
        """
        severity = error.severity

        # 处理策略矩阵
        if severity == ErrorSeverity.FATAL:
            # FATAL: 退出程序 + 阻断 + 不通知 MCP
            return ErrorDecision(
                should_exit=True,
                should_block=True,
                notify_mcp=False,
                recovery_suggestion="程序将退出，请检查系统配置或联系管理员",
            )

        elif severity == ErrorSeverity.CRITICAL:
            # CRITICAL: 不退出 + 阻断 + 通知 MCP
            return ErrorDecision(
                should_exit=False,
                should_block=True,
                notify_mcp=True,
                recovery_suggestion="需要用户干预，请检查错误详情",
            )

        elif severity == ErrorSeverity.ERROR:
            # ERROR: 不退出 + 阻断 + 通知 MCP
            return ErrorDecision(
                should_exit=False,
                should_block=True,
                notify_mcp=True,
                recovery_suggestion="操作失败，请重试或检查配置",
            )

        elif severity == ErrorSeverity.WARNING:
            # WARNING: 不退出 + 不阻断 + 通知 MCP
            return ErrorDecision(
                should_exit=False,
                should_block=False,
                notify_mcp=True,
                recovery_suggestion="警告级别，可以继续操作",
            )

        elif severity == ErrorSeverity.NOTICE:
            # NOTICE: 不退出 + 不阻断 + 不通知 MCP
            return ErrorDecision(
                should_exit=False,
                should_block=False,
                notify_mcp=False,
                recovery_suggestion="注意：需要查看此通知",
            )

        else:  # INFO
            # INFO: 不退出 + 不阻断 + 不通知 MCP
            return ErrorDecision(
                should_exit=False,
                should_block=False,
                notify_mcp=False,
                recovery_suggestion=None,
            )

    @staticmethod
    def _severity_to_log_level(severity: ErrorSeverity) -> int:
        """
        将错误严重级别转换为日志级别

        Args:
            severity: 错误严重级别

        Returns:
            日志级别（logging 模块的常量）
        """
        severity_map = {
            ErrorSeverity.FATAL: logging.CRITICAL,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.NOTICE: logging.INFO,
            ErrorSeverity.INFO: logging.INFO,
        }
        return severity_map.get(severity, logging.ERROR)

    def get_error_info(self) -> Optional[IntelliSearchError]:
        """
        获取最后的错误信息（供事件管线使用）

        Returns:
            最后的异常对象，如果没有则为 None
        """
        return self.last_error

    def get_stats(self) -> Dict[str, Any]:
        """
        获取错误统计信息（用于测试）

        Returns:
            统计信息字典
        """
        return {
            "total_errors": self.error_count,
            "last_error_code": self.last_error.error_code if self.last_error else None,
        }

    def reset(self) -> None:
        """重置错误中心（用于测试）"""
        self.error_count = 0
        self.last_error = None


# 全局错误中心实例
error_center = ErrorCenter()


def handle_error(exception: Exception) -> ErrorDecision:
    """
    处理异常的便捷函数

    Args:
        exception: 异常对象

    Returns:
        错误决策对象
    """
    return error_center.handle(exception)


def with_error_handler(func):
    """
    装饰器：自动捕获函数的所有异常并处理

    Args:
        func: 要装饰的函数

    Returns:
        包装后的函数
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 捕获所有异常，交给错误中心处理
            return handle_error(e)

    return wrapper

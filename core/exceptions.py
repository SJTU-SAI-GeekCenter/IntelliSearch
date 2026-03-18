"""
IntelliSearch Exception System

Provides a unified error handling mechanism with error classification based on severity levels.
Distinguishes different domains through error code prefixes (e.g., MCP_###, SEC_###, AGT_###, etc.).

Design Principles:
- Simple: Only 6 exception classes for severity levels
- Flexible: Distinguish domains through error codes
- Extensible: New error types only require defining error codes
- Easy to use: ErrorCode objects automatically map error codes to severity levels
"""

from enum import Enum
from typing import Optional, Dict, Any, Set, ClassVar
import re


class ErrorSeverity(Enum):
    """Error severity level"""

    FATAL = "FATAL"  # Fatal error: immediate program termination
    CRITICAL = "CRITICAL"  # Critical error: blocks current operation, requires user intervention
    ERROR = "ERROR"  # Error: log error, return to caller
    WARNING = "WARNING"  # Warning: UI warning but does not block flow
    NOTICE = "NOTICE"  # Notice: requires user attention but allows execution
    INFO = "INFO"  # Info: log only


class IntelliSearchError(Exception):
    """IntelliSearch exception base class"""

    # Default error code (can be overridden by subclasses)
    error_code: str = "UNKNOWN"

    # Default user-friendly error message
    default_message: str = "An unknown error occurred in IntelliSearch"

    # Severity level (must be defined by subclasses)
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
        Initialize exception

        Args:
            error_code: Error code (format: DOMAIN_TYPE_SPECIFIC, e.g., MCP_CONNECTION_ERROR)
            message: Error message (overrides default message)
            context: Context information dictionary
            cause: Original exception (for exception chaining)
            recovery_suggestion: Recovery suggestion (optional)
        """
        # Use provided error code or class-defined default value
        self.error_code = error_code or self.error_code or "UNKNOWN"
        self.message = message or self.default_message
        self.context = context or {}
        self.cause = cause
        self.recovery_suggestion = recovery_suggestion
        super().__init__(self.message)

    def __init_subclass__(cls, **kwargs):
        """Validate severity level when subclass is created"""
        super().__init_subclass__(**kwargs)

        if cls is IntelliSearchError:
            return  # Skip base class itself

        # Validate that subclass has defined severity
        if not hasattr(cls, "severity") or not isinstance(cls.severity, ErrorSeverity):
            raise TypeError(
                f"{cls.__name__} must define severity attribute (of type ErrorSeverity)"
            )

    def add_context(self, key: str, value: Any) -> "IntelliSearchError":
        """Add context information"""
        self.context[key] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (for logging and API responses)"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "recovery_suggestion": self.recovery_suggestion,
        }

    def format_user_message(self) -> str:
        """Generate user-friendly formatted message"""
        msg = f"[{self.error_code}] {self.message}"
        if self.context and self.severity == ErrorSeverity.ERROR:
            details = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg += f"\nDetails: {details}"
        if self.recovery_suggestion:
            msg += f"\n💡 Suggestion: {self.recovery_suggestion}"
        return msg

    def format_debug_message(self) -> str:
        """Generate debug message with technical details"""
        msg = f"{self.__class__.__name__} [{self.error_code}]: {self.message}"
        if self.context:
            msg += f"\nContext: {self.context}"
        if self.cause:
            msg += f"\nCaused by: {type(self.cause).__name__}: {self.cause}"
        return msg

    def display_exception(self, show_traceback: bool = False) -> None:
        """
        Display exception in UI using DisplayControl

        Args:
            show_traceback: Whether to show detailed traceback information (for debugging)
        """
        try:
            from core.UI.components.display import (
                create_error_display,
                create_fatal_display,
                create_critical_display,
                create_warning_display,
                create_notice_display,
            )
            from core.UI.console import console

            # Map severity to display style
            severity_style_map = {
                ErrorSeverity.FATAL: create_fatal_display,
                ErrorSeverity.CRITICAL: create_critical_display,
                ErrorSeverity.ERROR: create_error_display,
                ErrorSeverity.WARNING: create_warning_display,
                ErrorSeverity.NOTICE: create_notice_display,
                ErrorSeverity.INFO: create_error_display,  # Use error style for info
            }

            # Get appropriate display creator
            display_creator = severity_style_map.get(
                self.severity, create_error_display
            )

            # Build display text
            display_text = f"[{self.error_code}] {self.message}"

            # Add context if available
            if self.context:
                context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
                display_text += f"\n\nContext: {context_str}"

            # Add recovery suggestion if available
            if self.recovery_suggestion:
                display_text += f"\n\n💡 Suggestion: {self.recovery_suggestion}"

            # Add cause if available
            if self.cause:
                display_text += (
                    f"\n\nCaused by: {type(self.cause).__name__}: {self.cause}"
                )

            # Add traceback if requested
            if show_traceback and self.cause and hasattr(self.cause, "__traceback__"):
                import traceback

                tb_text = "".join(
                    traceback.format_exception(
                        type(self.cause), self.cause, self.cause.__traceback__
                    )
                )
                display_text += f"\n\nTraceback:\n{tb_text}"

            # Create and display
            display = display_creator(text=display_text)
            console.print(display)

        except ImportError:
            # Fallback to simple print if UI components are not available
            print(f"[{self.severity.value}] {self.error_code}: {self.message}")
            if self.recovery_suggestion:
                print(f"💡 Suggestion: {self.recovery_suggestion}")
            if self.cause:
                print(f"Caused by: {type(self.cause).__name__}: {self.cause}")
            if show_traceback and self.cause and hasattr(self.cause, "__traceback__"):
                import traceback

                traceback.print_exc()


# ============ 6 Exception Classes for Severity Levels ============


class FatalError(IntelliSearchError):
    """
    Fatal error: immediate program termination

    Use cases:
    - Corrupted or missing configuration files
    - System initialization failure
    - Unrecoverable system errors

    Error code examples: CFG_LOAD_ERROR, SYS_INIT_ERROR
    """

    severity = ErrorSeverity.FATAL
    default_message = "A fatal error occurred, program will exit"


class CriticalError(IntelliSearchError):
    """
    Critical error: blocks current operation, requires user intervention

    Use cases:
    - MCP connection failure
    - Agent execution failure
    - Security validation failure

    Error code examples: MCP_CONNECTION_ERROR, AGT_EXECUTION_ERROR, SEC_VALIDATION_FAILED
    """

    severity = ErrorSeverity.CRITICAL
    default_message = "A critical error occurred, operation blocked"


class Error(IntelliSearchError):
    """
    Normal error: log error, return to caller

    Use cases:
    - Tool argument error
    - Tool execution failure
    - Configuration validation failure
    - Timeout error

    Error code examples: TOL_ARGUMENT_ERROR, TOL_EXECUTION_ERROR, CFG_VALIDATION_ERROR, AGT_TIMEOUT
    """

    severity = ErrorSeverity.ERROR
    default_message = "An error occurred during operation"


class Warning(IntelliSearchError):
    """
    Warning: UI warning but does not block flow

    Use cases:
    - Insufficient permissions
    - Sensitive data disclosure risk
    - Tool not available

    Error code examples: SEC_PERMISSION_DENIED, SEC_SENSITIVE_DATA_RISK, TOL_NOT_AVAILABLE, MCP_TOOL_NOT_FOUND
    """

    severity = ErrorSeverity.WARNING
    default_message = "A warning occurred, operation continues"


class Notice(IntelliSearchError):
    """
    Notice: requires user attention but allows execution

    Use cases:
    - Agent configuration issue
    - Required configuration missing

    Error code examples: AGT_CONFIGURATION_ISSUE, CFG_MISSING_REQUIRED
    """

    severity = ErrorSeverity.NOTICE
    default_message = "A notice occurred, please review"


class Info(IntelliSearchError):
    """
    Info: log only

    Use cases:
    - General notification
    - Debug information

    Error code examples: INF_GENERAL_INFO, INF_DEBUG_INFO
    """

    severity = ErrorSeverity.INFO
    default_message = "Informational message"


# ============ Other Exceptions ============


class OtherError(Error):
    """
    Other exception (for wrapping non-IntelliSearchError native exceptions)

    Non-IntelliSearchError native exceptions are automatically wrapped as OtherError
    """

    error_code = "OTH_UNEXPECTED_ERROR"
    default_message = "An unexpected error occurred"

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        error_code: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
    ) -> "OtherError":
        """
        Create OtherError from original exception

        Args:
            exc: Original exception
            error_code: Custom error code (optional, format: DOMAIN_TYPE_SPECIFIC, e.g., OTH_CUSTOM_ERROR).
                       If not provided, a runtime error code will be generated automatically.
            severity: Custom severity level (optional). If not provided, defaults to ERROR level.
                      Must be one of: FATAL, CRITICAL, ERROR, WARNING, NOTICE, INFO

        Returns:
            OtherError instance containing original exception information
        """
        import traceback

        # Extract exception information
        exc_type = type(exc).__name__
        exc_msg = str(exc)

        # Automatically infer domain
        domain = cls._infer_domain_from_exception(exc)

        # Use provided error code or generate runtime error code
        if error_code:
            # Validate custom error code format: uppercase letters, numbers, and underscores
            # Format: DOMAIN_SPECIFIC (e.g., OTH_CUSTOM_ERROR_1)
            if not re.match(r"^[A-Z][A-Z0-9]*(_[A-Z0-9_]+)*$", error_code):
                raise ValueError(
                    f"Custom error code format error: {error_code}. Correct format should be DOMAIN_SPECIFIC (e.g., OTH_CUSTOM_ERROR or OTH_CUSTOM_ERROR_1)"
                )
            # Ensure error code starts with OTH_ prefix for OtherError
            if not error_code.startswith("OTH_"):
                error_code = f"OTH_{error_code}"
        else:
            # Generate unique error code (runtime)
            error_code = cls._generate_runtime_error_code()

        # Build friendly error message
        message = f"{exc_type}: {exc_msg}"

        # Build context information
        context = {
            "original_type": exc_type,
            "original_message": exc_msg,
            "domain": domain,
            "traceback": "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)[-3:]
            ),
        }

        # Add more information for standard library exceptions
        if hasattr(exc, "__module__"):
            context["module"] = exc.__module__

        # Create OtherError instance
        # Note: We need to create the instance first, then override severity if provided
        instance = cls(
            error_code=error_code, message=message, context=context, cause=exc
        )

        # Override severity if custom severity is provided
        if severity is not None:
            if not isinstance(severity, ErrorSeverity):
                raise ValueError(
                    f"Severity must be an ErrorSeverity enum value, got {type(severity)}"
                )
            instance.severity = severity

        return instance

    @staticmethod
    def _infer_domain_from_exception(exc: Exception) -> str:
        """
        Infer domain from exception stack

        Args:
            exc: Original exception

        Returns:
            Inferred domain string
        """
        import traceback

        # Analyze stack information
        tb_str = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_text = "".join(tb_str).lower()

        # Infer domain based on keywords in stack
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
        Generate runtime unique error code

        Returns:
            Error code in format OTH_RUNTIME_XXX
        """
        import time

        timestamp = int(time.time() * 1000) % 1000
        return f"OTH_RUNTIME_{timestamp:03d}"


# ============ Convenience Factory Functions (Optional) ============


def create_error(
    severity: ErrorSeverity,
    error_code: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    cause: Optional[Exception] = None,
) -> IntelliSearchError:
    """
    Convenience function to create exceptions based on severity level

    Args:
        severity: Severity level
        error_code: Error code (format: DOMAIN_TYPE_SPECIFIC)
        message: Error message
        context: Context information
        cause: Original exception

    Returns:
        Exception instance corresponding to the severity level
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


# ============ Error Code Objects (Recommended) ============


class ErrorCode:
    """
    Error code object containing error code, severity level, default message, and recovery suggestions

    This is the recommended approach, providing the most elegant error throwing interface.
    Usage examples:
        ErrorCodes.MCP_CONNECTION_ERROR.raise_error("Unable to connect")
        ErrorCodes.SEC_PERMISSION_DENIED.raise_error("Permission denied")
    """

    # Class variable for detecting duplicate error codes
    _registered_codes: ClassVar[Set[str]] = set()

    def __init__(
        self,
        code: str,
        severity: ErrorSeverity,
        default_message: str,
        recovery_suggestion: Optional[str] = None,
    ):
        """
        Initialize error code object

        Args:
            code: Error code (format: DOMAIN_TYPE_SPECIFIC)
            severity: Severity level
            default_message: Default error message
            recovery_suggestion: Recovery suggestion (optional)

        Raises:
            ValueError: If error code format is incorrect or duplicate
        """
        # Validate error code format: DOMAIN_TYPE_SPECIFIC (uppercase letters and underscores)
        if not re.match(r"^[A-Z]+_[A-Z_]+$", code):
            raise ValueError(
                f"Error code format error: {code}. Correct format should be DOMAIN_TYPE_SPECIFIC (e.g., MCP_CONNECTION_ERROR)"
            )

        # Check if error code is duplicate
        if code in self._registered_codes:
            raise ValueError(f"Error code duplicate: {code} already registered")

        # Register error code
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
        Raise exception, automatically using correct severity level

        Args:
            message: Error message (optional, uses default message)
            context: Context information
            cause: Original exception
            recovery_suggestion: Recovery suggestion (optional, defaults to ErrorCode's recovery suggestion)

        Raises:
            IntelliSearchError corresponding to the severity level
        """
        error = create_error(
            self.severity,
            self.code,
            message or self.default_message,
            context,
            cause,
        )
        # Set recovery suggestion (prioritize provided value, otherwise use default)
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
        Create exception object (without raising)

        Args:
            message: Error message (optional, uses default message)
            context: Context information
            cause: Original exception
            recovery_suggestion: Recovery suggestion (optional, defaults to ErrorCode's recovery suggestion)

        Returns:
            IntelliSearchError object corresponding to the severity level
        """
        error = create_error(
            self.severity,
            self.code,
            message or self.default_message,
            context,
            cause,
        )
        # Set recovery suggestion (prioritize provided value, otherwise use default)
        error.recovery_suggestion = recovery_suggestion or self.recovery_suggestion
        return error

    def __str__(self) -> str:
        """Return error code string"""
        return self.code

    def __repr__(self) -> str:
        """Return detailed representation"""
        return f"ErrorCode(code={self.code}, severity={self.severity.value}, message={self.default_message})"


class ErrorCodes:
    """
    Error code constant definitions

    Uses ErrorCode objects to encapsulate error codes, severity levels, and default messages.

    Domain prefixes:
    - MCP: MCP related errors
    - SEC: Security related errors
    - AGT: Agent related errors
    - CFG: Configuration related errors
    - TOL: Tool related errors
    - UIR: UI related errors
    - SYS: System related errors
    - OTH: Other errors

    Usage examples:
        # Method 1: Simplest, using default message
        ErrorCodes.MCP_CONNECTION_ERROR.raise_error()

        # Method 2: Custom message
        ErrorCodes.MCP_CONNECTION_ERROR.raise_error("Unable to connect to server")

        # Method 3: Add context
        ErrorCodes.SEC_PERMISSION_DENIED.raise_error(
            "Permission denied",
            context={"file": "/etc/passwd"}
        )

        # Method 4: Create exception object (without raising)
        error = ErrorCodes.MCP_CONNECTION_ERROR.create_error("Connection failed")
    """

    # MCP related
    MCP_CONNECTION_ERROR = ErrorCode(
        "MCP_CONNECTION_ERROR",
        ErrorSeverity.CRITICAL,
        "MCP connection failed",
        "Please check if MCP server is running normally, confirm server address and port in configuration are correct",
    )
    MCP_TOOL_NOT_FOUND = ErrorCode(
        "MCP_TOOL_NOT_FOUND",
        ErrorSeverity.WARNING,
        "MCP tool not found",
        "Please confirm tool name spelling is correct, or check if MCP server has registered this tool",
    )
    MCP_EXECUTION_ERROR = ErrorCode(
        "MCP_EXECUTION_ERROR",
        ErrorSeverity.ERROR,
        "MCP tool execution failed",
        "Please check if tool parameters are correct, or view detailed error information to understand failure reason",
    )
    MCP_TIMEOUT = ErrorCode(
        "MCP_TIMEOUT",
        ErrorSeverity.ERROR,
        "MCP execution timeout",
        "Please try again later, or consider increasing timeout configuration",
    )
    MCP_INVALID_RESPONSE = ErrorCode(
        "MCP_INVALID_RESPONSE",
        ErrorSeverity.ERROR,
        "MCP response format error",
        "This may be caused by MCP server version incompatibility, please check server version",
    )

    # Security related
    SEC_PERMISSION_DENIED = ErrorCode(
        "SEC_PERMISSION_DENIED",
        ErrorSeverity.WARNING,
        "Permission denied",
        "Please check your permission configuration, or contact administrator to obtain required permissions",
    )
    SEC_INVALID_PATH = ErrorCode(
        "SEC_INVALID_PATH",
        ErrorSeverity.ERROR,
        "Invalid path",
        "Please ensure path format is correct and does not contain illegal characters or relative paths",
    )
    SEC_DANGEROUS_OPERATION = ErrorCode(
        "SEC_DANGEROUS_OPERATION",
        ErrorSeverity.CRITICAL,
        "Dangerous operation blocked",
        "This operation may cause damage to the system, please confirm operation safety or contact administrator",
    )
    SEC_SENSITIVE_DATA_RISK = ErrorCode(
        "SEC_SENSITIVE_DATA_RISK",
        ErrorSeverity.WARNING,
        "Sensitive data disclosure risk",
        "Please be careful not to include sensitive information (such as passwords, keys, etc.) in logs or output",
    )
    SEC_VALIDATION_FAILED = ErrorCode(
        "SEC_VALIDATION_FAILED",
        ErrorSeverity.ERROR,
        "Security validation failed",
        "Please check if your operation complies with security rules, or contact administrator for details",
    )

    # Agent related
    AGT_INITIALIZATION_ERROR = ErrorCode(
        "AGT_INITIALIZATION_ERROR",
        ErrorSeverity.ERROR,
        "Agent initialization failed",
        "Please check if Agent configuration is correct, confirm all required configuration items are set",
    )
    AGT_EXECUTION_ERROR = ErrorCode(
        "AGT_EXECUTION_ERROR",
        ErrorSeverity.CRITICAL,
        "Agent execution failed",
        "Please view detailed error information, or try reinitializing Agent",
    )
    AGT_TIMEOUT = ErrorCode(
        "AGT_TIMEOUT",
        ErrorSeverity.ERROR,
        "Agent response timeout",
        "Please try again later, or consider increasing timeout configuration",
    )
    AGT_CONFIGURATION_ISSUE = ErrorCode(
        "AGT_CONFIGURATION_ISSUE",
        ErrorSeverity.NOTICE,
        "Agent configuration issue",
        "Suggest checking configuration file, ensure all required configuration items are set correctly",
    )

    # Configuration related
    CFG_LOAD_ERROR = ErrorCode(
        "CFG_LOAD_ERROR",
        ErrorSeverity.FATAL,
        "Configuration file load failed",
        "Please check if configuration file exists, format is correct, and is readable",
    )
    CFG_VALIDATION_ERROR = ErrorCode(
        "CFG_VALIDATION_ERROR",
        ErrorSeverity.ERROR,
        "Configuration validation failed",
        "Please check if configuration file content meets requirements, refer to configuration example file",
    )
    CFG_MISSING_REQUIRED = ErrorCode(
        "CFG_MISSING_REQUIRED",
        ErrorSeverity.NOTICE,
        "Required configuration missing",
        "Please check configuration file, ensure all required configuration items are set",
    )

    # Tool related
    TOL_NOT_AVAILABLE = ErrorCode(
        "TOL_NOT_AVAILABLE",
        ErrorSeverity.WARNING,
        "Tool not available",
        "This tool is currently unavailable, please try again later or use alternative tool",
    )
    TOL_ARGUMENT_ERROR = ErrorCode(
        "TOL_ARGUMENT_ERROR",
        ErrorSeverity.ERROR,
        "Tool argument error",
        "Please check if tool parameters meet requirements, refer to tool documentation",
    )
    TOL_EXECUTION_ERROR = ErrorCode(
        "TOL_EXECUTION_ERROR",
        ErrorSeverity.ERROR,
        "Tool execution failed",
        "Please view detailed error information, or try using different parameters",
    )

    # UI related
    UIR_RENDERING_ERROR = ErrorCode(
        "UIR_RENDERING_ERROR",
        ErrorSeverity.ERROR,
        "UI rendering failed",
        "Please try refreshing page or restarting application",
    )
    UIR_USER_INTERACTION_ERROR = ErrorCode(
        "UIR_USER_INTERACTION_ERROR",
        ErrorSeverity.ERROR,
        "User interaction error",
        "Please retry operation, or contact technical support",
    )
    UIR_EVENT_PIPELINE_ERROR = ErrorCode(
        "UIR_EVENT_PIPELINE_ERROR",
        ErrorSeverity.ERROR,
        "Event pipeline error",
        "Please check event configuration, or reinitialize event pipeline",
    )

    # System related
    SYS_INIT_ERROR = ErrorCode(
        "SYS_INIT_ERROR",
        ErrorSeverity.FATAL,
        "System initialization failed",
        "This may be a serious system error, please check system logs or contact technical support",
    )
    SYS_IO_ERROR = ErrorCode(
        "SYS_IO_ERROR",
        ErrorSeverity.ERROR,
        "IO error",
        "Please check if file or directory exists, and if read/write permissions are available",
    )
    SYS_NETWORK_ERROR = ErrorCode(
        "SYS_NETWORK_ERROR",
        ErrorSeverity.ERROR,
        "Network error",
        "Please check if network connection is normal, or try again later",
    )


# Automatically register all error codes to error_center
def _register_all_error_codes():
    """Automatically register all error codes defined in ErrorCodes class to error_center"""
    try:
        from core.error_center import register_error_code

        for attr_name in dir(ErrorCodes):
            if attr_name.startswith("_"):
                continue
            attr = getattr(ErrorCodes, attr_name)
            if isinstance(attr, ErrorCode):
                try:
                    register_error_code(
                        code=attr.code,
                        severity=attr.severity,
                        description=attr.default_message,
                        suggestions=attr.recovery_suggestion,
                    )
                except ValueError:
                    pass
    except ImportError:
        pass


_register_all_error_codes()

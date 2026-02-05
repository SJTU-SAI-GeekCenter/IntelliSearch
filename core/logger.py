"""
Global Logger Configuration for IntelliSearch

This module provides a centralized logging system powered by loguru:
- Creates timestamped log files with automatic rotation
- Provides consistent log formatting across all modules
- Supports different log levels for console and file output
- Automatically adds module names and function names to log records
- Defines custom log levels shared across the application
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger as _logger

# Remove default handler
_logger.remove()

# Custom log levels for IntelliSearch
TOOL_CALL_ERROR = 35  # Between ERROR(40) and WARNING(30)
MCP_COMMUNICATION = 25  # Between WARNING(30) and INFO(20)

# Define log level name mapping
LOG_LEVEL_NAMES = {
    TOOL_CALL_ERROR: "TOOL_CALL_ERROR",
    MCP_COMMUNICATION: "MCP_COMMUNICATION",
}


class IntelliSearchLogger:
    """
    Global logger manager for IntelliSearch project using loguru.

    This class manages logging configuration and provides unified logger instances
    across all modules. It creates timestamped log files and ensures consistent
    formatting throughout the application.

    Attributes:
        log_dir: Directory to store log files
        session_start_time: Timestamp of the current session start
        log_file_path: Full path to the current session's log file
        console_level: Logging level for console output
        file_level: Logging level for file output

    Example:
        >>> from core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.error("An error occurred")
    """

    def __init__(
        self,
        log_dir: str = "log",
        console_level: str = "WARNING",
        file_level: str = "INFO",
    ):
        """
        Initialize the global logger manager.

        Args:
            log_dir: Directory to store log files (default: "log")
            console_level: Logging level for console output (default: "WARNING")
            file_level: Logging level for file output (default: "INFO")
        """
        self.log_dir = Path(log_dir)
        self.session_start_time = datetime.now()
        self.log_file_path: Optional[Path] = None
        self.console_level = console_level
        self.file_level = file_level
        self._initialized = False

        # Register custom log levels
        self._register_custom_levels()

    def _create_log_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _register_custom_levels(self) -> None:
        """
        Register custom log levels for IntelliSearch.

        This method defines custom log levels that are shared across all modules:
        - TOOL_CALL_ERROR (35): For tool call errors
        - MCP_COMMUNICATION (25): For MCP protocol communication
        """
        _logger.level(
            LOG_LEVEL_NAMES[TOOL_CALL_ERROR], no=TOOL_CALL_ERROR, color="<fg #FF0000>"
        )
        _logger.level(
            LOG_LEVEL_NAMES[MCP_COMMUNICATION],
            no=MCP_COMMUNICATION,
            color="<fg #00CFFF>",
        )

    def _generate_log_filename(self, name) -> str:
        """
        Generate a timestamped log filename.

        Returns:
            Filename with session start timestamp
        """
        return f"intellisearch_{name}.log"

    def _get_log_format(self, *, with_color: bool = False) -> str:
        """
        Get log format string.

        Args:
            with_color: Whether to include color codes (for console output)

        Returns:
            Log format string
        """
        if with_color:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <16}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        else:
            return (
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <16} | "
                "{name}:{function}:{line} | "
                "{message}"
            )

    def initialize(self, name="main") -> None:
        """
        Initialize the global logging system.

        This method should be called once at application startup.
        It sets up loguru with console and file handlers.
        """
        if self._initialized:
            return

        # Create log directory
        self._create_log_directory()

        # Generate log file path
        log_filename = self._generate_log_filename(name=name)
        self.log_file_path = self.log_dir / log_filename

        # Add console handler with color
        _logger.add(
            sink=lambda msg: print(msg, end=""),
            level=self.console_level,
            format=self._get_log_format(with_color=True),
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

        # Add file handler with rotation and compression
        _logger.add(
            sink=str(self.log_file_path),
            level=self.file_level,
            format=self._get_log_format(with_color=False),
            rotation="10 MB",
            retention="10 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
        )

        self._initialized = True

    def get_logger(self, name: str):
        """
        Get a logger instance with the specified name.

        Args:
            name: Logger name, typically __name__ of the calling module

        Returns:
            Logger instance with configured handlers

        Example:
            >>> logger_manager = IntelliSearchLogger()
            >>> logger_manager.initialize()
            >>> logger = logger_manager.get_logger(__name__)
            >>> logger.info("Module initialized")
        """
        if not self._initialized:
            self.initialize()

        # Bind context with module name
        return _logger.bind(name=name)


# Global logger manager instance
_logger_manager: Optional[IntelliSearchLogger] = None


def setup_logging(
    log_dir: str = "log", console_level: str = "WARNING", file_level: str = "INFO"
) -> IntelliSearchLogger:
    """
    Setup the global logging system.

    This function should be called once at application startup to initialize
    the logging system with custom configuration. Custom log levels are
    automatically registered.

    Args:
        log_dir: Directory to store log files (default: "log")
        console_level: Logging level for console output (default: "WARNING")
                      Available: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
        file_level: Logging level for file output (default: "INFO")

    Returns:
        The initialized IntelliSearchLogger instance

    Example:
        >>> from core.logger import setup_logging
        >>> setup_logging(
        ...     console_level="INFO",
        ...     file_level="DEBUG"
        ... )
    """
    global _logger_manager

    _logger_manager = IntelliSearchLogger(
        log_dir=log_dir, console_level=console_level, file_level=file_level
    )

    _logger_manager.initialize()
    return _logger_manager


def get_logger(name: str):
    """
    Get a logger instance with the specified name.

    This is the main interface for obtaining loggers throughout the application.
    If the logging system hasn't been initialized yet, it will be initialized
    with default settings.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Logger instance with configured handlers

    Example:
        >>> from core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
        >>> logger.debug("Detailed debug information")
        >>> logger.error("An error occurred")
    """
    global _logger_manager

    if _logger_manager is None:
        # Initialize with default settings if not already initialized
        setup_logging()

    return _logger_manager.get_logger(name)


def get_log_file_path() -> Optional[Path]:
    """
    Get the path to the current session's log file.

    Returns:
        Path to the log file, or None if logging hasn't been initialized

    Example:
        >>> from core.logger import get_log_file_path
        >>> log_path = get_log_file_path()
        >>> print(f"Logs are being written to: {log_path}")
    """
    global _logger_manager
    if _logger_manager is None:
        return None
    return _logger_manager.log_file_path


def get_session_start_time() -> Optional[datetime]:
    """
    Get the timestamp of the current logging session start.

    Returns:
        Session start time, or None if logging hasn't been initialized

    Example:
        >>> from core.logger import get_session_start_time
        >>> start_time = get_session_start_time()
        >>> print(f"Session started at: {start_time}")
    """
    global _logger_manager
    if _logger_manager is None:
        return None
    return _logger_manager.session_start_time


__all__ = [
    "IntelliSearchLogger",
    "setup_logging",
    "get_logger",
    "get_log_file_path",
    "get_session_start_time",
    "TOOL_CALL_ERROR",
    "MCP_COMMUNICATION",
]

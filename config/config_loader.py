"""Configuration Loader Module.

This module provides unified management of all IntelliSearch MCP configurations,
supporting YAML file configuration with environment variable overrides.

Classes:
    Config: Global configuration manager for all settings
"""

import yaml
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class Config:
    """
    Global configuration manager for IntelliSearch.

    This class loads configuration from a YAML file and applies environment variables.
    It should be initialized once at application startup with the config file path.

    Example:
        >>> from config.config_loader import Config
        >>> config = Config(config_file_path="config/config.yaml")
        >>> config.load_config()
        >>> model_name = config.get("agent.model_name")
    """

    _instance: Optional["Config"] = None
    _config: Optional[Dict[str, Any]] = None

    def __init__(self, config_file_path: str = "config/config.yaml"):
        """
        Initialize the Config instance.

        Args:
            config_file_path: Path to the YAML configuration file.
                            If not provided, uses default: config/config.yaml
        """
        if Config._instance is not None:
            raise RuntimeError(
                "Config is a singleton. Use Config.get_instance() to get the existing instance."
            )

        self.config_file_path = config_file_path or self._get_default_config_path()
        Config._instance = self

    @staticmethod
    def get_instance() -> "Config":
        """
        Get the singleton Config instance.

        Returns:
            The singleton Config instance

        Raises:
            RuntimeError: If Config has not been initialized
        """
        if Config._instance is None:
            raise RuntimeError(
                "Config has not been initialized. "
                "Call Config(config_file_path='...') first."
            )
        return Config._instance

    @staticmethod
    def _get_default_config_path() -> str:
        """
        Get the default configuration file path.

        Returns:
            Path to config/config.yaml
        """
        return str(Path(__file__).parent / "config.yaml")

    def load_config(self, override: bool = True) -> None:
        """
        Load configuration from YAML file and apply environment variables.

        This method:
        1. Loads the YAML configuration file
        2. Applies the 'env' section to os.environ
        3. Stores the configuration for later access

        Args:
            override: If True, config env vars override existing os.environ.
                     If False, only set vars that don't exist in os.environ.
        """
        config_path = Path(self.config_file_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                Config._config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config file {config_path}: {e}")

        # Apply environment variables from config to os.environ
        self._apply_env_variables(override)

    def _apply_env_variables(self, override: bool = True) -> None:
        """
        Apply environment variables from config to os.environ.

        Args:
            override: If True, config env vars override existing os.environ.
        """
        if Config._config is None:
            return

        env_config: Dict = Config._config.get("env", {})
        if not env_config:
            return

        for key, value in env_config.items():
            if override or key not in os.environ:
                os.environ[key] = str(value)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value through dot-separated path.

        Args:
            key_path: Dot-separated configuration path, e.g. 'agent.model_name'
            default: Default value if path not found

        Returns:
            Configuration value or default value

        Example:
            >>> config.get("agent.model_name")
            "deepseek-chat"
            >>> config.get("mcp.connection.http_timeout", 60)
            60
        """
        if Config._config is None:
            raise RuntimeError(
                "Config not loaded. Call load_config() first."
            )

        keys = key_path.split(".")
        value = Config._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_with_env(
        self, key_path: str, default: Any = None, env_prefix: str = "TOOL_BACKEND"
    ) -> Any:
        """
        Get configuration value with environment variable override support.

        This method checks for environment variables first before falling back to
        the configuration file. Environment variables should be named in format:
        {PREFIX}_{SECTION}_{KEY}, where sections are converted from dot notation.

        Args:
            key_path: Dot-separated configuration path, e.g. 'tool_backend.ipython_backend_port'
            default: Default value if path not found
            env_prefix: Prefix for environment variables (default: "TOOL_BACKEND")

        Returns:
            Configuration value from environment variable or config file

        Example:
            >>> # With env var TOOL_BACKEND_IPYTHON_BACKEND_PORT=8080
            >>> config.get_with_env("tool_backend.ipython_backend_port")
            8080
            >>> # With config: tool_backend.ipython_backend_port: 39256
            >>> config.get_with_env("tool_backend.ipython_backend_port")
            39256
        """
        if Config._config is None:
            raise RuntimeError(
                "Config not loaded. Call load_config() first."
            )

        # *Generate environment variable name, for tool backends
        # Convert: "tool_backend.ipython_backend_port" -> "TOOL_BACKEND_IPYTHON_BACKEND_PORT"
        env_var_name = "_".join(key_path.split(".")).upper()
        full_env_var_name = f"{env_prefix}_{env_var_name}" if env_prefix else env_var_name

        # Check environment variable first
        if full_env_var_name in os.environ:
            env_value = os.environ[full_env_var_name]
            # Try to convert to appropriate type
            if isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    return default
            elif isinstance(default, bool):
                return env_value.lower() in ("true", "1", "yes")
            else:
                return env_value

        # Fall back to config file
        return self.get(key_path, default)

    @property
    def data(self) -> Dict[str, Any]:
        """
        Get the raw configuration dictionary.

        Returns:
            The complete configuration dictionary
        """
        if Config._config is None:
            raise RuntimeError(
                "Config not loaded. Call load_config() first."
            )
        return Config._config

    def reload(self, override: bool = True) -> None:
        """
        Reload configuration from file.

        Args:
            override: If True, config env vars override existing os.environ.
        """
        self.load_config(override=override)


# Convenience functions for backward compatibility and easy access
def get_mcp_timeout() -> int:
    """Get MCP HTTP timeout.

    Returns:
        HTTP timeout in seconds
    """
    config = Config.get_instance()
    return config.get("mcp.connection.http_timeout", 60)


def is_cache_enabled() -> bool:
    """Check if tool cache is enabled.

    Returns:
        True if cache is enabled
    """
    config = Config.get_instance()
    return config.get("cache.enabled", False)


def get_cache_dir() -> str:
    """Get cache directory path.

    Returns:
        Path to cache directory
    """
    config = Config.get_instance()
    return config.get("cache.cache_dir", "./cache")


def get_cache_ttl() -> int:
    """Get cache TTL in hours.

    Returns:
        Cache TTL in hours (0 for permanent)
    """
    config = Config.get_instance()
    return config.get("cache.ttl_hours", 0)


def get_cache_server_whitelist() -> List[str]:
    """Get list of servers whose tools should be cached.

    Returns:
        List of server names to cache (empty list means cache all)
    """
    config = Config.get_instance()
    return config.get("cache.server_whitelist", [])

"""Configuration Loader Module.

This module provides unified management of all IntelliSearch MCP configurations,
supporting YAML file configuration with environment variable overrides.

Classes:
    MCPConfig: Singleton configuration manager for MCP settings
"""

import yaml
import os
from typing import Dict, Any, Union, Optional, List
from pathlib import Path


class MCPConfig:
    """Singleton configuration manager for MCP settings.

    This class manages all MCP configurations using a singleton pattern,
    loading settings from YAML files and allowing environment variable overrides.
    Configuration priority: environment variables > YAML file > default values.

    Attributes:
        _instance: Singleton instance
        _config: Loaded configuration dictionary

    Example:
        >>> config = MCPConfig()
        >>> timeout = config.get_value('mcp.connection.http_timeout')
    """

    _instance: Optional["MCPConfig"] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls) -> "MCPConfig":
        """Create or return the singleton instance.

        Returns:
            The singleton MCPConfig instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the configuration if not already loaded."""
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file with environment overrides.

        Loads configuration in priority order:
        1. Environment variables (highest priority)
        2. YAML configuration file
        3. Default values (lowest priority)
        """
        config_path = Path(__file__).parent / "config.yaml"

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f)
            except Exception as e:
                print(f"Warning: Failed to load config file {config_path}: {e}")
                self._config = self._get_default_config()
        else:
            print(f"Config file {config_path} not found, using default configuration")
            self._config = self._get_default_config()

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration.

        Returns:
            Dictionary containing all default configuration values
        """
        return {
            "mcp": {
                "connection": {
                    "http_timeout": 60,
                    "tool_discovery_timeout": 10,
                    "health_check_timeout": 2,
                    "process_wait_timeout": 5,
                },
                "ports": {
                    "default_port": 3001,
                    "port_search_attempts": 100,
                    "random_port_min": 10000,
                    "random_port_max": 50000,
                },
            },
            "cache": {
                "enabled": False,
                "cache_dir": "./cache",
                "ttl_hours": 0,
                "server_whitelist": [],
            },
        }

    def _apply_env_overrides(self) -> None:
        """Apply environment variable configuration overrides.

        Scans environment variables starting with 'BENCHMARK_' and applies
        them to the configuration. Supports automatic type conversion.
        """
        # Supported format: BENCHMARK_MCP_CONNECTION_HTTP_TIMEOUT=120
        env_mapping = {
            "MCP_CONNECTION_HTTP_TIMEOUT": "mcp.connection.http_timeout",
            "MCP_CONNECTION_TOOL_DISCOVERY_TIMEOUT": "mcp.connection.tool_discovery_timeout",
            "MCP_CONNECTION_HEALTH_CHECK_TIMEOUT": "mcp.connection.health_check_timeout",
            "MCP_CONNECTION_PROCESS_WAIT_TIMEOUT": "mcp.connection.process_wait_timeout",
            "MCP_PORTS_DEFAULT_PORT": "mcp.ports.default_port",
            "MCP_PORTS_PORT_SEARCH_ATTEMPTS": "mcp.ports.port_search_attempts",
            "MCP_PORTS_RANDOM_PORT_MIN": "mcp.ports.random_port_min",
            "MCP_PORTS_RANDOM_PORT_MAX": "mcp.ports.random_port_max",
            "CACHE_ENABLED": "cache.enabled",
            "CACHE_CACHE_DIR": "cache.cache_dir",
            "CACHE_TTL_HOURS": "cache.ttl_hours",
        }

        for key, value in os.environ.items():
            if key.startswith("BENCHMARK_"):
                env_suffix = key[10:]  # Remove BENCHMARK_ prefix

                # Try direct mapping first
                if env_suffix in env_mapping:
                    config_path = env_mapping[env_suffix]
                else:
                    # Fallback to automatic conversion (convert underscores to dots)
                    config_path = env_suffix.lower().replace("_", ".")

                try:
                    # Try to convert to numbers or boolean values
                    converted_value = self._convert_env_value(value)
                    self._set_nested_value(self._config, config_path, converted_value)
                except Exception as e:
                    print(
                        f"Warning: Failed to apply environment override {key}={value}: {e}"
                    )

    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable values to appropriate types.

        Args:
            value: String value from environment variable

        Returns:
            Converted value as int, float, bool, or original string
        """
        # Boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Integer
        try:
            if "." not in value:
                return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String
        return value

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any) -> None:
        """Set value in nested dictionary using dot-separated path.

        Args:
            config: Dictionary to modify
            path: Dot-separated path (e.g., 'mcp.connection.timeout')
            value: Value to set at the path
        """
        keys = path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value through dot-separated path.

        Args:
            key_path: Dot-separated configuration path, e.g. 'mcp.connection.http_timeout'
            default: Default value if path not found

        Returns:
            Configuration value or default value
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value


# Create global configuration instance
config = MCPConfig()


# Convenience functions for actually used configurations
def get_mcp_timeout() -> int:
    """Get MCP HTTP timeout.

    Returns:
        HTTP timeout in seconds
    """
    return config.get("mcp.connection.http_timeout", 60)


def is_cache_enabled() -> bool:
    """Check if tool cache is enabled.

    Returns:
        True if cache is enabled
    """
    return config.get("cache.enabled", False)


def get_cache_dir() -> str:
    """Get cache directory path.

    Returns:
        Path to cache directory
    """
    return config.get("cache.cache_dir", "./cache")


def get_cache_ttl() -> int:
    """Get cache TTL in hours.

    Returns:
        Cache TTL in hours (0 for permanent)
    """
    return config.get("cache.ttl_hours", 0)


def get_cache_server_whitelist() -> List[str]:
    """Get list of servers whose tools should be cached.

    Returns:
        List of server names to cache (empty list means cache all)
    """
    return config.get("cache.server_whitelist", [])

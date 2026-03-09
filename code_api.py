#!/usr/bin/env python3
"""IntelliSearch Code API - OpenAI-compatible backend entry point."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config_loader import Config
from backend.code_backend import CodeBackend
from core.logger import get_logger


def main():
    logger = get_logger(__name__, "code_api")

    try:
        config = Config(config_file_path="config/config.yaml")
        config.load_config()
        code_backend_config = config.get("code_backend", {})

        host = code_backend_config.get("host", "0.0.0.0")
        port = code_backend_config.get("port", 8002)

        agent_config = code_backend_config.get("agent", {})
        api_keys = code_backend_config.get("api_keys", [])
        require_api_key = code_backend_config.get("require_api_key", True)

        if require_api_key and not api_keys:
            logger.warning(
                "API key authentication enabled but no keys configured. "
                "Check 'code_backend.api_keys' in config.yaml"
            )

        full_config = {
            "agent": agent_config,
            "api_keys": api_keys,
            "require_api_key": require_api_key,
        }

        backend = CodeBackend(config=full_config)

        logger.info(f"Starting Code Backend on {host}:{port}")
        backend.run(host=host, port=port, log_level="info")

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

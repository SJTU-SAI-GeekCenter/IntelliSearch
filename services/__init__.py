"""
Services layer for IntelliSearch.

This layer provides backend service abstractions that separate business logic
from UI implementation. Services manage Agent lifecycle and orchestrate
request/response handling while being agnostic to the UI layer.
"""

from services.base_service import BaseService
from services.cli_service import CLIService
from services.web_service import WebService

__all__ = ["BaseService", "CLIService", "WebService"]

"""
Error Center Handler - Simplified Version

Responsible only for error code registration and query, without any decision-making or processing.
"""

from typing import Optional, Dict, Any, List
import re

from .exceptions import ErrorSeverity


# Global error code registry
_ERROR_CODE_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_error_code(
    code: str,
    severity: ErrorSeverity,
    description: str,
    suggestions: Optional[str] = None,
) -> bool:
    """
    Register an error code

    Args:
        code: Error code (format: DOMAIN_TYPE_SPECIFIC)
        severity: Severity level
        description: Error description
        suggestions: Recovery suggestions (optional)

    Returns:
        True if registration successful, False if error code already exists or format is incorrect

    Raises:
        ValueError: If error code format is incorrect
    """
    # Validate error code format: DOMAIN_TYPE_SPECIFIC (uppercase letters and underscores)
    if not re.match(r"^[A-Z]+_[A-Z_]+$", code):
        raise ValueError(
            f"Error code format error: {code}. Correct format should be DOMAIN_TYPE_SPECIFIC (e.g., MCP_CONNECTION_ERROR)"
        )

    # Check if error code already exists
    if code in _ERROR_CODE_REGISTRY:
        return False

    # Register error code
    _ERROR_CODE_REGISTRY[code] = {
        "severity": severity,
        "description": description,
        "suggestions": suggestions,
    }

    return True


def get_error_by_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Get error information by error code

    Args:
        code: Error code

    Returns:
        Error information dictionary, or None if not found
    """
    return _ERROR_CODE_REGISTRY.get(code)


def list_all_codes() -> List[str]:
    """
    Get all registered error codes

    Returns:
        List of error codes
    """
    return sorted(_ERROR_CODE_REGISTRY.keys())


def clear_registry():
    """Clear error code registry (for testing only)"""
    _ERROR_CODE_REGISTRY.clear()

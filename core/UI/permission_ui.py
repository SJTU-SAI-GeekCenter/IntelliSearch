"""
Permission UI handler for file system access requests.

This module provides a user interface for handling permission errors
from the file system security manager, allowing users to grant
temporary or permanent access permissions.

Updated to use the unified UIEngine for cross-platform support.
"""

import re
import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from mcp_server.operate_file.security import (
        SecurityManager,
        AccessScope,
        PermissionRule,
        ImplicitDenyError,
        ExplicitDenyError,
    )

    # Initialize the specific manager for Filesystem
    try:
        security_manager = SecurityManager()
    except Exception as e:
        print(f"CRITICAL: SecurityManager init failed: {e}")
        security_manager = None
except ImportError as e:
    print(f"DEBUG: Failed to import SecurityManager: {e}")
    security_manager = None

    class AccessScope:
        RECURSIVE = 2
        SHALLOW = 1
        DENIED = 0

    class ImplicitDenyError(Exception):
        pass

    class ExplicitDenyError(Exception):
        pass

    class PermissionRule:
        pass


logger = logging.getLogger("ui.permission")


def _get_path_display(path: str) -> str:
    """Truncate long paths for display"""
    path_str = str(path)
    if len(path_str) > 60:
        return "..." + path_str[-57:]
    return path_str


def _extract_target_path(exception: Exception) -> str:
    """
    Extract target path from exception message.

    Priority:
    1. Extract from "Rule <PATH> does not..." pattern (High Confidence)
    2. Extract from "covers <PATH>" pattern
    3. Extract from "path '<PATH>'" pattern
    4. Fallback - find absolute paths, ignoring common python files
    """
    target_path = ""
    error_msg = str(exception)

    # Priority 1: Extract from specific "Rule <PATH> does not..." pattern
    path_match = re.search(r"Rule\s+(.+?)\s+does not", error_msg)

    # Priority 2: Extract from "covers <PATH>" pattern
    if not path_match:
        path_match = re.search(r"covers\s+(.+?)(\.|$)", error_msg)

    # Priority 3: Extract from "path '<PATH>'" pattern
    if not path_match:
        path_match = re.search(r"path '(.+?)'", error_msg)

    # Priority 4: Fallback - Looking for absolute paths
    if not path_match:
        candidates = re.findall(r"([a-zA-Z]:\\[^\s\"'<>\)]+|/[^\s\"'<>\)]+)", error_msg)
        for cand in candidates:
            if (
                "site-packages" not in cand
                and "lib" not in cand
                and "agents" not in cand
                and "process_query_async" not in cand
            ):
                target_path = cand
                break
    else:
        target_path = path_match.group(1).strip(".'\"")

    return target_path if target_path else "Unknown Target"


def handle_permission_error(exception: Exception) -> bool:
    """
    Handle permission errors with user confirmation.

    This function intercepts ImplicitDenyError exceptions and prompts
    the user to grant permission for the requested file system access.

    Args:
        exception: The exception that triggered the permission check

    Returns:
        True if permission was granted, False otherwise

    Raises:
        ExplicitDenyError: If the user explicitly denies access
    """
    from core.UI import UIEngine

    # Extract target path from exception
    target_path = _extract_target_path(exception)

    # Determine error type
    is_explicit_deny = "ExplicitDeny" in str(
        type(exception)
    ) or "ExplicitDenyError" in str(type(exception))

    # Display information panel
    _display_permission_panel(target_path, is_explicit_deny, exception)

    # Get user action choice
    choice = UIEngine.prompt_user_select(
        "Select Action",
        options=[
            "Allow (Recursive)",
            "Temp (30 minutes)",
            "Custom",
            "Deny",
        ],
        default_index=0,
    )

    # User denied access
    if choice == "Deny":
        print("   [red]✖ Access Denied.[/red]\n")
        return False

    # Check if security manager is available
    if not security_manager:
        if __name__ == "__main__":
            print("   [dim]Preview Mode: Output simulated[/dim]\n")
            return True
        print("   [bold red]Error: Security Manager component not loaded.[/bold red]")
        print(
            "   [dim]Ensure 'mcp_server.operate_file.security.SecurityManager' is importable.[/dim]\n"
        )
        return False

    # Configure permission based on user choice
    scope = AccessScope.RECURSIVE
    allow_read = True
    allow_write = True
    allow_create = True
    allow_delete = True
    ttl_seconds = None

    if choice == "Temp (30 minutes)":
        ttl_seconds = 1800
        print("   [yellow]⏱️  Authorized (30 min)[/yellow]")
    elif choice == "Custom":
        return _handle_custom_permission(target_path)

    # Add permission
    try:
        security_manager.add_permission(
            target_path,
            scope=scope,
            allow_read=allow_read,
            allow_write=allow_write,
            allow_create=allow_create,
            allow_delete=allow_delete,
            ttl_seconds=ttl_seconds,
        )
        print(f"   [green]✔ Access Granted.[/green]\n")
        return True
    except Exception as e:
        print(f"   [red]✖ Authorization Failed: {e}[/red]\n")
        return False


def _display_permission_panel(
    target_path: str, is_explicit_deny: bool, exception: Exception
):
    """Display a formatted permission information panel."""
    # Try to use Rich if available, otherwise fall back to basic output
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        from rich import box

        console = Console()

        # Info Grid
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(style="dim bold", width=14)
        grid.add_column(style="bright white")

        # Resource
        grid.add_row("Resource Path", _get_path_display(target_path))

        # Status
        if is_explicit_deny:
            status_text = Text("🚫 Denied", style="red")
        else:
            status_text = Text("🔒 Unauthorized", style="yellow")
        grid.add_row("Current Status", status_text)

        # Intent
        action = (
            "Write/Create"
            if "write" in str(exception).lower() or "create" in str(exception).lower()
            else "Read/Access"
        )
        grid.add_row("Request Action", action)

        # Panel
        panel_content = Table.grid(expand=True)
        panel_content.add_row(grid)

        console.print()
        console.print(
            Panel(
                panel_content,
                title=" [bold red]Security Intercept[/bold red] ",
                border_style="dim white",
                box=box.ROUNDED,
                width=80,
                padding=(1, 2),
            )
        )
    except ImportError:
        # Fallback to basic output
        print("\n" + "=" * 60)
        print("Security Intercept")
        print("=" * 60)
        print(f"Resource Path: {target_path}")
        print(f"Status: {'Denied' if is_explicit_deny else 'Unauthorized'}")
        action = (
            "Write/Create"
            if "write" in str(exception).lower() or "create" in str(exception).lower()
            else "Read/Access"
        )
        print(f"Request Action: {action}")
        print("=" * 60 + "\n")


def _handle_custom_permission(target_path: str) -> bool:
    """
    Handle custom permission configuration.

    Args:
        target_path: The path to configure permissions for

    Returns:
        True if permission was granted, False otherwise
    """
    from core.UI import UIEngine

    print()

    # Recursive or Shallow
    is_recursive = UIEngine.prompt_user_confirm(
        "Recursive access (include subdirectories)?",
        default_choice=True,
    )
    scope = AccessScope.RECURSIVE if is_recursive else AccessScope.SHALLOW

    # Read Permission
    allow_read = UIEngine.prompt_user_confirm(
        "Allow Read access?",
        default_choice=True,
    )

    # Write Permission
    allow_write = UIEngine.prompt_user_confirm(
        "Allow Modification? (Write/Create)",
        default_choice=False,
    )
    if allow_write:
        allow_create = True
        allow_delete = UIEngine.prompt_user_confirm(
            "Allow Deletion?",
            default_choice=False,
        )
    else:
        allow_create = False
        allow_delete = False

    # Check if user effectively denied everything
    if not allow_read and not allow_write and not allow_create and not allow_delete:
        if UIEngine.prompt_user_confirm(
            "⚠️  You selected NO permissions. Deny access?",
            default_choice=True,
        ):
            print("   [red]✖ Access Denied by User.[/red]\n")
            return False
        else:
            # Retry custom config
            print("   [yellow]↺ Restarting selection...[/yellow]")
            # This is a recursive call but depth is limited by user choices
            return _handle_custom_permission(target_path)

    # TTL
    ttl_minutes_str = UIEngine.prompt_user_input(
        "TTL in Minutes (0=Forever)",
        default_value="0",
    )
    try:
        ttl_minutes = int(ttl_minutes_str)
        if ttl_minutes < 0:
            print("   [red]Please enter a non-negative number.[/red]")
            return False
        ttl_seconds = ttl_minutes * 60 if ttl_minutes > 0 else None
    except ValueError:
        print("   [red]Invalid input. Please enter a number.[/red]")
        return False

    # Add permission
    try:
        security_manager.add_permission(
            target_path,
            scope=scope,
            allow_read=allow_read,
            allow_write=allow_write,
            allow_create=allow_create,
            allow_delete=allow_delete,
            ttl_seconds=ttl_seconds,
        )
        print(f"   [green]✔ Access Granted.[/green]\n")
        return True
    except Exception as e:
        print(f"   [red]✖ Authorization Failed: {e}[/red]\n")
        return False


if __name__ == "__main__":
    # Preview code
    fake_path = "/var/www/project/secret_config.json"
    fake_error = Exception(
        "No known permission rule covers /var/www/project/secret_config.json"
    )
    handle_permission_error(fake_error)

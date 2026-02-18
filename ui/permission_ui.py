from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.table import Table
from rich import box
import re
import sys
import os
from pathlib import Path
import logging

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
    # Print the specific error for debugging
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
console = Console()


def _get_path_display(path: str) -> str:
    """Truncate long paths"""
    path_str = str(path)
    if len(path_str) > 60:
        return "..." + path_str[-57:]
    return path_str


def handle_permission_error(exception: Exception) -> bool:
    """
    Minimalist Permission Intercept UI (English Version)
    """
    # [ADAPTATION] Extract path from Exception if not provided explicitly
    target_path = ""
    error_msg = str(exception)

    # Priority 1: Extract from specific "Rule <PATH> does not..." pattern (High Confidence)
    path_match = re.search(r"Rule\s+(.+?)\s+does not", error_msg)

    # Priority 2: Extract from "covers <PATH>" pattern
    if not path_match:
        path_match = re.search(r"covers\s+(.+?)(\.|$)", error_msg)

    # Priority 3: Extract from "path '<PATH>'" pattern
    if not path_match:
        path_match = re.search(r"path '(.+?)'", error_msg)

    # Priority 4: Fallback - Looking for absolute paths, BUT ignoring common python files to avoid traceback noise
    if not path_match:
        # Find all candidates resembling paths
        candidates = re.findall(r"([a-zA-Z]:\\[^\s\"'<>\)]+|/[^\s\"'<>\)]+)", error_msg)
        for cand in candidates:
            # Filter out python source files which are likely traceback artifacts
            # Only skip .py if it's likely a system/library file, to allow editing user scripts
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

    if not target_path or target_path == "":
        target_path = "Unknown Target"

    # UI Style: Vercel/Linear Minimalist

    # [1] Info Grid
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(style="dim bold", width=14)
    grid.add_column(style="bright_white")

    # Resource
    grid.add_row("Resource Path", _get_path_display(target_path))

    # Status
    if "ExplicitDeny" in str(type(exception)) or "ExplicitDenyError" in str(
        type(exception)
    ):
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

    # [2] Menu
    menu_text = Text()
    menu_text.append("\n Options ", style="dim underline")
    menu_text.append("\n")
    menu_text.append(" [Y] ", style="black on green")
    menu_text.append(" Allow (Recursive)", style="bold green")
    menu_text.append("   ")
    menu_text.append(" [T] ", style="black on yellow")
    menu_text.append(" Temp (30m)", style="yellow")
    menu_text.append("   ")
    menu_text.append(" [C] ", style="black on blue")
    menu_text.append(" Custom ", style="blue")
    menu_text.append("   ")
    menu_text.append(" [N] ", style="black on red")
    menu_text.append(" Deny ", style="red")

    # [3] Panel
    panel_content = Table.grid(expand=True)
    panel_content.add_row(grid)
    panel_content.add_row(menu_text)

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

    # [4] Prompt
    choice = Prompt.ask(
        " Select Action",
        choices=["y", "n", "c", "t"],
        default="y",
        show_choices=False,
        show_default=False,
    )

    if choice == "n":
        console.print("   [red]✖ Access Denied.[/red]\n")
        return False

    # --- Logic ---

    if not security_manager:
        if __name__ == "__main__":
            console.print("   [dim]Preview Mode: Output simulated[/dim]\n")
            return True
        console.print(
            "   [bold red]Error: Security Manager component not loaded.[/bold red]"
        )
        console.print(
            "   [dim]Ensure 'mcp_server.operate_file.security.SecurityManager' is importable.[/dim]\n"
        )
        return False

    # Default Logic (Y)
    scope = AccessScope.RECURSIVE
    allow_read = True
    allow_write = True
    allow_create = True
    allow_delete = True
    ttl_seconds = None

    if choice == "t":
        ttl_seconds = 1800
        console.print("   [yellow]⏱️  Authorized (30 min)[/yellow]")

    if choice == "c":
        console.print()
        is_recursive = Confirm.ask("   Recursive?", default=True)
        scope = AccessScope.RECURSIVE if is_recursive else AccessScope.SHALLOW

        # Explicitly ask for Read Permission
        allow_read = Confirm.ask("   Allow Read?", default=True)

        # Ask for Write Permission
        allow_write = Confirm.ask(
            "   Allow Modification? (Write/Create)", default=False
        )
        if allow_write:
            allow_create = True
            allow_delete = Confirm.ask("   Allow Deletion?", default=False)
        else:
            allow_create = False
            allow_delete = False

        # Check if user effectively denied everything
        if not allow_read and not allow_write and not allow_create and not allow_delete:
            if Confirm.ask(
                "   ⚠️  You selected NO permissions. Deny access?", default=True
            ):
                console.print("   [red]✖ Access Denied by User.[/red]\n")
                return False
            else:
                # Retry custom config
                console.print("   [yellow]↺ Restarting selection...[/yellow]")
                return handle_permission_error(exception)

        # Input Validation for TTL
        while True:
            ttl_input = Prompt.ask("   TTL in Minutes (0=Forever)", default="0")
            try:
                val = int(ttl_input)
                if val < 0:
                    console.print("   [red]Please enter a non-negative number.[/red]")
                    continue
                ttl_seconds = val * 60 if val > 0 else None
                break
            except ValueError:
                console.print("   [red]Invalid input. Please enter a number.[/red]")

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
        console.print(f"   [green]✔ Access Granted.[/green]\n")
        return True
    except Exception as e:
        console.print(f"   [red]✖ Authorization Failed: {e}[/red]\n")
        return False


if __name__ == "__main__":
    # 预览代码
    fake_path = "/var/www/project/secret_config.json"
    fake_error = Exception(
        "No known permission rule covers /var/www/project/secret_config.json"
    )
    handle_permission_error(fake_error)

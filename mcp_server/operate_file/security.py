import os
import time
import json
import logging
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass, asdict, field
from typing import Dict, Optional, Union, Tuple, List

logger = logging.getLogger("filesystem-security")


class SecurityError(PermissionError):
    """Base class for security errors."""

    pass


class ImplicitDenyError(SecurityError):
    """
    Access denied because no configuration exists for this path (Default Zero Trust).
    UI Intention: Prompt the user to grant permission.
    """

    pass


class ExplicitDenyError(SecurityError):
    """
    Access denied because a configured rule explicitly forbids this action.
    UI Intention: Do NOT prompt (user already decided).
    """

    pass


class AccessScope(IntEnum):
    DENIED = 0  # 禁止访问
    SHALLOW = 1  # 仅限当前目录（不允许子目录）
    RECURSIVE = 2  # 递归访问（允许子目录）


@dataclass
class PermissionRule:
    scope: int = AccessScope.DENIED

    # Granular Permissions
    allow_read: bool = True
    allow_create: bool = False
    allow_write: bool = False  # 修改现有文件
    allow_delete: bool = False

    # TTL (Unix Timestamp, None = Forever)
    expires_at: Optional[float] = None

    # Filtering (预留位：黑白名单)
    whitelist_patterns: List[str] = field(default_factory=list)
    blacklist_patterns: List[str] = field(default_factory=list)

    def to_dict(self):
        data = asdict(self)
        if self.expires_at is not None:
            # 保留2位小数即可，不必微秒级精确
            data["expires_at"] = round(self.expires_at, 2)
        return data

    @staticmethod
    def from_dict(data: dict):
        return PermissionRule(
            scope=data.get("scope", 0),
            allow_read=data.get("allow_read", True),
            allow_create=data.get("allow_create", False),
            allow_write=data.get("allow_write", False),
            allow_delete=data.get("allow_delete", False),
            expires_at=data.get("expires_at"),
            whitelist_patterns=data.get("whitelist_patterns", []),
            blacklist_patterns=data.get("blacklist_patterns", []),
        )

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


CONFIG_FILE = Path(__file__).parent / "permissions.json"


class SecurityManager:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.permissions: Dict[Path, PermissionRule] = {}
        self._last_mtime = 0.0

        # 确保配置文件存在（如果不存在则创建一个空的）
        if not self.config_path.exists():
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                logger.info(f"Created empty permissions file at {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to create permissions file: {e}")

        self._load_config()
        self._cleanup_expired_rules()

        # 默认安全策略：如果无配置，直接拒绝所有访问 (最安全)
        # 用户或前端必须显式配置 permissions.json 才能启用功能
        if not self.permissions:
            logger.warning(
                "No permission rules found. Filesystem access is strictly explicitly DENIED by default."
            )

    def _cleanup_expired_rules(self):
        """Remove any rules that have already expired upon loading."""
        expired_paths = []
        for path, rule in self.permissions.items():
            if rule.is_expired():
                expired_paths.append(path)

        if expired_paths:
            for path in expired_paths:
                del self.permissions[path]
                logger.info(f"Startup Cleanup: Removed expired permission for {path}")
            self.save_config()

    def _load_config(self):
        """Load permissions from JSON file."""
        if not self.config_path.exists():
            return

        try:
            # Check timestamp to avoid redundant loads if called frequently
            current_mtime = self.config_path.stat().st_mtime
            if current_mtime == self._last_mtime:
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                new_permissions = {}
                for path_str, rule_data in data.items():
                    # 确保存储的是绝对路径
                    new_permissions[Path(path_str).resolve()] = (
                        PermissionRule.from_dict(rule_data)
                    )
                self.permissions = new_permissions
                self._last_mtime = current_mtime

            # Re-run cleanup after loading
            self._cleanup_expired_rules()
            logger.info(f"Loaded {len(self.permissions)} permission rules (Updated).")
        except Exception as e:
            logger.error(f"Failed to load permissions: {e}")

    def save_config(self):
        """Save permissions to JSON file for persistence."""
        try:
            data = {str(p): r.to_dict() for p, r in self.permissions.items()}
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")

    def add_permission(
        self,
        path: Union[str, Path],
        scope: int,
        allow_read: bool = True,
        allow_write: bool = False,
        allow_create: bool = False,
        allow_delete: bool = False,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Add or update a permission rule with granular controls.
        Supports both files and directories.
        If a rule for the exact same path exists, it will be UPDATED (overwritten).
        """
        abs_path = Path(path).resolve()

        expires_at = None
        if ttl_seconds:
            expires_at = time.time() + ttl_seconds

        new_rule = PermissionRule(
            scope=scope,
            allow_read=allow_read,
            allow_write=allow_write,
            allow_create=allow_create,
            allow_delete=allow_delete,
            expires_at=expires_at,
        )

        # Python dictionary automatically handles overwrite if key exists
        action_type = "Updated" if abs_path in self.permissions else "Added"

        self.permissions[abs_path] = new_rule
        self.save_config()

        logger.info(
            f"Rule {action_type} for {abs_path}: Scope={AccessScope(scope).name}"
        )

    def remove_permission(self, path: Union[str, Path]):
        """Remove a permission rule."""
        abs_path = Path(path).resolve()
        if abs_path in self.permissions:
            del self.permissions[abs_path]
            self.save_config()

    def get_effective_permission(
        self, target_path: Path
    ) -> Tuple[PermissionRule, Optional[Path]]:
        """
        Check permissions using 'Longest Prefix Match' logic.
        Returns: (EffectiveRule, MatchedRulePath)
        """
        # Hot Reload: Check for external updates before evaluating
        self._load_config()

        target_path = target_path.resolve()

        # 1. Exact match
        if target_path in self.permissions:
            return self.permissions[target_path], target_path

        # 2. Parent match (Longest Prefix Match)
        sorted_rules = sorted(
            self.permissions.keys(), key=lambda p: len(p.parts), reverse=True
        )

        for rule_path in sorted_rules:
            try:
                target_path.relative_to(rule_path)
                return self.permissions[rule_path], rule_path
            except ValueError:
                continue

        # 3. No rule found -> Default to Denied
        return PermissionRule(scope=AccessScope.DENIED), None

    def validate_access(self, path: Union[str, Path], action: str = "read") -> Path:
        """
        Main entry point. Validates path and returns resolved Path object if allowed.
        Args:
            path: Target path
            action: "read", "write", "create", "delete"
        Raises:
            ImplicitDenyError: If no rule covers this path (Ask User).
            ExplicitDenyError: If a rule covers it but forbids action (Don't Ask).
            PermissionError: General error.
        """
        try:
            target = Path(path).resolve()
        except Exception as e:
            raise PermissionError(f"Invalid path format: {e}")

        rule, rule_path = self.get_effective_permission(target)

        # 0. Check Expiration
        if rule.is_expired():
            if rule_path in self.permissions:
                logger.warning(
                    f"Permission for {rule_path} expired at {rule.expires_at}. Removing rule."
                )
                del self.permissions[rule_path]
                self.save_config()
            raise ImplicitDenyError(
                f"Access Denied: Permission for {rule_path} has expired."
            )

        # 1. Implicit Deny Check (No rule found)
        if rule_path is None:
            raise ImplicitDenyError(
                f"Access Denied: No known permission rule covers {target}."
            )

        # 2. Check Scope
        if rule.scope == AccessScope.DENIED:
            raise ExplicitDenyError(
                f"Access Denied (Scope 0): {target} is explicitly forbidden by rule at {rule_path}."
            )

        if rule.scope == AccessScope.SHALLOW:
            # Case 1: Checking the folder itself
            if target == rule_path:
                pass
            # Case 2: Checking a direct child
            elif target.parent == rule_path:
                pass
            else:
                raise ExplicitDenyError(
                    f"Access Denied (Scope 1 - Shallow): Cannot access deep path {target}. Root: {rule_path}"
                )

        # 3. Check Granular Action
        if action == "read" and not rule.allow_read:
            raise ExplicitDenyError(
                f"Read Denied: Rule {rule_path} does not allow reading."
            )
        if action == "write" and not rule.allow_write:
            raise ExplicitDenyError(
                f"Write Denied: Rule {rule_path} does not allow modification."
            )
        if action == "create" and not rule.allow_create:
            raise ExplicitDenyError(
                f"Create Denied: Rule {rule_path} does not allow creating files."
            )
        if action == "delete" and not rule.allow_delete:
            raise ExplicitDenyError(
                f"Delete Denied: Rule {rule_path} does not allow deletion."
            )

        return target


# Singleton Instance
security_manager = SecurityManager()


def validate_path(path: Union[str, Path], action: str = "read") -> Path:
    """
    Helper function using the singleton security manager.
    """
    return security_manager.validate_access(path, action=action)

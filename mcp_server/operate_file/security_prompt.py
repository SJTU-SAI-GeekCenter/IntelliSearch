import json
from pathlib import Path
import sys

# Ensure project root is importable (for `from core.UI import UIEngine`)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from security import validate_path, ImplicitDenyError, ExplicitDenyError
except ImportError:
    from .security import validate_path, ImplicitDenyError, ExplicitDenyError


PERMISSION_REQUEST_MARKER = "PERMISSION_REQUEST::"


def ensure_path_access(path: str, action: str) -> Path:
    """
    Validate security access.

    On implicit deny, this function raises an ImplicitDenyError with a structured
    marker payload. Caller side (main CLI process) can intercept this marker and
    open interactive Form safely.

    Returns:
        Resolved Path object when allowed.

    Raises:
        PermissionError / ExplicitDenyError when not granted.
    """
    try:
        return validate_path(path, action=action)
    except ExplicitDenyError:
        raise
    except ImplicitDenyError as e:
        target = Path(path).resolve()
        payload = {
            "target_path": str(target),
            "action": action,
            "reason": str(e),
        }
        raise ImplicitDenyError(
            f"{PERMISSION_REQUEST_MARKER}{json.dumps(payload, ensure_ascii=False)}"
        ) from e

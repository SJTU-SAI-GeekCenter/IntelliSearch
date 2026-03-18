from rich.live import Live
from rich.text import Text
from rich.console import Console
from rich.console import Group
import threading

_layer_lock = threading.RLock()
_layers = {
    "status": None,
    "form": None,
    "misc": None,
}


def _compose_layers():
    parts = []
    # status 在上，form 在下，避免互相覆盖
    if _layers.get("status") is not None:
        parts.append(_layers["status"])
    if _layers.get("form") is not None:
        parts.append(_layers["form"])
    if _layers.get("misc") is not None:
        parts.append(_layers["misc"])

    if not parts:
        return Text("")
    return Group(*parts)


# Disable auto_refresh to allow KeyboardInterrupt to propagate
# This enables Ctrl+C to work even when Live is active
live = Live(
    _compose_layers(),
    console=Console(),
    refresh_per_second=10,
    transient=True,
    auto_refresh=False,  # Important: allows Ctrl+C to work during Live display
    vertical_overflow="visible",
)


def set_live_layer(name: str, renderable):
    """Set one live layer and refresh composed output."""
    with _layer_lock:
        _layers[name] = renderable
        live.update(_compose_layers(), refresh=True)


def clear_live_layer(name: str):
    """Clear one live layer and refresh composed output."""
    with _layer_lock:
        _layers[name] = None
        live.update(_compose_layers(), refresh=True)


def has_live_layers() -> bool:
    """Whether any live layer is active."""
    with _layer_lock:
        return any(v is not None for v in _layers.values())


def start_live():
    """
    安全启动 live 实例，避免重复启动导致的 RuntimeError。

    Rich.Live.start() 在已经启动时再次调用会抛出 RuntimeError。
    此函数使用 try/except 来处理这种情况，确保不会因重复调用而崩溃。

    这比检查内部 _started 属性更安全，因为：
    1. 不依赖私有属性
    2. 处理所有可能的启动失败情况
    3. 与 Rich 的内部实现解耦

    注意：如果在异常状态下调用，这可能会静默失败。但这是合理的设计选择，
    因为在大多数情况下，live.start() 的失败都是因为已经启动。
    """
    try:
        live.start()
    except RuntimeError:
        # 已经启动，忽略错误
        pass


def stop_live():
    """
    安全停止 live 实例。

    使用 try/except 处理可能的异常，确保在未启动的情况下调用不会崩溃。
    """
    try:
        live.stop()
    except (RuntimeError, AttributeError):
        # 未启动或已停止，忽略错误
        pass

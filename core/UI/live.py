from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

panel = Text("")
# Disable auto_refresh to allow KeyboardInterrupt to propagate
# This enables Ctrl+C to work even when Live is active
live = Live(
    panel,
    console=Console(),
    refresh_per_second=10,
    transient=True,
    auto_refresh=False,  # Important: allows Ctrl+C to work during Live display
)


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

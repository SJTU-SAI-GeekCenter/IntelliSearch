from rich.live import Live
from core.UI.console import console
from rich.panel import Panel
from rich.text import Text

panel = Text("")
live = Live(panel, console=console, refresh_per_second=10, transient=True)

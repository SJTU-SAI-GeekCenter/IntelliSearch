"""
Welcome UI component for displaying logo and messages.

This module provides the WelcomeUI class for displaying the SAI-IntelliSearch
logo in a visually appealing way using rich formatting.
"""

from core.UI.theme import ThemeColors


class WelcomeUI:
    """
    Helper class for displaying welcome logo and message.

    This class provides methods to display the SAI-IntelliSearch logo
    in a visually appealing way using rich formatting.
    """

    LOGO_ART = """
██╗███╗   ██╗████████╗███████╗██╗     ██╗     ██╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
██║████╗  ██║╚══██╔══╝██╔════╝██║     ██║     ██║██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
██║██╔██╗ ██║   ██║   █████╗  ██║     ██║     ██║███████╗█████╗  ███████║██████╔╝██║     ███████║
██║██║╚██╗██║   ██║   ██╔══╝  ██║     ██║     ██║╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
██║██║ ╚████║   ██║   ███████╗███████╗███████╗██║███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║
╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""

    def __init__(self, console):
        """
        Initialize WelcomeUI.

        Args:
            console: Rich console instance for output
        """
        self.console = console

    def display_logo(
        self,
        title: str = "[bold]SJTU-SAI Geek Center[/bold]",
        subtitle: str = None,  # type: ignore[assignment]
    ) -> None:
        """
        Display beautiful SAI-IntelliSearch logo with ASCII art.

        Args:
            title: Panel title (default: SJTU-SAI Geek Center)
            subtitle: Optional subtitle to display below logo
        """
        from rich.panel import Panel
        from rich.text import Text
        from rich.style import Style

        logo_text = Text()
        logo_text.append(
            self.LOGO_ART, style=Style(color=ThemeColors.ACCENT, bold=True)
        )

        logo_panel = Panel(
            logo_text,
            border_style=Style(color=ThemeColors.PRIMARY),
            padding=(1, 2),
            title=title,
            title_align="right",
        )

        self.console.print(logo_panel)

        if subtitle:
            subtitle_text = Text()
            subtitle_text.append(subtitle, style=Style(color=ThemeColors.SECONDARY))
            self.console.print(subtitle_text)

        self.console.print()

    def display_welcome_message(
        self,
        message: str = "Welcome to IntelliSearch CLI!",
        style: str = ThemeColors.SUCCESS,
    ) -> None:
        """
        Display a welcome message.

        Args:
            message: Welcome message text
            style: Color style for the message
        """
        from rich.text import Text
        from rich.style import Style

        welcome_text = Text()
        welcome_text.append(message, style=Style(color=style))
        self.console.print(welcome_text)
        self.console.print()

    def display_full_welcome(
        self,
        title: str = "[bold]SJTU-SAI Geek Center[/bold]",
        subtitle: str = None,  # type: ignore[assignment]
        message: str = "Welcome to IntelliSearch CLI!",
    ) -> None:
        """
        Display full welcome screen with logo, subtitle, and message.

        Args:
            title: Panel title
            subtitle: Optional subtitle
            message: Welcome message
        """
        self.display_logo(title=title, subtitle=subtitle)
        self.display_welcome_message(message=message)

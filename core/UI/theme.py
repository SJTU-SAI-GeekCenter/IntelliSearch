"""
Theme colors for IntelliSearch CLI.

This module defines the color scheme used throughout the application,
including the dark green primary theme and cyan/blue tool UI theme.
"""

from rich.theme import Theme


class ThemeColors:
    """Color scheme for IntelliSearch CLI (Dark Green Theme)."""

    # Primary colors (Dark Green Theme)
    PRIMARY = "#2E5A38"  # Deep green
    SECONDARY = "#3A7A4A"  # Medium green
    ACCENT = "#4CAF50"  # Bright green

    # Tool UI colors (Cyan/Blue Theme - distinct from green)
    TOOL_PRIMARY = "#265A5A"  # Deep cyan
    TOOL_SECONDARY = "#367A7A"  # Medium cyan
    TOOL_ACCENT = "#00BCD4"  # Bright cyan
    TOOL_BORDER = "#4DD0E1"  # Light cyan border

    # Summarizing colors (Pink-Orange Theme - for final response generation)
    SUMMARY_PRIMARY = "#5A3A3A"  # Deep pink-orange
    SUMMARY_SECONDARY = "#7A4A4A"  # Medium pink-orange
    SUMMARY_ACCENT = "#FF8C69"  # Pink-orange (coral)
    SUMMARY_BORDER = "#FFAB91"  # Light pink-orange border

    # UI colors
    BG = "#1A1A1A"  # Dark background
    FG = "#E0E0E0"  # Light text
    DIM = "#808080"  # Dimmed text

    # Status colors
    SUCCESS = "#66BB6A"  # Green
    WARNING = "#FFA726"  # Orange
    ERROR = "#EF5350"  # Red
    INFO = "#42A5F5"  # Blue

    # Error severity colors
    FATAL = "#B71C1C"  # Deep red (fatal)
    CRITICAL = "#D32F2F"  # Red (critical)
    NOTICE = "#42A5F5"  # Blue (notice)

    # Special colors
    USER_BUBBLE = "#2E5A38"  # User message background
    ASSISTANT_BUBBLE = "#1E3A24"  # Assistant message background
    BORDER = "#3A7A4A"  # Border color

    @classmethod
    def get_rich_theme(cls) -> Theme:
        """
        Get Rich Theme object with custom color styles.

        Returns:
            Theme: Rich Theme with custom styles
        """
        styles = {
            "primary": f"bold {cls.PRIMARY}",
            "secondary": cls.SECONDARY,
            "accent": f"bold {cls.ACCENT}",
            "success": cls.SUCCESS,
            "warning": cls.WARNING,
            "error": f"bold {cls.ERROR}",
            "info": cls.INFO,
            "dim": cls.DIM,
            "tool": cls.TOOL_ACCENT,
            "summary": cls.SUMMARY_ACCENT,
            "user": cls.USER_BUBBLE,
            "assistant": cls.ASSISTANT_BUBBLE,
        }
        return Theme(styles)

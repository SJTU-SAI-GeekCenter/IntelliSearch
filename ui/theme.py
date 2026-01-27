"""
Theme colors for IntelliSearch CLI.

This module defines the color scheme used throughout the application,
including the dark green primary theme and cyan/blue tool UI theme.
"""


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

    # UI colors
    BG = "#1A1A1A"  # Dark background
    FG = "#E0E0E0"  # Light text
    DIM = "#808080"  # Dimmed text

    # Status colors
    SUCCESS = "#66BB6A"  # Green
    WARNING = "#FFA726"  # Orange
    ERROR = "#EF5350"  # Red
    INFO = "#42A5F5"  # Blue

    # Special colors
    USER_BUBBLE = "#2E5A38"  # User message background
    ASSISTANT_BUBBLE = "#1E3A24"  # Assistant message background
    BORDER = "#3A7A4A"  # Border color

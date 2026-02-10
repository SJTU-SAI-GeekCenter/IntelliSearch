import pyperclip
import os
import math
from simpleeval import (
    SimpleEval,
    NameNotDefined,
    FunctionNotDefined,
    FeatureNotAvailable,
)
from datetime import datetime
from PIL import ImageGrab
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Base-ToolKit")


@mcp.tool()
def get_current_date() -> str:
    """
    Get the current date in the local timezone.

    Returns:
        str: Current date in "YYYY-MM-DD" format.
    """
    try:
        now = datetime.now()
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        weekday_str = weekdays[now.weekday()]

        return f"{now.strftime('%Y-%m-%d')} {weekday_str}"
    except Exception as e:
        return f"Error getting current date: {str(e)}"


@mcp.tool()
def get_current_time() -> str:
    """
    Get the current time in the local timezone.

    Returns:
        str: Current time in "%Y-%m-%d,%H:%M:%S" format.
    """
    try:
        now = datetime.now()
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        weekday_str = weekdays[now.weekday()]
        return f"{now.strftime('%Y-%m-%d,%H:%M:%S')} {weekday_str}"
    except Exception as e:
        return f"Error getting current time: {str(e)}"


@mcp.tool()
def calculate_maths(expression: str) -> str:
    """
    Safely evaluate a mathematical expression and return the result.
    supported expressions and functions:
        - abs, round, min, max, pow, sqrt, sin, cos, tan, log, pi, e

    Args:
        expression (str): A mathematical expression string, e.g., "2 + 3 * 4".

    Returns:
        str: The result of the calculation as a string, or an error message.
    """
    s = SimpleEval()
    s.functions = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        result = s.eval(expression)
        if isinstance(result, (int, float)):
            if isinstance(result, float):
                result = round(result, 6)
            return f"Result: {result}"
        else:
            return "Error: Expression did not return a number"

    except ZeroDivisionError:
        return "Error: Division by zero"
    except (NameNotDefined, FunctionNotDefined) as e:
        return f"Error: {str(e)}"
    except FeatureNotAvailable:
        return "Error: Use of forbidden Python features"
    except SyntaxError:
        return f"Error: Invalid syntax in expression: '{expression}'"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


@mcp.tool()
def get_clipboard(max_length: int = 2000) -> str:
    """
    Reads the text content from the local system clipboard.

    Args:
        max_length (int): The maximum number of characters to return. Defaults to 2000
                          to prevent excessive token usage from large clipboard data.

    Returns:
        str: The text content from the clipboard. Returns a notification if the
             clipboard is empty, contains non-text data, or if an error occurs.
    """
    try:
        # Retrieve clipboard content
        content = pyperclip.paste()

        if not content:
            return "The clipboard is currently empty or does not contain valid text."

        # Track original length for the truncation notice
        original_length = len(content)

        # Trim whitespace and truncate content based on max_length
        processed_content = content[:max_length].strip()

        if original_length > max_length:
            return (
                f"{processed_content}\n\n"
                f"[System Note: Content truncated from {original_length} to {max_length} characters.]"
            )

        return processed_content

    except Exception as e:
        return f"Error reading clipboard: {str(e)}"


@mcp.tool()
def take_screenshot(save_path: str) -> str:
    """
    Captures a full screenshot of the current system desktop and saves it to a local path.

    Args:
        save_path (str): The local file path where the screenshot will be saved (e.g., 'screenshot.png').

    Returns:
        str: A message confirming success with the file path, or an error message.
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(save_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Capture the entire screen
        screenshot = ImageGrab.grab()

        # Save the file
        screenshot.save(save_path)

        return f"Screenshot successfully saved to: {os.path.abspath(save_path)}"

    except Exception as e:
        return f"Failed to take screenshot: {str(e)}"


if __name__ == "__main__":
    mcp.run()

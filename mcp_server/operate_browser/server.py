from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Operate-Browser")

# todo 总体目标
# 利用 Playwright 等开源库实现若干组件化工具，让 Agent 可以通过环境和浏览器进行交互
# 具体任务：
# 完成若干 @mcp.tool() 的函数实现
# 优化 Docstring

from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any

mcp = FastMCP("Operate-Browser")


@mcp.tool()
def open_url(url: str, wait_for_network: bool = True):
    """
    Opens a specific URL in a new browser tab.

    Args:
        url (str): The complete URL to visit (e.g., 'https://www.google.com').
        wait_for_network (bool): If True, waits until the network is idle before returning.
    """
    pass


@mcp.tool()
def get_page_content(selector: str = "body", format: str = "text") -> str:
    """
    Retrieves the content of the currently active page.

    Args:
        selector (str): CSS selector to target specific content. Defaults to "body".
        format (str): The output format, either "text" for plain text or "html" for source code.

    Returns:
        str: The extracted content, truncated if it exceeds context limits.
    """
    pass


@mcp.tool()
def click_element(selector: str, timeout: int = 5000):
    """
    Clicks a specific element on the page identified by a CSS or XPath selector.

    Args:
        selector (str): The selector of the element to click (e.g., 'button#submit', '//a[text()="Login"]').
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
    """
    pass


@mcp.tool()
def input_text(selector: str, text: str, press_enter: bool = False):
    """
    Types text into an input field or textarea.

    Args:
        selector (str): The CSS or XPath selector of the input field.
        text (str): The string to type into the field.
        press_enter (bool): If True, simulates pressing the 'Enter' key after typing.
    """
    pass


@mcp.tool()
def scroll_page(direction: str = "down", amount: Optional[int] = None):
    """
    Scrolls the current page up or down.

    Args:
        direction (str): The direction to scroll, either 'up' or 'down'.
        amount (int, optional): The number of pixels to scroll. If None, scrolls by one viewport height.
    """
    pass


@mcp.tool()
def take_page_screenshot(save_path: str, full_page: bool = False) -> str:
    """
    Captures a screenshot of the current browser tab.

    Args:
        save_path (str): Local file path to save the screenshot (e.g., './downloads/page.png').
        full_page (bool): If True, captures the entire scrollable page height.

    Returns:
        str: The absolute path of the saved image.
    """
    pass


@mcp.tool()
def get_browser_state() -> Dict[str, Any]:
    """
    Returns the current metadata of the browser, such as active URL and page title.

    Returns:
        dict: A dictionary containing 'url', 'title', and 'tab_count'.
    """
    pass


if __name__ == "__main__":
    mcp.run()

"""
Browser Operation MCP Server

This server provides comprehensive browser automation capabilities using Playwright,
allowing agents to interact with web pages through a standardized MCP interface.
"""

from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from pathlib import Path
import asyncio
import json

mcp = FastMCP("Operate-Browser")


class BrowserManager:
    """
    Singleton class to manage browser instances and contexts.

    This class maintains the lifecycle of browser instances, pages, and contexts,
    enabling stateful browser operations across multiple tool calls.

    Attributes:
        _instance: The singleton instance of BrowserManager.
        _playwright: The Playwright async context manager.
        _browser: The active Browser instance.
        _context: The active BrowserContext for cookies and storage.
        _pages: Dictionary tracking all open pages/tabs by ID.
        _current_page_id: ID of the currently active page.
        _next_page_id: Counter for generating unique page IDs.
        _request_logs: List storing HTTP request/response logs.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._pages: Dict[str, Page] = {}
        self._current_page_id: Optional[str] = None
        self._next_page_id = 1
        self._request_logs: List[Dict[str, Any]] = []
        self._initialized = True

    async def get_browser(self, headless: bool = True) -> Browser:
        """
        Get or create a browser instance.

        Args:
            headless: Whether to run browser in headless mode (no GUI).

        Returns:
            The active Browser instance.
        """
        if self._browser is None:
            self._playwright = async_playwright()
            playwright_instance = await self._playwright.__aenter__()

            # Try to use installed Chromium, fallback to Playwright's bundled browser
            try:
                self._browser = await playwright_instance.chromium.launch(
                    headless=headless, args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
            except Exception as e:
                raise

        return self._browser

    async def get_context(self) -> BrowserContext:
        """
        Get or create a browser context.

        A browser context is an isolated session with its own cookies,
        cache, and storage.

        Returns:
            The active BrowserContext instance.
        """
        if self._context is None:
            browser = await self.get_browser()
            self._context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )

        return self._context

    async def get_current_page(self) -> Page:
        """
        Get the currently active page.

        Returns:
            The active Page instance.

        Raises:
            RuntimeError: If no page is currently active.
        """
        if self._current_page_id is None or self._current_page_id not in self._pages:
            # Create a new page if none exists
            context = await self.get_context()
            page = await context.new_page()
            page_id = str(self._next_page_id)
            self._next_page_id += 1
            self._pages[page_id] = page
            self._current_page_id = page_id

        return self._pages[self._current_page_id]

    async def new_page(self) -> str:
        """
        Create a new page/tab and make it the current page.

        Returns:
            The ID of the newly created page.
        """
        context = await self.get_context()
        page = await context.new_page()
        page_id = str(self._next_page_id)
        self._next_page_id += 1
        self._pages[page_id] = page
        self._current_page_id = page_id
        return page_id

    async def switch_page(self, page_id: str) -> bool:
        """
        Switch to a different page/tab.

        Args:
            page_id: The ID of the page to switch to.

        Returns:
            True if successfully switched, False if page_id not found.
        """
        if page_id in self._pages:
            self._current_page_id = page_id
            return True
        return False

    async def close_page(self, page_id: Optional[str] = None) -> bool:
        """
        Close a specific page or the current page.

        Args:
            page_id: The ID of the page to close. If None, closes current page.

        Returns:
            True if successfully closed, False otherwise.
        """
        target_id = page_id or self._current_page_id

        if target_id and target_id in self._pages:
            await self._pages[target_id].close()
            del self._pages[target_id]

            # Reset current_page_id if we closed the current page
            if self._current_page_id == target_id:
                self._current_page_id = (
                    list(self._pages.keys())[0] if self._pages else None
                )

            return True
        return False

    async def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        Get information about all open pages.

        Returns:
            List of dictionaries containing page IDs, URLs, and titles.
        """
        pages_info = []
        for page_id, page in self._pages.items():
            try:
                pages_info.append(
                    {"page_id": page_id, "url": page.url, "title": await page.title()}
                )
            except Exception as e:
                pages_info.append(
                    {"page_id": page_id, "url": "unknown", "title": "unknown"}
                )
        return pages_info

    async def close(self):
        """Close all browser resources and clean up."""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.__aexit__(None, None, None)
            self._playwright = None

        self._pages.clear()
        self._current_page_id = None


# Global browser manager instance
browser_manager = BrowserManager()


# ============================================================================
# Basic Navigation Tools
# ============================================================================


@mcp.tool()
async def open_url(
    url: str, wait_for_network: bool = True, timeout: int = 30000
) -> str:
    """
    Opens a specific URL in a new browser tab.

    This tool navigates to the specified URL and optionally waits for network
    requests to complete before returning. Supports both HTTP and HTTPS protocols.

    Args:
        url (str): The complete URL to visit (e.g., 'https://www.google.com', 'https://github.com').
                   Must include the protocol (http:// or https://).
        wait_for_network (bool): If True, waits until the network is nearly idle
                                (no more than 2 requests for 500ms). Default is True.
                                This ensures the page is fully loaded.
        timeout (int): Maximum time in milliseconds to wait for the page to load.
                      Default is 30000 (30 seconds).

    Returns:
        str: A success message containing the final URL and page title, or an error message.

    Examples:
        >>> await open_url("https://www.example.com")
        "Successfully opened https://www.example.com - Title: Example Domain"
        >>> await open_url("https://github.com/microsoft/playwright", wait_for_network=False)
        "Opened https://github.com/microsoft/playwright - Title: playwright/python"

    Raises:
        Exception: If the URL is invalid, navigation fails, or timeout is exceeded.
    """
    try:
        page = await browser_manager.get_current_page()

        if wait_for_network:
            await page.goto(url, wait_until="networkidle", timeout=timeout)
        else:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

        title = await page.title()
        return f"Successfully opened {url} - Title: {title}"

    except Exception as e:
        error_msg = f"Failed to open URL {url}: {str(e)}"
        return error_msg


@mcp.tool()
async def get_page_content(
    selector: str = "body", format: str = "text", timeout: int = 5000
) -> str:
    """
    Retrieves the content of the currently active page.

    Extracts content from the page using a CSS selector. Can return either
    plain text (with readable formatting) or raw HTML source code.

    Args:
        selector (str): CSS selector to target specific content. Defaults to "body" (entire page).
                       Examples: "article", ".content", "#main", "div.post p".
        format (str): The output format. Must be either "text" for plain text
                     or "html" for source code. Default is "text".
        timeout (int): Maximum time in milliseconds to wait for the selector to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: The extracted content. If "text" format, returns readable text content.
             If "html" format, returns raw HTML markup.
             Returns empty string if selector is not found or an error occurs.

    Examples:
        >>> await get_page_content()
        "Welcome to my website... [full page text content]"
        >>> await get_page_content("article", "text")
        "[article text content only]"
        >>> await get_page_content(".header", "html")
        "<div class='header'>...HTML source...</div>"

    Raises:
        Exception: If the selector is invalid or content extraction fails.
    """
    try:
        page = await browser_manager.get_current_page()

        # Wait for element
        await page.wait_for_selector(selector, timeout=timeout)

        if format == "html":
            content = await page.locator(selector).inner_html()
        else:
            content = await page.locator(selector).inner_text()

        # Truncate if too long (prevent context overflow)
        max_length = 50000
        if len(content) > max_length:
            content = (
                content[:max_length] + f"\n... [truncated, total {len(content)} chars]"
            )

        return content

    except Exception as e:
        error_msg = f"Failed to get content with selector '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def click_element(
    selector: str, timeout: int = 5000, wait_after: bool = True
) -> str:
    """
    Clicks a specific element on the page identified by a CSS or XPath selector.

    This tool will scroll the element into view if needed and perform a click action.
    Optionally waits for navigation after clicking (useful for links and buttons).

    Args:
        selector (str): The selector of the element to click.
                       CSS examples: 'button#submit', 'a[href="/login"]', '.btn-primary'.
                       XPath examples: '//a[text()="Login"]', '//button[@type="submit"]'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear
                      and become clickable. Default is 5000 (5 seconds).
        wait_after (bool): If True, waits for potential navigation after clicking.
                          Default is True. Set to False for non-navigational clicks.

    Returns:
        str: Success message if click was performed, or error message if element
             not found or not clickable.

    Examples:
        >>> await click_element("button.submit")
        "Successfully clicked element: button.submit"
        >>> await click_element('//a[text()="Next Page"]', wait_after=True)
        "Clicked element and waited for navigation: //a[text()='Next Page']"
        >>> await click_element(".menu-item", wait_after=False)
        "Successfully clicked element: .menu-item"

    Raises:
        Exception: If selector is invalid, element not found, timeout exceeded,
                  or element is obscured/not clickable.
    """
    try:
        page = await browser_manager.get_current_page()

        if wait_after:
            async with page.expect_navigation(
                wait_until="networkidle", timeout=timeout
            ):
                await page.click(selector, timeout=timeout)
        else:
            await page.click(selector, timeout=timeout)

        return f"Successfully clicked element: {selector}"

    except Exception as e:
        error_msg = f"Failed to click element '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def input_text(
    selector: str,
    text: str,
    press_enter: bool = False,
    clear_first: bool = True,
    timeout: int = 5000,
) -> str:
    """
    Types text into an input field or textarea.

    This tool will focus the specified input field and type the provided text character by character.
    Optionally clears existing content before typing and simulates pressing Enter.

    Args:
        selector (str): The CSS or XPath selector of the input field.
                       Examples: 'input[name="email"]', '#username', 'textarea#message'.
        text (str): The string to type into the field. Can be any UTF-8 text.
                   Examples: "hello@example.com", "Hello World!", "12345".
        press_enter (bool): If True, simulates pressing the 'Enter' key after typing.
                           Default is False. Useful for search forms and submissions.
        clear_first (bool): If True, clears existing content in the field before typing.
                           Default is True. Set to False to append text.
        timeout (int): Maximum time in milliseconds to wait for the input field to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message with the text that was entered, or error message if input fails.

    Examples:
        >>> await input_text("input[name='email']", "user@example.com")
        "Entered text 'user@example.com' into input[name='email']"
        >>> await input_text("#search", "Python tutorial", press_enter=True)
        "Entered text 'Python tutorial' into #search and pressed Enter"
        >>> await input_text("textarea", "Additional notes here", clear_first=False)
        "Appended text 'Additional notes here' to textarea"

    Raises:
        Exception: If selector is invalid, element not found, or element is not an input field.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_selector(selector, timeout=timeout)

        input_field = page.locator(selector)

        if clear_first:
            await input_field.clear()

        await input_field.fill(text)

        if press_enter:
            await input_field.press("Enter")

        return f"Entered text '{text}' into {selector}" + (
            " and pressed Enter" if press_enter else ""
        )

    except Exception as e:
        error_msg = f"Failed to input text into '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def scroll_page(direction: str = "down", amount: Optional[int] = None) -> str:
    """
    Scrolls the current page up or down.

    Performs page scrolling either by a specific pixel amount or by one viewport height.
    Useful for revealing content below the fold or navigating back up the page.

    Args:
        direction (str): The direction to scroll. Must be either 'up' or 'down'.
                        Default is "down". Case-insensitive.
        amount (int, optional): The number of pixels to scroll. If None, scrolls by
                               one viewport height (approximately 1080 pixels).
                               Default is None. Examples: 500, 1000, 2000.

    Returns:
        str: Success message indicating the scroll direction and amount.

    Examples:
        >>> await scroll_page()
        "Scrolled down by viewport height"
        >>> await scroll_page("up")
        "Scrolled up by viewport height"
        >>> await scroll_page("down", 500)
        "Scrolled down by 500 pixels"
        >>> await scroll_page("up", 200)
        "Scrolled up by 200 pixels"

    Raises:
        ValueError: If direction is not 'up' or 'down'.
        Exception: If scroll operation fails.
    """
    try:
        page = await browser_manager.get_current_page()

        if direction.lower() not in ["up", "down"]:
            return "Error: direction must be 'up' or 'down'"

        scroll_amount = (
            amount if amount is not None else 1080
        )  # Default viewport height
        direction_value = (
            scroll_amount if direction.lower() == "down" else -scroll_amount
        )

        await page.evaluate(f"window.scrollBy(0, {direction_value})")

        return f"Scrolled {direction} by {scroll_amount} pixels"

    except Exception as e:
        error_msg = f"Failed to scroll page: {str(e)}"
        return error_msg


@mcp.tool()
async def take_page_screenshot(
    save_path: str = "./screenshot.png", full_page: bool = False, timeout: int = 5000
) -> str:
    """
    Captures a screenshot of the current browser tab.

    Saves a screenshot of the current page to the specified file path.
    Can capture either the visible viewport or the entire scrollable page.

    Args:
        save_path (str): Local file path to save the screenshot. Must include file extension.
                        Examples: './screenshot.png', '/tmp/page.png', 'downloads/capture.png'.
                        Supported formats: PNG, JPEG.
        full_page (bool): If True, captures the entire scrollable page height.
                         If False, captures only the visible viewport.
                         Default is False. Note: Full page screenshots may be very large.
        timeout (int): Maximum time in milliseconds to wait for screenshot to complete.
                      Default is 5000 (5 seconds).

    Returns:
        str: Absolute path of the saved screenshot file, or error message if capture fails.

    Examples:
        >>> await take_page_screenshot("./my_screenshot.png")
        "/Users/user/project/my_screenshot.png"
        >>> await take_page_screenshot("/tmp/full.png", full_page=True)
        "/tmp/full.png"
        >>> await take_page_screenshot("capture.jpg")

    Raises:
        Exception: If save_path is invalid, directory doesn't exist, or screenshot capture fails.
    """
    try:
        page = await browser_manager.get_current_page()

        # Create directory if it doesn't exist
        save_file = Path(save_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)

        await page.screenshot(path=save_path, full_page=full_page, timeout=timeout)

        absolute_path = str(save_file.absolute())
        return absolute_path

    except Exception as e:
        error_msg = f"Failed to take screenshot: {str(e)}"
        return error_msg


@mcp.tool()
async def get_browser_state() -> Dict[str, Any]:
    """
    Returns the current metadata of the browser, such as active URL and page title.

    Provides comprehensive information about the current browser state including
    URL, page title, and number of open tabs.

    Returns:
        dict: A dictionary containing the following keys:
            - url (str): The URL of the current page.
            - title (str): The title of the current page.
            - tab_count (int): The number of open browser tabs.
            - current_tab_id (str): The ID of the currently active tab.

    Examples:
        >>> await get_browser_state()
        {
            "url": "https://www.example.com",
            "title": "Example Domain",
            "tab_count": 3,
            "current_tab_id": "1"
        }

    Raises:
        Exception: If unable to retrieve browser state.
    """
    try:
        page = await browser_manager.get_current_page()

        state = {
            "url": page.url,
            "title": await page.title(),
            "tab_count": len(browser_manager._pages),
            "current_tab_id": browser_manager._current_page_id,
        }

        return state

    except Exception as e:
        error_msg = f"Failed to get browser state: {str(e)}"
        return {"error": error_msg}


# ============================================================================
# Wait and Selection Tools
# ============================================================================


@mcp.tool()
async def wait_for_element(
    selector: str, state: str = "visible", timeout: int = 30000
) -> str:
    """
    Waits for an element to appear and reach a specific state on the page.

    This tool pauses execution until the specified element meets the desired state condition.
    Useful for handling dynamic content and AJAX-loaded elements.

    Args:
        selector (str): The CSS or XPath selector to wait for.
                       Examples: '.loading-finished', '#result', '//div[@class="content"]'.
        state (str): The state to wait for. Must be one of:
                    - 'attached': Element is present in DOM (may be hidden).
                    - 'detached': Element is removed from DOM.
                    - 'visible': Element is present and visible (default).
                    - 'hidden': Element is present but not visible (display:none or opacity:0).
        timeout (int): Maximum time in milliseconds to wait. Default is 30000 (30 seconds).

    Returns:
        str: Success message when element reaches the desired state, or timeout message.

    Examples:
        >>> await wait_for_element(".result")
        "Element '.result' became visible"
        >>> await wait_for_element("#loading", state="hidden")
        "Element '#loading' became hidden"
        >>> await wait_for_element("//button[@disabled]", state="detached", timeout=60000)
        "Element '//button[@disabled]' was removed from DOM"

    Raises:
        ValueError: If state parameter is invalid.
        Exception: If timeout is exceeded or selector is invalid.
    """
    try:
        page = await browser_manager.get_current_page()

        if state not in ["attached", "detached", "visible", "hidden"]:
            return f"Error: state must be one of 'attached', 'detached', 'visible', 'hidden'"

        await page.wait_for_selector(selector, state=state, timeout=timeout)

        return f"Element '{selector}' reached state: {state}"

    except Exception as e:
        error_msg = f"Timeout waiting for element '{selector}' to reach state '{state}': {str(e)}"
        return error_msg


@mcp.tool()
async def wait_for_navigation(timeout: int = 30000) -> str:
    """
    Waits for a page navigation to complete.

    Use this tool after performing an action that triggers a navigation (like clicking a link)
    to ensure the new page has fully loaded before proceeding.

    Args:
        timeout (int): Maximum time in milliseconds to wait for navigation.
                      Default is 30000 (30 seconds).

    Returns:
        str: Success message when navigation completes, or timeout message.

    Examples:
        >>> await click_element("a.next-page", wait_after=False)
        "Successfully clicked element: a.next-page"
        >>> await wait_for_navigation()
        "Navigation completed"

    Raises:
        Exception: If timeout is exceeded or no navigation occurs.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_load_state("networkidle", timeout=timeout)
        return "Navigation completed"

    except Exception as e:
        error_msg = f"Timeout waiting for navigation: {str(e)}"
        return error_msg


@mcp.tool()
async def get_element_text(selector: str, timeout: int = 5000) -> str:
    """
    Retrieves the visible text content of a specific element.

    Extracts only the text content from the specified element, excluding HTML tags.
    Useful for scraping specific sections of a page.

    Args:
        selector (str): The CSS or XPath selector of the element.
                       Examples: 'h1', '.title', '#description', '//p[@class="summary"]'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: The visible text content of the element, or error message if not found.

    Examples:
        >>> await get_element_text("h1")
        "Welcome to My Website"
        >>> await get_element_text(".product-price")
        "$29.99"
        >>> await get_element_text("//*[@id='description']")
        "This is a great product with many features..."

    Raises:
        Exception: If element not found or content extraction fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_selector(selector, timeout=timeout)

        text = await page.locator(selector).inner_text()

        return text

    except Exception as e:
        error_msg = f"Failed to get text from '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def get_element_attribute(
    selector: str, attribute: str, timeout: int = 5000
) -> str:
    """
    Retrieves the value of a specific attribute from an element.

    Gets the value of HTML attributes like href, src, id, class, data-*, etc.

    Args:
        selector (str): The CSS or XPath selector of the element.
                       Examples: 'a.link', 'img.logo', 'input[type="text"]'.
        attribute (str): The attribute name to retrieve.
                        Examples: 'href', 'src', 'id', 'class', 'data-id', 'value'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: The attribute value, or error message if element/attribute not found.

    Examples:
        >>> await get_element_attribute("a.home", "href")
        "https://www.example.com/home"
        >>> await get_element_attribute("img.logo", "src")
        "/assets/logo.png"
        >>> await get_element_attribute("input[name='csrf']", "value")
        "abc123token456"

    Raises:
        Exception: If element not found or attribute doesn't exist.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_selector(selector, timeout=timeout)

        value = await page.get_attribute(selector, attribute)

        if value is None:
            return f"Attribute '{attribute}' not found on element '{selector}'"

        return value

    except Exception as e:
        error_msg = f"Failed to get attribute '{attribute}' from '{selector}': {str(e)}"
        return error_msg


# ============================================================================
# Mouse Interaction Tools
# ============================================================================


@mcp.tool()
async def hover_element(selector: str, timeout: int = 5000) -> str:
    """
    Hovers the mouse cursor over a specific element.

    Simulates moving the mouse over an element without clicking.
    Useful for triggering hover effects, dropdown menus, and tooltips.

    Args:
        selector (str): The CSS or XPath selector of the element to hover over.
                       Examples: '.menu-item', '#dropdown-trigger', '.tooltip-trigger'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message, or error message if element not found or hover fails.

    Examples:
        >>> await hover_element(".menu-item")
        "Successfully hovered over element: .menu-item"
        >>> await hover_element("#dropdown-trigger")
        "Successfully hovered over element: #dropdown-trigger"

    Raises:
        Exception: If element not found or hover operation fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.hover(selector, timeout=timeout)
        return f"Successfully hovered over element: {selector}"

    except Exception as e:
        error_msg = f"Failed to hover over '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def double_click(selector: str, timeout: int = 5000) -> str:
    """
    Performs a double-click action on an element.

    Simulates a double mouse click on the specified element.
    Useful for interactions that require double-clicking (e.g., opening files, selecting text).

    Args:
        selector (str): The CSS or XPath selector of the element to double-click.
                       Examples: '.file', 'button#edit', '.icon'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message, or error message if element not found or click fails.

    Examples:
        >>> await double_click(".file")
        "Successfully double-clicked element: .file"
        >>> await double_click("button#edit")
        "Successfully double-clicked element: button#edit"

    Raises:
        Exception: If element not found or double-click operation fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.dblclick(selector, timeout=timeout)
        return f"Successfully double-clicked element: {selector}"

    except Exception as e:
        error_msg = f"Failed to double-click '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def right_click(selector: str, timeout: int = 5000) -> str:
    """
    Performs a right-click (context menu) action on an element.

    Simulates a right mouse click on the specified element to open context menus.

    Args:
        selector (str): The CSS or XPath selector of the element to right-click.
                       Examples: '.file', '#element', 'table.row'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message, or error message if element not found or click fails.

    Examples:
        >>> await right_click(".file")
        "Successfully right-clicked element: .file"
        >>> await right_click("#element")
        "Successfully right-clicked element: #element"

    Raises:
        Exception: If element not found or right-click operation fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.click(selector, button="right", timeout=timeout)
        return f"Successfully right-clicked element: {selector}"

    except Exception as e:
        error_msg = f"Failed to right-click '{selector}': {str(e)}"
        return error_msg


# ============================================================================
# Keyboard and File Input Tools
# ============================================================================


@mcp.tool()
async def press_key(
    key: str, selector: Optional[str] = None, timeout: int = 5000
) -> str:
    """
    Simulates pressing a keyboard key.

    Presses a specified keyboard key, optionally after focusing an element.
    Supports special keys like Enter, Escape, Arrow keys, and function keys.

    Args:
        key (str): The key to press. Examples:
                   - Single characters: 'a', '1', '@'
                   - Special keys: 'Enter', 'Escape', 'Tab', 'Backspace', 'Delete'
                   - Arrow keys: 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'
                   - Function keys: 'F1', 'F2', ..., 'F12'
                   - Modifiers: 'Control+a', 'Shift+KeyA', 'Meta+c' (Cmd/Ctrl)
        selector (str, optional): The CSS or XPath selector of an element to focus before pressing.
                                  If None, presses the key on the currently focused element.
        timeout (int): Maximum time in milliseconds to wait for the selector if provided.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message, or error message if operation fails.

    Examples:
        >>> await press_key("Escape")
        "Successfully pressed key: Escape"
        >>> await press_key("Control+a", "input[name='text']")
        "Successfully pressed key: Control+a on input[name='text']"
        >>> await press_key("ArrowDown")
        "Successfully pressed key: ArrowDown"

    Raises:
        Exception: If selector is invalid or key press fails.
    """
    try:
        page = await browser_manager.get_current_page()

        if selector:
            await page.wait_for_selector(selector, timeout=timeout)
            page.locator(selector).focus()

        await page.keyboard.press(key)

        target_msg = f" on {selector}" if selector else ""
        return f"Successfully pressed key: {key}{target_msg}"

    except Exception as e:
        error_msg = f"Failed to press key '{key}': {str(e)}"
        return error_msg


@mcp.tool()
async def upload_file(selector: str, file_path: str, timeout: int = 5000) -> str:
    """
    Uploads a file to a file input element.

    Selects a file from the local filesystem to be uploaded through a file input field.

    Args:
        selector (str): The CSS or XPath selector of the file input element.
                       Examples: 'input[type="file"]', '#file-upload', '.file-input'.
        file_path (str): Absolute or relative path to the file to upload.
                        Examples: '/Users/user/Documents/file.pdf', './data.csv'.
        timeout (int): Maximum time in milliseconds to wait for the element to appear.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message with file name, or error message if upload fails.

    Examples:
        >>> await upload_file("input[type='file']", "/path/to/file.pdf")
        "Successfully uploaded file: file.pdf"
        >>> await upload_file("#upload", "./data.csv")
        "Successfully uploaded file: data.csv"

    Raises:
        Exception: If element not found, file doesn't exist, or upload fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_selector(selector, timeout=timeout)

        # Convert to absolute path if relative
        file_abs_path = str(Path(file_path).absolute())

        await page.set_input_files(selector, file_abs_path)

        file_name = Path(file_path).name
        return f"Successfully uploaded file: {file_name}"

    except Exception as e:
        error_msg = f"Failed to upload file '{file_path}': {str(e)}"
        return error_msg


# ============================================================================
# Form Operation Tools
# ============================================================================


@mcp.tool()
async def fill_form(
    fields: Dict[str, str], submit: bool = False, timeout: int = 5000
) -> str:
    """
    Fills multiple form fields at once.

    Fills multiple input fields, textareas, and selects in a single operation.
    Can optionally submit the form after filling.

    Args:
        fields (dict): Dictionary mapping selectors to values.
                      Keys are CSS/XPath selectors, values are the text to fill.
                      Examples:
                      {
                          'input[name="email"]': 'user@example.com',
                          'input[name="password"]': 'secret123',
                          'textarea#message': 'Hello World'
                      }
        submit (bool): If True, submits the form after filling by pressing Enter
                      on the last field or clicking a submit button. Default is False.
        timeout (int): Maximum time in milliseconds to wait for each element.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message listing filled fields, or error message if any fill fails.

    Examples:
        >>> await fill_form({'input[name="email"]': 'user@example.com', 'input[name="password"]': 'pass123'})
        "Filled 2 fields: email, password"
        >>> await fill_form({'#username': 'john', '#email': 'john@example.com'}, submit=True)
        "Filled 2 fields: username, email and submitted form"

    Raises:
        Exception: If any selector is invalid or fill operation fails.
    """
    try:
        page = await browser_manager.get_current_page()

        filled_count = 0
        field_names = []

        for selector, value in fields.items():
            await page.wait_for_selector(selector, timeout=timeout)
            await page.fill(selector, value)
            filled_count += 1

            # Extract field name from selector for reporting
            field_name = selector.split("[")[-1].rstrip('"]')
            field_names.append(field_name)


        if submit:
            # Try to find and click a submit button, or press Enter
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
            ]
            submitted = False

            for submit_selector in submit_selectors:
                try:
                    await page.click(submit_selector, timeout=1000)
                    submitted = True
                    break
                except Exception:
                    continue

            if not submitted:
                await page.keyboard.press("Enter")

            return f"Filled {filled_count} fields: {', '.join(field_names)} and submitted form"

        return f"Filled {filled_count} fields: {', '.join(field_names)}"

    except Exception as e:
        error_msg = f"Failed to fill form: {str(e)}"
        return error_msg


@mcp.tool()
async def select_option(
    selector: str,
    value: Optional[str] = None,
    label: Optional[str] = None,
    index: Optional[int] = None,
    timeout: int = 5000,
) -> str:
    """
    Selects an option from a dropdown (select) element.

    Selects an option from a dropdown menu by value, visible text, or index.

    Args:
        selector (str): The CSS or XPath selector of the select element.
                       Examples: 'select[name="country"]', '#dropdown', 'form select'.
        value (str, optional): Select by option value attribute.
                             Example: For <option value="us">United States</option>, value="us".
        label (str, optional): Select by visible text content.
                             Example: For <option value="us">United States</option>, label="United States".
        index (int, optional): Select by option index (0-based).
                             Example: index=0 selects the first option.
        timeout (int): Maximum time in milliseconds to wait for the element.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message indicating which option was selected, or error message.

    Examples:
        >>> await select_option("select[name='country']", value="us")
        "Selected option by value: us"
        >>> await select_option("#dropdown", label="United States")
        "Selected option by label: United States"
        >>> await select_option("form select", index=0)
        "Selected option by index: 0"

    Raises:
        Exception: If selector invalid, element not found, or selection fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_selector(selector, timeout=timeout)

        if value:
            await page.select_option(selector, value=value)
            return f"Selected option by value: {value}"
        elif label:
            await page.select_option(selector, label=label)
            return f"Selected option by label: {label}"
        elif index is not None:
            await page.select_option(selector, index=index)
            return f"Selected option by index: {index}"
        else:
            return "Error: Must specify value, label, or index"

    except Exception as e:
        error_msg = f"Failed to select option from '{selector}': {str(e)}"
        return error_msg


@mcp.tool()
async def check_checkbox(
    selector: str, checked: bool = True, timeout: int = 5000
) -> str:
    """
    Checks or unchecks a checkbox or radio button.

    Sets the checked state of a checkbox or radio button element.

    Args:
        selector (str): The CSS or XPath selector of the checkbox/radio element.
                       Examples: 'input[type="checkbox"]', '#agree', 'input[name="subscribe"]'.
        checked (bool): True to check the element, False to uncheck.
                       Default is True.
        timeout (int): Maximum time in milliseconds to wait for the element.
                      Default is 5000 (5 seconds).

    Returns:
        str: Success message, or error message if operation fails.

    Examples:
        >>> await check_checkbox("#agree")
        "Checked element: #agree"
        >>> await check_checkbox("input[name='subscribe']", checked=False)
        "Unchecked element: input[name='subscribe']"

    Raises:
        Exception: If selector invalid or element not found.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_selector(selector, timeout=timeout)

        if checked:
            await page.check(selector)
        else:
            await page.uncheck(selector)

        action = "Checked" if checked else "Unchecked"
        return f"{action} element: {selector}"

    except Exception as e:
        error_msg = (
            f"Failed to {'check' if checked else 'uncheck'} '{selector}': {str(e)}"
        )
        return error_msg


@mcp.tool()
async def get_all_links(selector: str = "a") -> List[Dict[str, str]]:
    """
    Extracts all links from the page or from a specific section.

    Retrieves all anchor (<a>) elements with their href, text, and title attributes.

    Args:
        selector (str): CSS selector to scope the link search. Defaults to "a" (all links).
                       Examples: "a" (all), ".content a" (links in content area), "#menu a" (menu links).

    Returns:
        list: List of dictionaries, each containing:
              - text (str): The visible link text.
              - href (str): The URL the link points to.
              - title (str): The title attribute (if present).

    Examples:
        >>> await get_all_links()
        [
            {"text": "Home", "href": "/home", "title": ""},
            {"text": "About", "href": "/about", "title": "About Us"}
        ]
        >>> await get_all_links(".content a")
        [{"text": "Read more", "href": "/article/123", "title": ""}]

    Raises:
        Exception: If link extraction fails.
    """
    try:
        page = await browser_manager.get_current_page()

        links = await page.locator(selector).all()
        result = []

        for link in links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                title = await link.get_attribute("title") or ""

                result.append(
                    {"text": text.strip(), "href": href or "", "title": title}
                )
            except Exception:
                continue

        return result

    except Exception as e:
        error_msg = f"Failed to get links: {str(e)}"
        return [{"error": error_msg}]


# ============================================================================
# JavaScript Execution Tools
# ============================================================================


@mcp.tool()
async def execute_javascript(code: str) -> str:
    """
    Executes arbitrary JavaScript code in the page context.

    Runs custom JavaScript code and returns the result. Useful for operations
    not supported by other tools.

    Args:
        code (str): The JavaScript code to execute.
                   Examples:
                   - 'document.title'
                   - 'window.scrollY'
                   - '[...document.querySelectorAll(".item")].map(e => e.textContent)'

    Returns:
        str: The result of the JavaScript execution as a string, or error message.

    Examples:
        >>> await execute_javascript("document.title")
        "Example Domain"
        >>> await execute_javascript("window.scrollY")
        "500"
        >>> await execute_javascript("document.cookie")
        "session=abc123; user=john"

    Raises:
        Exception: If code execution fails.
    """
    try:
        page = await browser_manager.get_current_page()
        result = await page.evaluate(code)

        # Convert result to string
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result, ensure_ascii=False)
        else:
            result_str = str(result)

        return result_str

    except Exception as e:
        error_msg = f"Failed to execute JavaScript: {str(e)}"
        return error_msg


@mcp.tool()
async def evaluate_function(function: str, *args) -> str:
    """
    Evaluates a JavaScript function with arguments.

    Executes a JavaScript function with provided arguments and returns the result.

    Args:
        function (str): The JavaScript function to execute.
                       Examples:
                       - '(element) => element.textContent'
                       - '(selector) => document.querySelector(selector).href'
                       - '(x, y) => x + y'
        *args: Arguments to pass to the function.

    Returns:
        str: The function result as a string, or error message.

    Examples:
        >>> await evaluate_function("(selector) => document.querySelector(selector).textContent", "h1")
        "Welcome"
        >>> await evaluate_function("(a, b) => a + b", 5, 3)
        "8"

    Raises:
        Exception: If function evaluation fails.
    """
    try:
        page = await browser_manager.get_current_page()
        result = await page.evaluate(function, *args)

        result_str = (
            json.dumps(result, ensure_ascii=False)
            if isinstance(result, (dict, list))
            else str(result)
        )

        return result_str

    except Exception as e:
        error_msg = f"Failed to evaluate function: {str(e)}"
        return error_msg


# ============================================================================
# Alert and Dialog Handling
# ============================================================================


@mcp.tool()
async def handle_dialog(action: str, prompt_text: Optional[str] = None) -> str:
    """
    Handles JavaScript alerts, confirms, and prompts.

    Accepts or dismisses browser dialogs (alerts, confirm dialogs, prompts).
    Must be called BEFORE the action that triggers the dialog.

    Args:
        action (str): The action to perform. Must be 'accept' or 'dismiss'.
        prompt_text (str, optional): Text to enter into a prompt dialog if accepting.
                                    Ignored for alert and confirm dialogs.

    Returns:
        str: Success message, or error message if action fails.

    Examples:
        >>> # Before clicking a button that shows an alert
        >>> await handle_dialog("accept")
        "Accepted dialog"
        >>> # Before a confirm dialog
        >>> await handle_dialog("dismiss")
        "Dismissed dialog"
        >>> # Before a prompt dialog
        >>> await handle_dialog("accept", "John Doe")
        "Accepted dialog with prompt text: John Doe"

    Raises:
        Exception: If action is invalid or dialog handling fails.
    """
    try:
        if action not in ["accept", "dismiss"]:
            return "Error: action must be 'accept' or 'dismiss'"

        page = await browser_manager.get_current_page()

        async def handle_dialog(dialog):
            if action == "accept":
                if prompt_text and dialog.type == "prompt":
                    await dialog.accept(prompt_text)
                else:
                    await dialog.accept()
            else:
                await dialog.dismiss()

        page.on("dialog", lambda dialog: asyncio.create_task(handle_dialog(dialog)))

        return f"Set up handler to {action} dialog"

    except Exception as e:
        error_msg = f"Failed to handle dialog: {str(e)}"
        return error_msg


# ============================================================================
# Navigation Control Tools
# ============================================================================


@mcp.tool()
async def go_back() -> str:
    """
    Navigates to the previous page in browser history.

    Performs the same action as clicking the browser's back button.

    Returns:
        str: Success message with the new URL, or error message.

    Examples:
        >>> await go_back()
        "Navigated back to: https://www.example.com/home"

    Raises:
        Exception: If there is no previous page or navigation fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.go_back()

        new_url = page.url
        return f"Navigated back to: {new_url}"

    except Exception as e:
        error_msg = f"Failed to go back: {str(e)}"
        return error_msg


@mcp.tool()
async def go_forward() -> str:
    """
    Navigates to the next page in browser history.

    Performs the same action as clicking the browser's forward button.

    Returns:
        str: Success message with the new URL, or error message.

    Examples:
        >>> await go_forward()
        "Navigated forward to: https://www.example.com/next"

    Raises:
        Exception: If there is no forward page or navigation fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.go_forward()

        new_url = page.url
        return f"Navigated forward to: {new_url}"

    except Exception as e:
        error_msg = f"Failed to go forward: {str(e)}"
        return error_msg


@mcp.tool()
async def refresh_page(wait_for_network: bool = True) -> str:
    """
    Refreshes the current page.

    Reloads the current page, optionally waiting for network requests to complete.

    Args:
        wait_for_network (bool): If True, waits for network idle after refresh.
                                Default is True.

    Returns:
        str: Success message, or error message if refresh fails.

    Examples:
        >>> await refresh_page()
        "Page refreshed successfully"
        >>> await refresh_page(wait_for_network=False)
        "Page refreshed quickly"

    Raises:
        Exception: If refresh fails.
    """
    try:
        page = await browser_manager.get_current_page()

        if wait_for_network:
            await page.reload(wait_until="networkidle")
        else:
            await page.reload(wait_until="domcontentloaded")

        return "Page refreshed successfully"

    except Exception as e:
        error_msg = f"Failed to refresh page: {str(e)}"
        return error_msg


# ============================================================================
# Tab Management Tools
# ============================================================================


@mcp.tool()
async def new_tab(url: Optional[str] = None) -> str:
    """
    Opens a new browser tab.

    Creates a new tab and optionally navigates to a URL.

    Args:
        url (str, optional): URL to navigate to in the new tab.
                            If None, opens a blank tab.

    Returns:
        str: Success message with the new tab ID.

    Examples:
        >>> await new_tab()
        "Opened new tab with ID: 2"
        >>> await new_tab("https://www.example.com")
        "Opened new tab with ID: 3 and navigated to https://www.example.com"

    Raises:
        Exception: If tab creation or navigation fails.
    """
    try:
        page_id = await browser_manager.new_page()

        if url:
            page = await browser_manager.get_current_page()
            await page.goto(url)
            return f"Opened new tab with ID: {page_id} and navigated to {url}"

        return f"Opened new tab with ID: {page_id}"

    except Exception as e:
        error_msg = f"Failed to open new tab: {str(e)}"
        return error_msg


@mcp.tool()
async def switch_tab(page_id: str) -> str:
    """
    Switches to a different browser tab.

    Changes the active tab to the specified page ID.

    Args:
        page_id (str): The ID of the tab to switch to.
                      Use get_all_tabs() to list available tab IDs.

    Returns:
        str: Success message with tab details, or error message if tab not found.

    Examples:
        >>> await switch_tab("2")
        "Switched to tab 2: https://www.example.com - Example Domain"

    Raises:
        Exception: If tab ID is invalid or switch fails.
    """
    try:
        success = await browser_manager.switch_page(page_id)

        if not success:
            return f"Error: Tab with ID '{page_id}' not found"

        page = await browser_manager.get_current_page()
        url = page.url
        title = await page.title()

        return f"Switched to tab {page_id}: {url} - {title}"

    except Exception as e:
        error_msg = f"Failed to switch to tab '{page_id}': {str(e)}"
        return error_msg


@mcp.tool()
async def close_tab(page_id: Optional[str] = None) -> str:
    """
    Closes a browser tab.

    Closes the specified tab, or the current tab if no ID is provided.

    Args:
        page_id (str, optional): The ID of the tab to close.
                                If None, closes the current tab.

    Returns:
        str: Success message, or error message if close fails.

    Examples:
        >>> await close_tab()
        "Closed current tab: 1"
        >>> await close_tab("2")
        "Closed tab: 2"

    Raises:
        Exception: If tab ID is invalid or close fails.
    """
    try:
        target_id = page_id or browser_manager._current_page_id
        success = await browser_manager.close_page(target_id)

        if success:
            return f"Closed tab: {target_id}"
        else:
            return f"Error: Failed to close tab '{target_id}'"

    except Exception as e:
        error_msg = f"Failed to close tab: {str(e)}"
        return error_msg


@mcp.tool()
async def get_all_tabs() -> List[Dict[str, Any]]:
    """
    Lists all open browser tabs.

    Returns information about all open tabs including IDs, URLs, and titles.

    Returns:
        list: List of dictionaries, each containing:
              - page_id (str): The unique tab identifier.
              - url (str): The URL of the page.
              - title (str): The page title.

    Examples:
        >>> await get_all_tabs()
        [
            {"page_id": "1", "url": "https://www.google.com", "title": "Google"},
            {"page_id": "2", "url": "https://www.github.com", "title": "GitHub"}
        ]

    Raises:
        Exception: If retrieval fails.
    """
    try:
        tabs = await browser_manager.get_all_pages()
        return tabs

    except Exception as e:
        error_msg = f"Failed to get tabs: {str(e)}"
        return [{"error": error_msg}]


# ============================================================================
# Network Control Tools
# ============================================================================


@mcp.tool()
async def set_http_headers(headers: Dict[str, str]) -> str:
    """
    Sets custom HTTP headers for all requests.

    Adds custom headers to be sent with every HTTP request from the browser.

    Args:
        headers (dict): Dictionary of header names and values.
                       Examples:
                       {
                           'Authorization': 'Bearer token123',
                           'User-Agent': 'Custom Agent',
                           'Accept-Language': 'en-US'
                       }

    Returns:
        str: Success message listing set headers, or error message.

    Examples:
        >>> await set_http_headers({'Authorization': 'Bearer abc123'})
        "Set 1 HTTP header(s)"
        >>> await set_http_headers({'X-Custom-Header': 'value', 'User-Agent': 'MyApp'})
        "Set 2 HTTP header(s)"

    Raises:
        Exception: If setting headers fails.
    """
    try:
        context = await browser_manager.get_context()
        await context.set_extra_http_headers(headers)

        return f"Set {len(headers)} HTTP header(s)"

    except Exception as e:
        error_msg = f"Failed to set HTTP headers: {str(e)}"
        return error_msg


@mcp.tool()
async def get_request_logs(max_count: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves recent HTTP request logs.

    Returns a log of recent HTTP requests made by the browser.

    Args:
        max_count (int): Maximum number of recent requests to return.
                        Default is 50.

    Returns:
        list: List of request dictionaries, each containing:
              - url (str): The request URL.
              - method (str): HTTP method (GET, POST, etc.).
              - status (int): HTTP status code.
              - timestamp (str): Request timestamp.

    Examples:
        >>> await get_request_logs(10)
        [
            {"url": "https://api.example.com/data", "method": "GET", "status": 200, "timestamp": "..."},
            {"url": "https://example.com/script.js", "method": "GET", "status": 200, "timestamp": "..."}
        ]

    Raises:
        Exception: If log retrieval fails.
    """
    try:
        # Return logs from browser manager
        logs = browser_manager._request_logs[-max_count:]
        return logs

    except Exception as e:
        error_msg = f"Failed to get request logs: {str(e)}"
        return [{"error": error_msg}]


@mcp.tool()
async def block_requests(patterns: List[str]) -> str:
    """
    Blocks network requests matching specific patterns.

    Prevents the browser from loading resources that match the given patterns.
    Useful for blocking ads, trackers, or specific resource types.

    Args:
        patterns (list): List of URL patterns to block.
                        Examples:
                        - ['*.png', '*.jpg'] - Block all images
                        - ['*analytics*', '*tracker*'] - Block analytics/tracking
                        - ['*ads.com*'] - Block specific domains

    Returns:
        str: Success message indicating number of patterns blocked.

    Examples:
        >>> await block_requests(['*.png', '*.jpg', '*.gif'])
        "Blocked 3 request pattern(s)"
        >>> await block_requests(['*analytics*', '*tracker*'])
        "Blocked 2 request pattern(s)"

    Raises:
        Exception: If blocking fails.
    """
    try:
        context = await browser_manager.get_context()

        async def block_handler(route):
            await route.abort()

        await context.route(
            "**/*",
            lambda route: asyncio.create_task(
                block_handler(route)
                if any(p in route.request.url for p in patterns)
                else route.continue_()
            ),
        )

        return f"Blocked {len(patterns)} request pattern(s)"

    except Exception as e:
        error_msg = f"Failed to block requests: {str(e)}"
        return error_msg


# ============================================================================
# Search and Find Tools
# ============================================================================


@mcp.tool()
async def find_text(search_text: str) -> str:
    """
    Searches for specific text on the current page.

    Finds the first occurrence of the specified text and returns surrounding context.

    Args:
        search_text (str): The text to search for (case-sensitive).

    Returns:
        str: Message indicating whether text was found and its location,
             or error message if text not found.

    Examples:
        >>> await find_text("Welcome")
        "Found text 'Welcome' on the page"
        >>> await find_text("Specific phrase")
        "Text 'Specific phrase' not found on the page"

    Raises:
        Exception: If search operation fails.
    """
    try:
        page = await browser_manager.get_current_page()

        # Use page.evaluate to search for text
        found = await page.evaluate(
            f"() => document.body.innerText.includes('{search_text}')"
        )

        if found:
            return f"Found text '{search_text}' on the page"
        else:
            return f"Text '{search_text}' not found on the page"

    except Exception as e:
        error_msg = f"Failed to find text '{search_text}': {str(e)}"
        return error_msg


@mcp.tool()
async def find_elements_by_text(
    text: str, exact_match: bool = False
) -> List[Dict[str, Any]]:
    """
    Finds all elements containing specific text.

    Returns a list of elements that contain the specified text, along with their selectors.

    Args:
        text (str): The text to search for.
        exact_match (bool): If True, requires exact text match. Default is False.

    Returns:
        list: List of element dictionaries, each containing:
              - tag (str): The HTML tag name.
              - text (str): The element text content.
              - xpath (str): XPath selector for the element.

    Examples:
        >>> await find_elements_by_text("Click here")
        [
            {"tag": "button", "text": "Click here", "xpath": "//button[text()='Click here']"},
            {"tag": "a", "text": "Click here for more info", "xpath": "//a[contains(text(),'Click here')]"}
        ]

    Raises:
        Exception: If search fails.
    """
    try:
        page = await browser_manager.get_current_page()

        if exact_match:
            elements = await page.locator(f"text={text}").all()
        else:
            elements = await page.locator(f"text={text}").all()

        result = []
        for i, elem in enumerate(elements):
            try:
                tag = await elem.evaluate("e => e.tagName")
                elem_text = await elem.inner_text()

                result.append({"tag": tag, "text": elem_text, "index": i})
            except Exception:
                continue

        return result

    except Exception as e:
        error_msg = f"Failed to find elements by text '{text}': {str(e)}"
        return [{"error": error_msg}]


@mcp.tool()
async def get_page_structure() -> Dict[str, Any]:
    """
    Analyzes and returns the structure of the current page.

    Extracts the main structural elements of the page including headings,
    links count, forms, and other metadata.

    Returns:
        dict: A dictionary containing:
              - title (str): Page title.
              - headings (list): List of heading texts (h1-h6).
              - link_count (int): Number of links.
              - form_count (int): Number of forms.
              - image_count (int): Number of images.
              - button_count (int): Number of buttons.

    Examples:
        >>> await get_page_structure()
        {
            "title": "My Page",
            "headings": ["Welcome", "Features", "Pricing"],
            "link_count": 25,
            "form_count": 2,
            "image_count": 10,
            "button_count": 5
        }

    Raises:
        Exception: If structure analysis fails.
    """
    try:
        page = await browser_manager.get_current_page()

        structure = await page.evaluate(
            """() => {
            return {
                title: document.title,
                headings: [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')].map(h => h.textContent),
                link_count: document.querySelectorAll('a').length,
                form_count: document.querySelectorAll('form').length,
                image_count: document.querySelectorAll('img').length,
                button_count: document.querySelectorAll('button').length
            }
        }"""
        )

        return structure

    except Exception as e:
        error_msg = f"Failed to get page structure: {str(e)}"
        return {"error": error_msg}


# ============================================================================
# Cookie Management Tools
# ============================================================================


@mcp.tool()
async def get_cookies() -> List[Dict[str, Any]]:
    """
    Retrieves all cookies from the current browser context.

    Returns all cookies stored for the current page/domain.

    Returns:
        list: List of cookie dictionaries, each containing:
              - name (str): Cookie name.
              - value (str): Cookie value.
              - domain (str): Cookie domain.
              - path (str): Cookie path.
              - expires (float): Expiration timestamp (-1 for session).
              - httpOnly (bool): HTTP-only flag.
              - secure (bool): Secure flag.
              - sameSite (str): SameSite attribute.

    Examples:
        >>> await get_cookies()
        [
            {"name": "session", "value": "abc123", "domain": ".example.com", ...},
            {"name": "user", "value": "john", "domain": ".example.com", ...}
        ]

    Raises:
        Exception: If cookie retrieval fails.
    """
    try:
        context = await browser_manager.get_context()
        cookies = await context.cookies()

        return cookies

    except Exception as e:
        error_msg = f"Failed to get cookies: {str(e)}"
        return [{"error": error_msg}]


@mcp.tool()
async def set_cookie(
    name: str, value: str, domain: str, path: str = "/", expires: Optional[float] = None
) -> str:
    """
    Sets a cookie in the current browser context.

    Creates or updates a cookie with the specified parameters.

    Args:
        name (str): Cookie name. Example: "session", "user_id".
        value (str): Cookie value. Example: "abc123", "user@example.com".
        domain (str): Cookie domain. Example: ".example.com", "www.example.com".
        path (str): Cookie path. Default is "/".
        expires (float, optional): Expiration timestamp (Unix timestamp).
                                  If None, creates a session cookie.

    Returns:
        str: Success message, or error message if setting fails.

    Examples:
        >>> await set_cookie("session", "abc123", ".example.com")
        "Set cookie: session=abc123"
        >>> await set_cookie("user", "john", "www.example.com", path="/profile")
        "Set cookie: user=john"

    Raises:
        Exception: If cookie setting fails.
    """
    try:
        context = await browser_manager.get_context()

        cookie_data = {"name": name, "value": value, "domain": domain, "path": path}

        if expires:
            cookie_data["expires"] = expires

        await context.add_cookies([cookie_data])

        return f"Set cookie: {name}={value}"

    except Exception as e:
        error_msg = f"Failed to set cookie '{name}': {str(e)}"
        return error_msg


@mcp.tool()
async def clear_cookies() -> str:
    """
    Clears all cookies from the current browser context.

    Removes all stored cookies for the current context.

    Returns:
        str: Success message, or error message if clearing fails.

    Examples:
        >>> await clear_cookies()
        "Cleared all cookies"

    Raises:
        Exception: If clearing fails.
    """
    try:
        context = await browser_manager.get_context()
        await context.clear_cookies()

        return "Cleared all cookies"

    except Exception as e:
        error_msg = f"Failed to clear cookies: {str(e)}"
        return error_msg


# ============================================================================
# Additional Utility Tools
# ============================================================================


@mcp.tool()
async def get_page_url() -> str:
    """
    Returns the URL of the current page.

    A quick utility to get the current page URL without full browser state.

    Returns:
        str: The current page URL, or error message.

    Examples:
        >>> await get_page_url()
        "https://www.example.com/page"

    Raises:
        Exception: If URL retrieval fails.
    """
    try:
        page = await browser_manager.get_current_page()
        url = page.url
        return url

    except Exception as e:
        error_msg = f"Failed to get page URL: {str(e)}"
        return error_msg


@mcp.tool()
async def get_page_title() -> str:
    """
    Returns the title of the current page.

    A quick utility to get the current page title.

    Returns:
        str: The current page title, or error message.

    Examples:
        >>> await get_page_title()
        "Welcome to My Website"

    Raises:
        Exception: If title retrieval fails.
    """
    try:
        page = await browser_manager.get_current_page()
        title = await page.title()
        return title

    except Exception as e:
        error_msg = f"Failed to get page title: {str(e)}"
        return error_msg


@mcp.tool()
async def get_html_source() -> str:
    """
    Returns the complete HTML source code of the current page.

    Retrieves the full HTML markup of the page as currently rendered.

    Returns:
        str: The complete HTML source code, truncated if too large.

    Examples:
        >>> await get_html_source()
        "<!DOCTYPE html><html><head>...</head><body>...</body></html>"

    Raises:
        Exception: If source retrieval fails.
    """
    try:
        page = await browser_manager.get_current_page()
        html = await page.content()

        # Truncate if too large
        max_length = 100000
        if len(html) > max_length:
            html = html[:max_length] + f"\n... [truncated, total {len(html)} chars]"

        return html

    except Exception as e:
        error_msg = f"Failed to get HTML source: {str(e)}"
        return error_msg


@mcp.tool()
async def wait_for_timeout(milliseconds: int) -> str:
    """
    Pauses execution for a specified duration.

    A simple delay utility. Use sparingly - prefer wait_for_element or wait_for_navigation.

    Args:
        milliseconds (int): Duration to wait in milliseconds.
                           Example: 1000 (1 second), 5000 (5 seconds).

    Returns:
        str: Success message after waiting completes.

    Examples:
        >>> await wait_for_timeout(1000)
        "Waited for 1000 milliseconds"
        >>> await wait_for_timeout(5000)
        "Waited for 5000 milliseconds"

    Raises:
        Exception: If wait fails.
    """
    try:
        page = await browser_manager.get_current_page()
        await page.wait_for_timeout(milliseconds)

        return f"Waited for {milliseconds} milliseconds"

    except Exception as e:
        error_msg = f"Failed to wait: {str(e)}"
        return error_msg


@mcp.tool()
async def close_browser() -> str:
    """
    Closes the browser and cleans up all resources.

    Terminates the browser session and closes all tabs. Use this when done
    with browser operations.

    Returns:
        str: Success message, or error message if closing fails.

    Examples:
        >>> await close_browser()
        "Browser closed successfully"

    Raises:
        Exception: If closing fails.
    """
    try:
        await browser_manager.close()

        return "Browser closed successfully"

    except Exception as e:
        error_msg = f"Failed to close browser: {str(e)}"
        return error_msg


if __name__ == "__main__":
    mcp.run()

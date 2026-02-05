"""
WeChat Official Account Search MCP Server

This module provides tools for searching and retrieving content from
WeChat Official Accounts via Sogou WeChat Search.
"""

from typing import Annotated, List, Dict, Optional
from urllib.parse import quote

import requests
from lxml import html
from mcp.server.fastmcp import FastMCP

# Constants
SOGOU_WECHAT_SEARCH_URL = "https://weixin.sogou.com/weixin"
WECHAT_MP_URL_PREFIX = "https://mp."
REQUEST_TIMEOUT = 10
MAX_RETRY_TIMES = 3


# HTTP Headers
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
}

SOGOU_HEADERS = {
    **DEFAULT_HEADERS,
    "Cookie": "ABTEST=7|1750756616|v1; SUID=0A5BF4788E52A20B00000000685A6D08; IPLOC=CN1100; SUID=605BF4783954A20B00000000685A6D08; SUV=006817F578F45BFE685A6D0B913DA642; SNUID=B3E34CC0B8BF80F5737E3561B9B78454; ariaDefaultTheme=undefined",
}

ARTICLE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
}


class WeChatSearchError(Exception):
    """Custom exception for WeChat search errors."""
    pass


class WeChatContentExtractor:
    """Extractor for WeChat Official Account content."""

    @staticmethod
    def extract_real_url(sogou_url: str) -> str:
        """
        Extract real WeChat article URL from Sogou redirect URL.

        Args:
            sogou_url: Sogou WeChat search result URL

        Returns:
            Real WeChat MP article URL

        Example:
            >>> extractor = WeChatContentExtractor()
            >>> url = extractor.extract_real_url("https://weixin.sogou.com/...")
            >>> print(url)
            "https://mp.weixin.qq.com/..."
        """
        try:
            response = requests.get(
                sogou_url, headers=SOGOU_HEADERS, timeout=REQUEST_TIMEOUT
            )

            script_content = response.text
            url_parts = []

            # Extract URL parts from JavaScript code
            start_index = script_content.find("url += '") + len("url += '")
            while True:
                part_start = script_content.find("url += '", start_index)
                if part_start == -1:
                    break
                part_end = script_content.find("'", part_start + len("url += '"))
                part = script_content[part_start + len("url += '") : part_end]
                url_parts.append(part)
                start_index = part_end + 1

            full_url = "".join(url_parts).replace("@", "")
            real_url = WECHAT_MP_URL_PREFIX + full_url

            return real_url

        except requests.RequestException:
            return ""
        except Exception:
            return ""

    @staticmethod
    def extract_article_content(real_url: str, referer: Optional[str] = None) -> str:
        """
        Extract article content from WeChat MP article URL.

        Args:
            real_url: Real WeChat MP article URL
            referer: Optional referer URL for the request

        Returns:
            Article content as plain text

        Example:
            >>> extractor = WeChatContentExtractor()
            >>> content = extractor.extract_article_content(
            ...     "https://mp.weixin.qq.com/...",
            ...     referer="https://weixin.sogou.com/..."
            ... )
        """
        headers = ARTICLE_HEADERS.copy()
        if referer:
            headers["referer"] = referer

        try:
            response = requests.get(
                real_url, headers=headers, timeout=REQUEST_TIMEOUT
            )
            tree = html.fromstring(response.text)

            # Extract text content from article body
            content_elements = tree.xpath("//div[@id='js_content']//text()")
            cleaned_content = [text.strip() for text in content_elements if text.strip()]
            main_content = "\n".join(cleaned_content)

            return main_content

        except requests.RequestException as e:
            return f"Failed to fetch article content: {e}"
        except Exception as e:
            return f"Unexpected error extracting article content: {e}"


class SogouWeChatSearcher:
    """Searcher for Sogou WeChat search engine."""

    @staticmethod
    def search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search WeChat Official Accounts via Sogou WeChat Search.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, link, real_url, and publish_time

        Example:
            >>> searcher = SogouWeChatSearcher()
            >>> results = searcher.search("Python tutorial", max_results=5)
            >>> print(len(results))
            5
        """
        headers = DEFAULT_HEADERS.copy()
        headers["Referer"] = f"https://weixin.sogou.com/weixin?query={quote(query)}"

        params = {
            "type": "2",
            "s_from": "input",
            "query": query,
            "ie": "utf8",
            "_sug_": "n",
            "_sug_type_": "",
        }

        try:
            response = requests.get(
                SOGOU_WECHAT_SEARCH_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code != 200:
                return []

            tree = html.fromstring(response.text)
            results = SogouWeChatSearcher._parse_search_results(tree)

            return results[:max_results]

        except requests.RequestException:
            return []
        except Exception:
            return []

    @staticmethod
    def _parse_search_results(tree) -> List[Dict[str, str]]:
        """
        Parse search results from HTML tree.

        Args:
            tree: lxml HTML tree

        Returns:
            List of parsed search results
        """
        elements = tree.xpath("//a[contains(@id, 'sogou_vr_11002601_title_')]")
        publish_time_elements = tree.xpath(
            "//li[contains(@id, 'sogou_vr_11002601_box_')]"
            "/div[@class='txt-box']/div[@class='s-p']/span[@class='s2']"
        )

        results = []
        extractor = WeChatContentExtractor()

        for element, time_elem in zip(elements, publish_time_elements):
            title = element.text_content().strip()
            link = element.get("href")

            # Fix relative URLs
            if link and not link.startswith("http"):
                link = "https://weixin.sogou.com" + link

            # Extract real URL
            real_url = extractor.extract_real_url(link)
            publish_time = time_elem.text_content().strip()

            results.append(
                {
                    "title": title,
                    "link": link,
                    "real_url": real_url,
                    "publish_time": publish_time,
                }
            )

        return results


def sogou_weixin_search(
    query: Annotated[str, "Search keyword for WeChat Official Accounts"]
) -> List[Dict[str, str]]:
    """
    Search WeChat Official Accounts and return result list with real URLs.

    This is a legacy function for backward compatibility.
    Use SogouWeChatSearcher.search() instead.

    Args:
        query: Search keyword

    Returns:
        List of search results with title, link, real_url, and publish_time
    """
    searcher = SogouWeChatSearcher()
    return searcher.search(query)


def get_real_url_from_sogou(sogou_url: str) -> str:
    """
    Extract real WeChat article URL from Sogou link.

    This is a legacy function for backward compatibility.
    Use WeChatContentExtractor.extract_real_url() instead.

    Args:
        sogou_url: Sogou WeChat link

    Returns:
        Real WeChat article URL
    """
    extractor = WeChatContentExtractor()
    return extractor.extract_real_url(sogou_url)


def get_article_content(real_url: str, referer: Optional[str] = None) -> str:
    """
    Get WeChat Official Account article content.

    This is a legacy function for backward compatibility.
    Use WeChatContentExtractor.extract_article_content() instead.

    Args:
        real_url: Real WeChat article URL
        referer: Optional referer URL

    Returns:
        Article content as plain text
    """
    extractor = WeChatContentExtractor()
    return extractor.extract_article_content(real_url, referer)


# Initialize FastMCP server
mcp = FastMCP("WeChat Official Account Search")


@mcp.tool()
def wechat_search(
    query: Annotated[str, "Search keyword for WeChat Official Accounts"],
) -> List[Dict[str, str]]:
    """
    Search WeChat Official Accounts via Sogou WeChat Search.

    Args:
        query: Search keyword

    Returns:
        List of search results containing title, link, real_url, and publish_time

    Example:
        >>> results = weixin_search("AI technology")
        >>> print(results[0]["title"])
        "Latest AI Technology Trends"
    """
    searcher = SogouWeChatSearcher()
    return searcher.search(query)


@mcp.tool()
def get_wechat_article_content(
    real_url: Annotated[str, "Real WeChat Official Account article URL"],
    referer: Annotated[
        Optional[str], "Request source, should be the link from wechat_search result"
    ] = None,
) -> str:
    """
    Get the main content of a WeChat Official Account article.

    Args:
        real_url: Real WeChat Official Account article URL
        referer: Optional referer URL, should be the link from wechat_search result

    Returns:
        Article content as plain text

    Example:
        >>> content = get_wechat_article_content(
        ...     "https://mp.weixin.qq.com/...",
        ...     referer="https://weixin.sogou.com/..."
        ... )
        >>> print(content)
        "Article content here..."
    """
    extractor = WeChatContentExtractor()
    return extractor.extract_article_content(real_url, referer)


if __name__ == "__main__":
    mcp.run()

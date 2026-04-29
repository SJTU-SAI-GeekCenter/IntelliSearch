import httpx
import os
import http.client
import json
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

mcp = FastMCP("web-search")


@mcp.tool()
async def web_search_chinese(query: str) -> str:
    """
    【中文专属网页搜索】Search the internet for content for Chinese.
    此工具专用于搜索**中文网页**内容，并且**强制要求**输入的查询（query）必须是**中文**。
    请勿用于搜索英文或其他语言的内容，否则可能导致搜索失败或结果不准确。
    此工具返回的是搜索结果的摘要，而非原始网页的完整内容。
    
    Args:
        query: 必须是中文的搜索内容。
        
    Returns:
        一个包含中文搜索结果摘要的字符串，各个结果之间用三个换行符分隔。
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://open.bigmodel.cn/api/paas/v4/tools",
            headers={"Authorization": os.getenv("ZHIPU_API_KEY")},
            json={
                "tool": "web-search-pro",
                "messages": [{"role": "user", "content": query}],
                "stream": False,
            },
        )

        res_data = []
        for choice in response.json()["choices"]:
            for message in choice["message"]["tool_calls"]:
                search_results = message.get("search_result")
                if not search_results:
                    continue
                for result in search_results:
                    res_data.append(result["content"])

        return "\n\n\n".join(res_data)


@mcp.tool()
def google_search(query: str) -> str:
    """
    [General Web Search via Google] Perform a broad, general web search (Google Search) for any topic in any language.
    
    This is the **primary search tool** and should be used first to identify relevant web pages.
    It returns a structured JSON object containing snippets (summaries), titles, and crucially, the **URLs (web links)** of matching results.
    
    **AI Usage Guideline:**
    1.  Use this function to find the relevant URL(s) for a given query.
    2.  Once you have a specific URL of interest, you **must** pass that URL to the `web_parse` function to retrieve the full content of that page for detailed analysis.
    
    Args:
        query: The search query, which can be in any language (English, Chinese, etc.).
        
    Returns:
        A JSON string containing the search results, including snippets, titles, and the essential web links (URLs).
    """
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    conn.request("POST", "/search", payload, headers)
    data = conn.getresponse().read().decode("utf-8")
    return data


@mcp.tool()
def web_parse(url: str) -> str:
    """
    [Specific Web Page Content Extractor] Fetch and extract the full, clean text content from a specific web page given its URL.
    
    This tool is designed for deep content retrieval. It takes a complete URL and returns the entire, main body content of that page, stripped of irrelevant elements like headers, footers, and advertisements.
    
    **AI Usage Guideline (Recommended Workflow):**
    1.  **DO NOT** use this function for general searching.
    2.  First, call `Google Search` with your keywords to get a list of potential URLs.
    3.  Then, call `web_parse` using a specific URL retrieved from the `Google Search` output to get the complete text for summary or detailed fact-checking.
    
    Args:
        url: The complete, absolute URL of the page to scrape (e.g., 'https://www.example.com/article-title').
        
    Returns:
        A JSON string containing the full, readable content of the specified URL.
    """
    conn = http.client.HTTPSConnection("scrape.serper.dev")
    payload = json.dumps({"url": url})
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    conn.request("POST", "/", payload, headers)
    data = conn.getresponse().read().decode("utf-8")
    return data


@mcp.tool()
def tavily_search(query: str, search_depth: str = "basic", topic: str = "general", max_results: int = 5) -> str:
    """
    [Tavily Web Search] Perform a web search using Tavily, an AI-optimized search engine.

    Returns comprehensive search results including titles, URLs, content snippets, and relevance scores.
    Tavily results are optimized for LLM consumption and include clean, relevant content.

    **AI Usage Guideline:**
    1.  Use this as an alternative to `google_search` for general web queries.
    2.  Results include content snippets directly, but for full page content use `tavily_extract` or `web_parse`.

    Args:
        query: The search query, which can be in any language.
        search_depth: Search depth - "basic" (fast, 1 credit) or "advanced" (thorough, 2 credits). Defaults to "basic".
        topic: Search topic category - "general", "news", or "finance". Defaults to "general".
        max_results: Maximum number of results to return (1-20). Defaults to 5.

    Returns:
        A JSON string containing search results with titles, URLs, content, and relevance scores.
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=query,
        search_depth=search_depth,
        topic=topic,
        max_results=max_results,
    )
    return json.dumps(response, ensure_ascii=False)


@mcp.tool()
def tavily_extract(urls: list[str], query: str = "") -> str:
    """
    [Tavily Content Extractor] Extract clean, readable content from one or more web page URLs using Tavily.

    This tool retrieves the full content of specified web pages, stripped of irrelevant elements.
    It can be used as an alternative to `web_parse` for extracting page content.

    **AI Usage Guideline:**
    1.  Use after `tavily_search` or `google_search` to get full content from specific URLs.
    2.  Optionally provide a query to rerank extracted content chunks by relevance.
    3.  Accepts up to 20 URLs at once for batch extraction.

    Args:
        urls: A list of URLs to extract content from (max 20).
        query: Optional query to rerank extracted chunks by relevance.

    Returns:
        A JSON string containing the extracted content for each URL.
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    kwargs = {"urls": urls}
    if query:
        kwargs["query"] = query
    response = client.extract(**kwargs)
    return json.dumps(response, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
from mcp.server.fastmcp import FastMCP
import httpx
import os
import http.client
import json

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


if __name__ == "__main__":
    mcp.run()
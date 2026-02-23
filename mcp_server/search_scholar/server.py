import os
import http.client
import json
import arxiv
import httpx
import asyncio
from typing import List, Dict, Union
from mcp.server.fastmcp import FastMCP


client = arxiv.Client()
mcp = FastMCP("scholar-search")


@mcp.tool()
def arxiv_search_by_author(author_name: str, max_results: int = 5) -> List[Dict]:
    """
    根据作者姓名搜索 arXiv 论文。

    Args:
        author_name: 要搜索的作者全名 (例如: "Geoffrey Hinton")。
        max_results: 返回的最大结果数量，默认为 5。

    Returns:
        包含搜索结果摘要 (标题, 作者, ID, URL) 的字典列表。
    !ATTENTION! You can read the pdf url with web parse tools after you have searched the pdf_url
    """
    search = arxiv.Search(
        query=f"au:{author_name}",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    results = client.results(search)
    formatted_results = []

    for result in results:
        formatted_results.append(
            {
                "标题": result.title,
                "作者": [a.name for a in result.authors],
                "发表日期": result.published.strftime("%Y-%m-%d"),
                "摘要开头": result.summary.replace("\n", " "),
                "URL": result.entry_id,
                "pdf": str(result.entry_id).replace("abs", "pdf"),
            }
        )

    return formatted_results


@mcp.tool()
def arxiv_search_by_content(query_string: str, max_results: int = 5) -> List[Dict]:
    """
    根据文章内容（标题、摘要或主题）搜索 arXiv 论文。

    Args:
        query_string: 搜索关键字 (例如: "Large Language Model efficiency")。
        max_results: 返回的最大结果数量，默认为 5。

    Returns:
        包含搜索结果摘要 (标题, 作者, ID, URL) 的字典列表。
    !ATTENTION! You can read the pdf url with web parse tools after you have searched the pdf_url
    """
    search = arxiv.Search(
        query=query_string,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = client.results(search)
    formatted_results = []

    for result in results:
        formatted_results.append(
            {
                "标题": result.title,
                "作者": [a.name for a in result.authors],
                "发表日期": result.published.strftime("%Y-%m-%d"),
                "摘要开头": result.summary,
                "pdf": str(result.entry_id).replace("abs", "pdf"),
                "URL": result.entry_id,
            }
        )

    return formatted_results


@mcp.tool()
def google_scholar_search(query: str) -> str:
    """perform google scholar search with query provided.

    Args:
        query (str): Your query, you can search the name of the paper, or the name of the authors!

    Returns:
        str: return the detailed paper list for the most relevant search result.
    !ATTENTION! You can read the pdf url with web parse tools after you have searched the pdf_url
    """
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    conn.request("POST", "/scholar", payload, headers)
    data = conn.getresponse().read().decode("utf-8")
    return data


# dblp内部辅助函数
def _safe_str(val: Union[str, List, None]) -> str:
    """Helper to handle DBLP's inconsistent XML-to-JSON list/string conversion."""
    if val is None:
        return ""
    if isinstance(val, list):
        return str(val[0]) if val else ""
    return str(val)


async def _fetch_dblp(api_url: str, query: str, max_results: int) -> List[Dict]:
    """Internal helper to execute the HTTP request with exponential backoff retry."""
    max_retries = 3
    base_delay = 1.0
    params = {"q": query, "h": max_results, "format": "json"}

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params=params, timeout=20.0)
                response.raise_for_status()
                data = response.json()
                try:
                    return data["result"]["hits"]["hit"]
                except (KeyError, TypeError):
                    return []
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)

    return []


@mcp.tool()
async def search_dblp_papers(query: str, max_results: int = 5) -> str:
    """
    [Search Papers] Search for Computer Science research papers, theses, and articles on DBLP.

    Use this tool to find bibliographic details, citations, publication venues, and DOI links.
    It returns structured information including Title, Authors, Venue/Journal, Year, and Document Type.

    Args:
        query: The search keywords (e.g., "Diffusion Model", "Attention is all you need").
        max_results: Max number of papers to return (default 5).

    Returns:
        A string containing multiple search results separated by '---'.
        Each result includes: Title, Authors, Venue (with Year), Type, and Link.
    """
    url = "https://dblp.org/search/publ/api"
    hits = await _fetch_dblp(url, query, max_results)

    if not hits:
        return f"No papers found for query: '{query}'"

    formatted_output = []
    for hit in hits:
        info = hit.get("info", {})
        url_link = info.get("url", "No URL")

        title = _safe_str(info.get("title", "Unknown Title"))
        year = _safe_str(info.get("year", "Unknown Year"))
        doi_link = _safe_str(info.get("ee", url_link))
        pub_type = _safe_str(info.get("type", "Unknown Type"))
        venue_raw = info.get("venue")
        if venue_raw:
            venue_str = f"{_safe_str(venue_raw)} ({year})"
        else:
            venue_str = f"{pub_type} ({year})"  # 针对 Thesis 等无 Venue 情况

        # 作者处理
        authors_data = info.get("authors", {}).get("author", [])
        names = []
        if isinstance(authors_data, dict):
            names.append(authors_data.get("text", ""))
        elif isinstance(authors_data, list):
            for a in authors_data:
                names.append(a.get("text", "") if isinstance(a, dict) else str(a))
        authors_str = ", ".join(names) if names else "Unknown Authors"

        entry = (
            f"[Paper] {title}\n"
            f"Authors: {authors_str}\n"
            f"Venue: {venue_str}\n"
            f"Type: {pub_type}\n"
            f"Link: {doi_link}"
        )
        formatted_output.append(entry)

    return "\n\n---\n\n".join(formatted_output)


@mcp.tool()
async def search_dblp_authors(query: str, max_results: int = 5) -> str:
    """
    [Search Authors] Find researcher profiles, affiliations, and awards in Computer Science.

    Use this tool when the user asks about a specific person (e.g., "Who is Yann LeCun?", "Which university is X from?").
    It parses 'notes' to extract affiliations and awards (e.g., Turing Award).

    Args:
        query: The researcher's name (e.g., "Yann LeCun", "Geoffrey Hinton").
        max_results: Max number of authors to return (default 5).

    Returns:
        A formatted string containing matching author profiles, including Name, Context (Affiliations/Awards), and Profile Link.
    """
    url = "https://dblp.org/search/author/api"
    hits = await _fetch_dblp(url, query, max_results)

    if not hits:
        return f"No authors found for query: '{query}'"

    formatted_output = []
    for hit in hits:
        info = hit.get("info", {})
        author_name = _safe_str(info.get("author", "Unknown Name"))
        url_link = info.get("url", "No URL")

        # 解析 Notes (机构/奖项)
        notes_raw = info.get("notes", {}).get("note", [])
        notes_list = (
            [notes_raw]
            if isinstance(notes_raw, dict)
            else (notes_raw if isinstance(notes_raw, list) else [])
        )
        affiliations = [
            n.get("text", "") for n in notes_list if isinstance(n, dict) and "text" in n
        ]

        notes_str = f"Context: {'; '.join(affiliations)}\n" if affiliations else ""

        entry = (
            f"[Author] {author_name}\n" f"{notes_str}" f"Profile: {url_link}"
        )
        formatted_output.append(entry)

    return "\n\n---\n\n".join(formatted_output)


@mcp.tool()
async def search_dblp_venues(query: str, max_results: int = 5) -> str:
    """
    [Search Venues] Find details about conferences and journals (e.g., CVPR, Nature).

    Use this tool to check conference full names, acronyms, or publication types.

    Args:
        query: The venue name or acronym (e.g., "CVPR", "ICLR", "IEEE Transactions").
        max_results: Max number of venues to return (default 5).

    Returns:
        A formatted string containing matching venues, including Name, Acronym, and Type (Conference/Journal).
    """
    url = "https://dblp.org/search/venue/api"
    hits = await _fetch_dblp(url, query, max_results)

    if not hits:
        return f"No venues found for query: '{query}'"

    formatted_output = []
    for hit in hits:
        info = hit.get("info", {})
        url_link = info.get("url", "No URL")

        venue_name = _safe_str(info.get("venue", "Unknown Venue"))
        acronym = _safe_str(info.get("acronym", ""))
        venue_type = _safe_str(info.get("type", "Conference/Journal"))

        if acronym and acronym not in venue_name:
            display_name = f"{venue_name} ({acronym})"
        else:
            display_name = venue_name

        entry = (
            f"[Venue] {display_name}\n"
            f"Type: {venue_type}\n"
            f"Link: {url_link}"
        )
        formatted_output.append(entry)

    return "\n\n---\n\n".join(formatted_output)


if __name__ == "__main__":
    mcp.run()

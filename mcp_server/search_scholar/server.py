from mcp.server.fastmcp import FastMCP
import os
import http.client
import json
import arxiv
from typing import List, Dict

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
def scholar_search(query: str) -> str:
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


if __name__ == "__main__":
    mcp.run()
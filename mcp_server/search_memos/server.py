"""
SAI-LocalSearch MCP Server

This module provides an MCP server for searching the SAI local knowledge base,
which is specifically built for Shanghai Jiao Tong University AI Institute students.
The system queries the MemOS intelligent memory system to retrieve relevant
information from a million-word high-quality local database.

Environment Variables Required:
    - MEMOS_API_KEY: Authentication token for MemOS API
    - MEMOS_BASE_URL: Base URL for MemOS API endpoints
"""

import os
import uuid
import json
import requests

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Memos-RemoteSearch")


@mcp.tool()
def search_sai(query: str, conversation_id: str = None):
    """
    Search the SAI local knowledge base via MemOS API.

    This function queries the MemOS intelligent memory system to retrieve relevant
    information from the SAI local database. The database contains high-quality
    content specifically curated for Shanghai Jiao Tong University AI Institute,
    built through an automated pipeline processing millions of words.

    Args:
        query: The search query string to query the knowledge base.
        conversation_id: Optional conversation ID for context tracking.
                        If not provided, a new UUID will be generated.
                        Useful for maintaining conversation context across
                        multiple queries in the same session.

    Returns:
        str: The search results as a formatted JSON string with proper
        Unicode encoding and indentation.

    Usage Note:
        This tool is particularly effective for questions related to
        Shanghai Jiao Tong University AI Institute. Priority should be
        given to this tool when users ask about SAI-related topics.

    Example:
        >>> search_sai("What are the admission requirements for SAI?")
        >>> search_sai("Tell me about SAI research labs",
        ...            conversation_id="conv_12345")
    """
    user_id = os.environ["MEMOS_USER_ID"]
    # Generate conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Build request payload
    data = {
        "query": query,
        "user_id": user_id,
        "conversation_id": conversation_id,
    }

    # Prepare authentication headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {os.environ['MEMOS_API_KEY']}",
    }

    # Send POST request to MemOS search endpoint
    url = f"{os.environ['MEMOS_BASE_URL']}/search/memory"
    res = requests.post(url=url, headers=headers, data=json.dumps(data))

    # Return formatted search results
    result = res.json()
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()

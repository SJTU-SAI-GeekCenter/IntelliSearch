"""Bilibili Video Search MCP Server.

This server provides MCP tools for searching and retrieving information
from Bilibili, including video search, subtitle extraction, and video metadata.

Environment Variables Required:
    BILIBILI_SESSDATA: Bilibili session data for authentication
    BILIBILI_BILI_JCT: Bilibili CSRF token
    BILIBILI_BUVID3: Bilibili browser fingerprint

Features:
    - Search videos by keyword with pagination
    - Extract AI-generated subtitles from videos
    - Retrieve detailed video information
    - Automatic speech recognition (ASR) for videos without subtitles
"""

import os
import aiohttp
from typing import Dict, Any
from bilibili_api import video, Credential, search
from mcp.server.fastmcp import FastMCP
from bcut_asr import get_audio_subtitle

# Initialize FastMCP server
mcp = FastMCP("bilibili-search")

# Load credentials from environment variables
SESSDATA = os.getenv("BILIBILI_SESSDATA")
BILI_JCT = os.getenv("BILIBILI_BILI_JCT")
BUVID3 = os.getenv("BILIBILI_BUVID3")

# Initialize Bilibili credential
credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)


@mcp.tool()
async def search_video(keyword: str, page: int = 1, page_size: int = 20) -> str:
    """Search for videos on Bilibili by keyword.

    This tool searches the Bilibili platform for videos matching the given keyword
    and returns a formatted table with video metadata including title, author,
    duration, view count, likes, category, and publication date.

    When to use:
        - User asks to find videos about a specific topic on Bilibili
        - Searching for tutorials, reviews, or entertainment content
        - Finding video resources for learning or research

    Features:
        - Full-text search across video titles and descriptions
        - Pagination support for large result sets
        - Sorted by relevance
        - Returns clickable Markdown links to videos

    Args:
        keyword (str): Search query string.
                       Examples: "machine learning tutorial", "python 入门", "游戏攻略"
        page (int, optional): Page number for pagination (1-indexed).
                              Default: 1
                              Recommended range: 1-10
        page_size (int, optional): Number of results per page.
                                   Default: 20
                                   Recommended range: 10-50
                                   Maximum: 50

    Returns:
        str: Formatted Markdown table with columns:
             - Publish Date
             - Title (clickable link)
             - Author (UP主)
             - Duration
             - View Count
             - Like Count
             - Category
             - BV ID

    Examples:
        >>> # Basic search
        >>> await search_video("人工智能")

        >>> # Search with pagination
        >>> await search_video("深度学习", page=2, page_size=30)

        >>> # Search for specific content
        >>> await search_video("Python教程", page=1, page_size=20)

    Notes:
        - Requires valid Bilibili credentials (SESSDATA, BILI_JCT, BUVID3)
        - Search results are sorted by relevance by default
        - View and like counts are updated in real-time
        - Supports both Chinese and English search queries

    See Also:
        get_video_info: Retrieve detailed information about a specific video
        get_video_subtitle: Extract subtitles from a video
    """
    try:
        print(f"Searching Bilibili for: {keyword}")

        # Execute search
        search_result = await search.search_by_type(
            keyword,
            search_type=search.SearchObjectType.VIDEO,
            page=page,
            page_size=page_size,
        )

        if not search_result.get("result"):
            return f"No results found for keyword: {keyword}"

        # Prepare table data
        from tabulate import tabulate
        from datetime import datetime

        table_data = []
        headers = [
            "Publish Date",
            "Title",
            "Author",
            "Duration",
            "Views",
            "Likes",
            "Category",
            "BV ID",
        ]

        for video_info in search_result["result"]:
            # Convert timestamp to readable date
            pubdate = datetime.fromtimestamp(video_info["pubdate"]).strftime("%Y/%m/%d")

            # Create Markdown link
            title_link = f"[{video_info['title']}]({video_info['arcurl']})"

            table_data.append(
                [
                    pubdate,
                    title_link,
                    video_info["author"],
                    video_info["duration"],
                    str(video_info["play"]),
                    str(video_info["like"]),
                    video_info["typename"],
                    video_info["bvid"],
                ]
            )

        # Generate Markdown table
        result = tabulate(table_data, headers=headers, tablefmt="pipe")
        print(f"Found {len(table_data)} results for: {keyword}")

        return result

    except Exception as e:
        print(f"Search failed: {e}")
        return f"Error searching for '{keyword}': {str(e)}"


@mcp.tool()
async def get_video_subtitle(bvid: str) -> Dict[str, Any]:
    """Extract subtitles from a Bilibili video.

    This tool retrieves subtitles from a Bilibili video. It prioritizes
    AI-generated Chinese subtitles, and falls back to automatic speech
    recognition (ASR) if no subtitles are available.

    When to use:
        - User wants to read video content without watching
        - Extracting transcripts for translation or analysis
        - Creating accessible versions of video content
        - Analyzing video content for research

    Features:
        - Prioritizes AI-generated Chinese subtitles (ai-zh)
        - Falls back to ASR for videos without subtitles
        - Returns clean, concatenated subtitle text
        - Handles both subtitle files and ASR processing

    Args:
        bvid (str): Bilibili Video ID (BV号).
                   Format: "BV1xx411c7mX" (11 characters starting with BV)
                   Examples:
                     - "BV1xx411c7mX"
                     - "BV1uv411q7Mv"
                   Can be found in video URLs or from search results

    Returns:
        dict: Subtitle data with the following structure:
            {
                "success": bool,        # True if subtitles extracted
                "text": str,            # Subtitle text content
                "source": str,          # "ai-zh", "asr", or "none"
                "bvid": str,            # Video ID
                "error": str            # Error message if failed
            }

    Examples:
        >>> # Get subtitles for a video
        >>> await get_video_subtitle("BV1xx411c7mX")

    Notes:
        - AI-generated subtitles are preferred (lang: "ai-zh")
        - ASR is used automatically if no subtitles exist
        - ASR processing may take 5-10 seconds
        - Returns empty string if neither subtitles nor ASR are available
        - Requires valid Bilibili credentials

    See Also:
        search_video: Find videos to extract subtitles from
        get_video_info: Get detailed video metadata
    """
    try:
        print(f"Extracting subtitles for video: {bvid}")

        # Initialize video instance
        v = video.Video(bvid=bvid, credential=credential)

        # Get video CID (Content ID)
        cid = await v.get_cid(page_index=0)

        # Get player info to check for subtitles
        info = await v.get_player_info(cid=cid)
        json_files = info.get("subtitle", {}).get("subtitles", [])

        # Try to find AI-generated Chinese subtitles
        target_subtitle = None
        for subtitle in json_files:
            if (
                subtitle.get("lan") == "ai-zh"
                and subtitle.get("lan_doc") == "中文(自动生成)"
            ):
                target_subtitle = subtitle
                break

        # Case 1: AI-generated subtitles exist
        if target_subtitle:
            print(f"Found AI-generated subtitles for {bvid}")

            subtitle_url = target_subtitle["subtitle_url"]
            if not subtitle_url.startswith(("http://", "https://")):
                subtitle_url = f"https:{subtitle_url}"

            # Fetch subtitle content
            async with aiohttp.ClientSession() as session:
                async with session.get(subtitle_url) as response:
                    subtitle_content = await response.json()

                    if "body" in subtitle_content:
                        # Extract and concatenate all subtitle segments
                        subtitle_text = "".join(
                            item["content"] for item in subtitle_content["body"]
                        )
                        return {
                            "success": True,
                            "text": subtitle_text,
                            "source": "ai-zh",
                            "bvid": bvid,
                        }
                    else:
                        return {
                            "success": False,
                            "text": "",
                            "source": "none",
                            "bvid": bvid,
                            "error": "Subtitle format not recognized",
                        }

        # Case 2: No AI subtitles, try ASR (Automatic Speech Recognition)
        print(f"No AI subtitles found for {bvid}, attempting ASR")

        # Get video download URL
        url_res = await v.get_download_url(cid=cid)
        audio_arr = url_res.get("dash", {}).get("audio", [])

        if not audio_arr:
            return {
                "success": False,
                "text": "",
                "source": "none",
                "bvid": bvid,
                "error": "No audio track found for ASR",
            }

        # Select best quality audio
        audio = audio_arr[-1]  # Usually highest quality
        audio_url = ""

        # Prefer CDN URLs
        if ".mcdn.bilivideo.cn" in audio["baseUrl"]:
            audio_url = audio["baseUrl"]
        else:
            backup_url = audio.get("backupUrl", [])
            if backup_url and "upos-sz" in backup_url[0]:
                audio_url = audio["baseUrl"]
            else:
                audio_url = backup_url[0] if backup_url else audio["baseUrl"]

        # Process ASR
        print(f"Processing ASR for {bvid}")
        asr_text = get_audio_subtitle(audio_url)

        if isinstance(asr_text, str):
            return {
                "success": True,
                "text": asr_text,
                "source": "asr",
                "bvid": bvid,
            }
        else:
            return {
                "success": False,
                "text": "",
                "source": "asr",
                "bvid": bvid,
                "error": str(asr_text),
            }

    except Exception as e:
        print(f"Failed to extract subtitles for {bvid}: {e}")
        return {
            "success": False,
            "text": "",
            "source": "error",
            "bvid": bvid,
            "error": str(e),
        }


@mcp.tool()
async def get_video_info(bvid: str) -> Dict[str, Any]:
    """Retrieve detailed information about a Bilibili video.

    This tool fetches comprehensive metadata for a specific video including
    title, description, author statistics, publication details, and more.

    When to use:
        - Getting detailed video metadata before watching
        - Retrieving author information and statistics
        - Checking video duration, size, and format details
        - Understanding video context and categorization

    Args:
        bvid (str): Bilibili Video ID (BV号).
                   Examples: "BV1xx411c7mX", "BV1uv411q7Mv"

    Returns:
        dict: Video information with detailed metadata including:
            - title: Video title
            - description: Video description
            - author: Author information (name, ID, avatar)
            - pubdate: Publication timestamp
            - duration: Video duration in seconds
            - view/stat: View, like, coin, favorite counts
            - pic: Thumbnail URL
            - cid: Content ID
            - And many more fields

    Examples:
        >>> # Get video information
        >>> info = await get_video_info("BV1xx411c7mX")
        >>> print(f"Title: {info['title']}")
        >>> print(f"Views: {info['stat']['view']}")

    Notes:
        - Returns complete video metadata as provided by Bilibili API
        - Includes real-time statistics (views, likes, etc.)
        - Contains author profile information
        - Includes video technical details (duration, format, etc.)

    See Also:
        search_video: Find videos and get their BV IDs
        get_video_subtitle: Extract subtitles from the video
    """
    try:
        print(f"Fetching video info for: {bvid}")

        # Initialize video instance
        v = video.Video(bvid=bvid, credential=credential)

        # Get video info
        info = await v.get_info()

        print(f"Successfully fetched info for: {info.get('title', bvid)}")
        return info

    except Exception as e:
        print(f"Failed to fetch video info for {bvid}: {e}")
        return {"error": str(e), "bvid": bvid, "success": False}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

import os
import hmac
import hashlib
import webbrowser
import requests
from tabulate import tabulate
from typing import List, Dict, Any
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Movie and Book Search")

# todo add api calls for TMDB
# https://www.themoviedb.org/settings/api

def get_douban_cookie() -> str:
    """Get Douban cookie from environment variables"""
    cookie = os.getenv("DOUBAN_COOKIE", "")
    return cookie


def get_frodo_sign(url: str, date: str, method: str = "GET") -> str:
    """
    Generate Frodo API signature.

    Args:
        url: The API URL
        date: Date in YYYYMMDD format
        method: HTTP method, default is GET

    Returns:
        Base64 encoded signature
    """
    url_parsed = urlparse(url)
    url_path = url_parsed.path
    raw_sign = f"{method.upper()}&{url_path}&{date}"
    hmac_obj = hmac.new(b"bf7dddc7c9cfe6f7", raw_sign.encode("utf-8"), hashlib.sha1)
    return hmac_obj.digest().decode("latin1")


def get_user_agent() -> str:
    """Get a random user agent from the list"""
    user_agents = [
        "api-client/1 com.douban.frodo/7.22.0.beta9(231) Android/23 product/Mate 40 vendor/HUAWEI model/Mate 40 brand/HUAWEI  rom/android  network/wifi  platform/AndroidPad",
        "api-client/1 com.douban.frodo/7.18.0(230) Android/22 product/MI 9 vendor/Xiaomi model/MI 9 brand/Android  rom/miui6  network/wifi  platform/mobile nd/1",
        "api-client/1 com.douban.frodo/7.1.0(205) Android/29 product/perseus vendor/Xiaomi model/Mi MIX 3  rom/miui6  network/wifi  platform/mobile nd/1",
        "api-client/1 com.douban.frodo/7.3.0(207) Android/22 product/MI 9 vendor/Xiaomi model/MI 9 brand/Android  rom/miui6  network/wifi platform/mobile nd/1",
    ]
    # Use a simple index cycling
    if not hasattr(get_user_agent, "index"):
        get_user_agent.index = 0
    get_user_agent.index = (get_user_agent.index + 1) % len(user_agents)
    return user_agents[get_user_agent.index]


def request_frodo_api(url_path: str) -> Dict[str, Any]:
    """
    Make a request to Frodo API.

    Args:
        url_path: API path

    Returns:
        JSON response as dictionary
    """
    base_url = "https://frodo.douban.com/api/v2"
    full_url = base_url + url_path
    date = datetime.now().strftime("%Y%m%d")

    params = {
        "os_rom": "android",
        "apiKey": "0dad551ec0f84ed02907ff5c42e8ec70",
        "_ts": date,
        "_sig": get_frodo_sign(full_url, date),
    }

    headers = {"user-agent": get_user_agent(), "cookie": get_douban_cookie()}

    response = requests.get(full_url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def format_table(headers: List[str], rows: List[Dict[str, Any]]) -> str:
    """
    使用 tabulate 将数据格式化为 Markdown 表格。
    """
    if not rows:
        return "No data available"

    data = [[row.get(h, "") for h in headers] for row in rows]
    return tabulate(data, headers=headers, tablefmt="github")


# * DOUBAN_SEARCH_TOOLS

@mcp.tool()
def search_book(q: Optional[str] = None, isbn: Optional[str] = None) -> str:
    """
    Search books from Douban, either by ISBN or by query.

    Args:
        q: Query string, e.g. "python"
        isbn: ISBN number, e.g. "9787501524044"

    Returns:
        Formatted book search results
    """
    if not q and not isbn:
        return {"error": "Either q or isbn must be provided"}

    try:
        books = []

        if q:
            # Search by keyword
            url = "https://api.douban.com/v2/book/search"
            params = {"q": q, "apikey": "0ac44ae016490db2204ce0a042db2916"}
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            books = data.get("books", [])

        elif isbn:
            # Search by ISBN
            url = f"https://api.douban.com/v2/book/isbn/{isbn}"
            params = {"apikey": "0ac44ae016490db2204ce0a042db2916"}
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            book = response.json()
            if book.get("id"):
                books = [book]

        # Format results
        headers = ["publish_date", "title", "author", "rating", "id", "isbn"]
        rows = []
        for book in books:
            # Format pubdate
            pubdate = book.get("pubdate", "")
            if pubdate:
                pubdate = (
                    pubdate.replace("年", "-").replace("月", "-").replace("日", "")
                )
                try:
                    pubdate = datetime.strptime(pubdate, "%Y-%m-%d").strftime("%Y/%m")
                except:
                    pass

            # Format rating
            rating = book.get("rating", {})
            rating_str = f"{rating.get('average', 0)} ({rating.get('numRaters', 0)}人)"

            # Format author
            author = "、".join(book.get("author", []))

            rows.append(
                {
                    "publish_date": pubdate,
                    "title": book.get("title", ""),
                    "author": author,
                    "rating": rating_str,
                    "id": book.get("id", ""),
                    "isbn": book.get("isbn13", ""),
                }
            )

        return format_table(headers, rows)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


@mcp.tool()
def list_book_reviews(id: str) -> str:
    """
    List book reviews.

    Args:
        id: Douban book ID, e.g. "1234567890"

    Returns:
        Formatted book reviews
    """
    try:
        data = request_frodo_api(f"/book/{id}/reviews")
        reviews = data.get("reviews", [])

        headers = ["title", "rating", "summary", "id"]
        rows = []

        for review in reviews:
            rating = review.get("rating")
            if rating:
                rating_str = f"{rating.get('value', 0)} ({rating.get('count', 0)}人)"
            else:
                rating_str = "N/A"

            rows.append(
                {
                    "title": review.get("title", ""),
                    "rating": rating_str,
                    "summary": review.get("abstract", ""),
                    "id": review.get("id", ""),
                }
            )

        return format_table(headers, rows)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Get reviews failed: {str(e)}"}


# Movie/TV search tools
@mcp.tool()
def search_movie(q: str) -> str:
    """
    Search movies or TVs from Douban by query.

    Args:
        q: Query string, e.g. "python"

    Returns:
        Formatted movie/TV search results
    """
    try:
        data = request_frodo_api(f"/search/movie?q={q}")
        items = data.get("items", [])
        movies = [item.get("target") for item in items if item.get("target")]

        headers = ["title", "subtitle", "publish_date", "rating", "id"]
        rows = []

        for movie in movies:
            # Format rating
            rating = movie.get("rating", {})
            rating_str = f"{rating.get('value', '0')} ({rating.get('count', 0)}人)"

            rows.append(
                {
                    "title": movie.get("title", ""),
                    "subtitle": movie.get("card_subtitle", ""),
                    "publish_date": movie.get("year", ""),
                    "rating": rating_str,
                    "id": movie.get("id", ""),
                }
            )

        return format_table(headers, rows)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


@mcp.tool()
def list_movie_reviews(id: str) -> str:
    """
    List movie reviews.

    Args:
        id: Douban movie ID, e.g. "1234567890"

    Returns:
        Formatted movie reviews
    """
    try:
        data = request_frodo_api(f"/movie/{id}/reviews")
        reviews = data.get("reviews", [])

        headers = ["title", "rating", "summary", "id"]
        rows = []

        for review in reviews:
            rating = review.get("rating")
            if rating:
                rating_str = (
                    f"{rating.get('value', 0)} (有用:{review.get('useful_count', 0)}人)"
                )
            else:
                rating_str = "N/A"

            rows.append(
                {
                    "title": review.get("title", ""),
                    "rating": rating_str,
                    "summary": review.get("abstract", ""),
                    "id": review.get("id", ""),
                }
            )

        return format_table(headers, rows)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Get reviews failed: {str(e)}"}


@mcp.tool()
def list_tv_reviews(id: str) -> str:
    """
    List TV reviews.

    Args:
        id: Douban TV ID, e.g. "1234567890"

    Returns:
        Formatted TV reviews
    """
    try:
        data = request_frodo_api(f"/tv/{id}/reviews")
        reviews = data.get("reviews", [])

        headers = ["title", "rating", "summary", "id"]
        rows = []

        for review in reviews:
            rating = review.get("rating")
            if rating:
                rating_str = (
                    f"{rating.get('value', 0)} (有用:{review.get('useful_count', 0)}人)"
                )
            else:
                rating_str = "N/A"

            rows.append(
                {
                    "title": review.get("title", ""),
                    "rating": rating_str,
                    "summary": review.get("abstract", ""),
                    "id": review.get("id", ""),
                }
            )

        return format_table(headers, rows)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Get reviews failed: {str(e)}"}


# Browse tool
@mcp.tool()
def browse(id: str) -> str:
    """
    Open default browser and browse Douban book detail.

    Args:
        id: Douban book ID, e.g. "1234567890"

    Returns:
        Confirmation message
    """
    try:
        url = f"https://book.douban.com/subject/{id}/"
        webbrowser.open(url)
        return f"The Douban Book Page has been opened in your default browser"
    except Exception as e:
        return {"error": f"Failed to open browser: {str(e)}"}


# Group topic tools
@mcp.tool()
def list_group_topics(
    id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    from_date: Optional[str] = None,
) -> str:
    """
    List group topics.

    Args:
        id: Douban group ID (default: '732764')
        tags: Tags to filter, e.g. ["python"]
        from_date: Filter topics from this date, e.g. "2024-01-01"

    Returns:
        Formatted group topics
    """
    try:
        group_id = id or "732764"
        data = request_frodo_api(f"/group/{group_id}/topics")

        topics = data.get("topics", [])
        # Filter out ads
        topics = [t for t in topics if not t.get("is_ad", False)]

        # Filter by tags
        if tags:
            topics = [
                t
                for t in topics
                if any(tag.get("name") in tags for tag in t.get("topic_tags", []))
            ]

        # Filter by date
        if from_date:
            try:
                filter_date = datetime.strptime(from_date, "%Y-%m-%d")
                topics = [
                    t
                    for t in topics
                    if datetime.strptime(
                        t.get("create_time", ""), "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    > filter_date
                ]
            except ValueError:
                pass

        headers = ["publish_date", "tags", "title", "id"]
        rows = []

        for topic in topics:
            # Format date
            create_time = topic.get("create_time", "")
            try:
                pub_date = datetime.strptime(
                    create_time, "%Y-%m-%dT%H:%M:%S.%fZ"
                ).strftime("%Y/%m/%d")
            except:
                pub_date = create_time

            # Format tags
            topic_tags = topic.get("topic_tags", [])
            tags_str = "、".join(tag.get("name", "") for tag in topic_tags)

            # Format title with URL
            title = f"[{topic.get('title', '')}]({topic.get('url', '')})"

            rows.append(
                {
                    "publish_date": pub_date,
                    "tags": tags_str,
                    "title": title,
                    "id": topic.get("id", ""),
                }
            )

        return format_table(headers, rows)

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Get topics failed: {str(e)}"}


@mcp.tool()
def get_group_topic_detail(id: str) -> str:
    """
    Get group topic detail.

    Args:
        id: Douban group topic ID, e.g. "1234567890"

    Returns:
        Formatted topic detail
    """
    try:
        topic = request_frodo_api(f"/group/topic/{id}")

        if not topic.get("id"):
            return {"error": "Request failed"}

        # Format tags
        topic_tags = topic.get("topic_tags", [])
        tags_str = "|".join(tag.get("name", "") for tag in topic_tags)

        # Convert HTML to plain text (simple version)
        content = topic.get("content", "")
        # Remove HTML tags (simple implementation)
        import re

        content_plain = re.sub(r"<[^>]+>", "\n", content)
        content_plain = re.sub(r"\n+", "\n", content_plain).strip()

        result = f"title: {topic.get('title', '')}\n"
        result += f"tags: {tags_str}\n"
        result += "content:\n"
        result += content_plain

        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Get topic detail failed: {str(e)}"}


if __name__ == "__main__":
    mcp.run()

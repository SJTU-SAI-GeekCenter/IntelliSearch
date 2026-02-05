import os
import requests
import base64
from mcp.server.fastmcp import FastMCP
from typing import Optional, List, Dict

class GitHubSearchClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}"
        }

    # -------------------------
    # Internal helpers
    # -------------------------
    def _build_query(self, keyword: str, repo: str = None, user: str = None,
                     language: str = None, qualifiers: List[str] = None):
        parts = [keyword]

        if repo:
            parts.append(f"repo:{repo}")
        if user:
            parts.append(f"user:{user}")
        if language:
            parts.append(f"language:{language}")
        if qualifiers:
            parts.extend(qualifiers)

        return "+".join(parts)

    def _request(self, endpoint: str, params: Dict = None):
        url = f"{self.BASE_URL}{endpoint}"
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    # -------------------------
    # Result Normalizer
    # -------------------------
    def _normalize(self, raw: Dict, result_type: str):
        items = []

        for it in raw.get("items", []):
            normalized = {
                "type": result_type,
                "name": it.get("name") or it.get("title"),
                "full_name": it.get("repository", {}).get("full_name") if "repository" in it else it.get("full_name"),
                "url": it.get("html_url"),
                "score": it.get("score"),
                "extra": {}
            }

            if result_type == "code":
                normalized["extra"] = {
                    "path": it.get("path"),
                    "repo": it["repository"]["full_name"],
                }

            elif result_type in ("issue", "pr"):
                normalized["extra"] = {
                    "state": it.get("state"),
                    "number": it.get("number"),
                    "repo": it.get("repository_url", "").replace("https://api.github.com/repos/", "")
                }

            elif result_type == "repo":
                normalized["extra"] = {
                    "stars": it.get("stargazers_count"),
                    "language": it.get("language")
                }

            elif result_type == "user":
                normalized["extra"] = {
                    "id": it.get("id"),
                    "avatar": it.get("avatar_url"),
                }

            items.append(normalized)

        return {"total": raw.get("total_count", 0), "items": items}

    # -------------------------
    # Search: Code
    # -------------------------
    def search_code(self, keyword: str, repo: str = None, user: str = None,
                    language: str = None, path: str = None,
                    per_page: int = 20):
        qualifiers = []
        if path:
            qualifiers.append(f"path:{path}")

        query = self._build_query(keyword, repo, user, language, qualifiers)

        raw = self._request("/search/code", {"q": query, "per_page": per_page})
        return self._normalize(raw, "code")

    # -------------------------
    # Search: Issues / PR
    # -------------------------
    def search_issues(self, keyword: str, repo: str = None, user: str = None,
                      language: str = None, state: str = None,
                      is_pr: bool = False, per_page: int = 20):
        qualifiers = []

        if state:
            qualifiers.append(f"state:{state}")
        qualifiers.append("is:pr" if is_pr else "is:issue")

        query = self._build_query(keyword, repo, user, language, qualifiers)

        raw = self._request("/search/issues", {"q": query, "per_page": per_page})
        return self._normalize(raw, "pr" if is_pr else "issue")

    # PR wrapper
    def search_pr(self, keyword: str, repo: str = None, user: str = None,
                  language: str = None, state: str = None,
                  per_page: int = 20):
        return self.search_issues(
            keyword, repo, user, language, state, is_pr=True, per_page=per_page
        )

    # -------------------------
    # Search: Repositories
    # -------------------------
    def search_repos(self, keyword: str, user: str = None, language: str = None,
                     sort: str = None, order: str = None, per_page: int = 20):
        qualifiers = []

        if user:
            qualifiers.append(f"user:{user}")
        if language:
            qualifiers.append(f"language:{language}")

        query = self._build_query(keyword, qualifiers=qualifiers)

        params = {"q": query, "per_page": per_page}
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order

        raw = self._request("/search/repositories", params)
        return self._normalize(raw, "repo")

    # -------------------------
    # Search: Users
    # -------------------------
    def search_users(self, keyword: str, qualifiers: List[str] = None,
                     per_page: int = 20):
        query = self._build_query(keyword, qualifiers=qualifiers or [])
        raw = self._request("/search/users", {"q": query, "per_page": per_page})
        return self._normalize(raw, "user")

    # -------------------------
    # New Feature: Get README.md
    # -------------------------
    def get_repo_readme(self, owner: str, repo: str) -> Dict:
        """
        Returns:
        {
            "name": "README.md",
            "path": "README.md",
            "content": "<markdown_string>",
            "html_url": "..."
        }
        """
        endpoint = f"/repos/{owner}/{repo}/readme"

        raw = self._request(endpoint)

        content_b64 = raw.get("content", "")
        markdown = base64.b64decode(content_b64).decode("utf-8")

        return {
            "name": raw.get("name"),
            "path": raw.get("path"),
            "html_url": raw.get("html_url"),
            "content": markdown
        }


mcp = FastMCP("github-search")


def get_github_client() -> GitHubSearchClient:
    """Initialize GitHub search client with token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return GitHubSearchClient(token)


@mcp.tool()
def search_code(keyword: str, repo: Optional[str] = None, user: Optional[str] = None,
                language: Optional[str] = None, path: Optional[str] = None,
                per_page: int = 20) -> str:
    """
    Search for code across GitHub repositories with various filters.

    This tool allows you to search for specific code patterns, functions, or keywords
    across all public GitHub repositories. Results are ranked by relevance and include
    file paths and repository information.

    Args:
        keyword: The search term to look for in code (e.g., "function getName", "import React")
        repo: Optional. Specific repository to search in format "owner/repo" (e.g., "facebook/react")
        user: Optional. Search within repositories owned by a specific user or organization
        language: Optional. Filter by programming language (e.g., "python", "javascript", "go")
        path: Optional. Search within specific file paths or directories (e.g., "src/components")
        per_page: Number of results to return (default: 20, max: 100)

    Returns:
        A formatted string containing search results with file paths, repository names,
        and direct URLs to the matching code files. Results are sorted by relevance score.
    """
    try:
        client = get_github_client()
        result = client.search_code(
            keyword=keyword,
            repo=repo,
            user=user,
            language=language,
            path=path,
            per_page=per_page
        )

        if not result["items"]:
            return f"No code found for keyword: {keyword}"

        output = [f"Found {result['total']} results for '{keyword}':\n"]

        for item in result["items"]:
            repo_name = item["full_name"] or "Unknown"
            file_path = item["extra"]["path"]
            file_url = item["url"]
            score = item.get("score", 0)

            output.append(f"Repository: {repo_name}")
            output.append(f"File: {file_path}")
            output.append(f"URL: {file_url}")
            output.append(f"Relevance Score: {score:.2f}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching code: {str(e)}"


@mcp.tool()
def search_repositories(keyword: str, user: Optional[str] = None, language: Optional[str] = None,
                       sort: Optional[str] = None, order: Optional[str] = None,
                       per_page: int = 20) -> str:
    """
    Search for GitHub repositories with various sorting and filtering options.

    Find repositories based on keywords, with options to filter by owner, programming language,
    and sort by stars, forks, or updated date. Useful for discovering popular projects
    or finding repositories in specific domains.

    Args:
        keyword: Search term for repository names, descriptions, or topics
        user: Optional. Filter by repositories owned by specific user/organization
        language: Optional. Filter by primary programming language
        sort: Optional. Sort by 'stars', 'forks', or 'updated'
        order: Optional. Sort order: 'asc' or 'desc' (default: 'desc')
        per_page: Number of results to return (default: 20, max: 100)

    Returns:
        A formatted string containing repository information including names, star counts,
        primary languages, and direct URLs to the repositories.
    """
    try:
        client = get_github_client()
        result = client.search_repos(
            keyword=keyword,
            user=user,
            language=language,
            sort=sort,
            order=order,
            per_page=per_page
        )

        if not result["items"]:
            return f"No repositories found for keyword: {keyword}"

        output = [f"Found {result['total']} repositories for '{keyword}':\n"]

        for item in result["items"]:
            name = item["name"] or "Unknown"
            full_name = item["full_name"] or "Unknown"
            stars = item["extra"]["stars"]
            language = item["extra"]["language"] or "Unknown"
            url = item["url"]

            output.append(f"Repository: {full_name}")
            output.append(f"Name: {name}")
            output.append(f"Language: {language}")
            output.append(f"Stars: {stars}")
            output.append(f"URL: {url}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching repositories: {str(e)}"


@mcp.tool()
def search_users(keyword: str, qualifiers: Optional[List[str]] = None, per_page: int = 20) -> str:
    """
    Search for GitHub users based on keywords and qualifiers.

    Find GitHub users by their usernames, full names, or bio information. Useful for
    discovering developers in specific fields or finding colleagues and collaborators.

    Args:
        keyword: Search term for username, full name, or bio
        qualifiers: Optional. List of GitHub search qualifiers (e.g., ["type:owner", "location:San Francisco"])
        per_page: Number of results to return (default: 20, max: 100)

    Returns:
        A formatted string containing user information including usernames, profile URLs,
        and user IDs from the search results.
    """
    try:
        client = get_github_client()
        result = client.search_users(
            keyword=keyword,
            qualifiers=qualifiers,
            per_page=per_page
        )

        if not result["items"]:
            return f"No users found for keyword: {keyword}"

        output = [f"Found {result['total']} users for '{keyword}':\n"]

        for item in result["items"]:
            name = item["name"] or "Unknown"
            full_name = item["full_name"] or "Unknown"
            user_id = item["extra"]["id"]
            avatar = item["extra"]["avatar"]
            url = item["url"]

            output.append(f"User: {full_name}")
            output.append(f"User ID: {user_id}")
            output.append(f"Username: {name}")
            output.append(f"Avatar: {avatar}")
            output.append(f"Profile: {url}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching users: {str(e)}"


@mcp.tool()
def search_issues(keyword: str, repo: Optional[str] = None, user: Optional[str] = None,
                 state: Optional[str] = None, per_page: int = 20) -> str:
    """
    Search for GitHub issues across repositories.

    Find issues and bug reports based on keywords, with options to filter by specific
    repositories, users, or issue state (open/closed). Useful for finding similar
    problems or tracking project issues.

    Args:
        keyword: Search term for issue titles and descriptions
        repo: Optional. Search within specific repository (format: "owner/repo")
        user: Optional. Search within repositories owned by specific user/organization
        state: Optional. Filter by issue state: 'open', 'closed', or 'all'
        per_page: Number of results to return (default: 20, max: 100)

    Returns:
        A formatted string containing issue information including titles, numbers,
        current state, and direct URLs to the issues.
    """
    try:
        client = get_github_client()
        result = client.search_issues(
            keyword=keyword,
            repo=repo,
            user=user,
            state=state,
            is_pr=False,
            per_page=per_page
        )

        if not result["items"]:
            return f"No issues found for keyword: {keyword}"

        output = [f"Found {result['total']} issues for '{keyword}':\n"]

        for item in result["items"]:
            title = item["name"] or "Unknown"
            number = item["extra"]["number"]
            repo_name = item["extra"]["repo"]
            state = item["extra"]["state"]
            url = item["url"]

            output.append(f"Issue #{number}: {title}")
            output.append(f"Repository: {repo_name}")
            output.append(f"State: {state}")
            output.append(f"URL: {url}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching issues: {str(e)}"


@mcp.tool()
def search_pull_requests(keyword: str, repo: Optional[str] = None, user: Optional[str] = None,
                        state: Optional[str] = None, per_page: int = 20) -> str:
    """
    Search for GitHub pull requests across repositories.

    Find pull requests based on keywords, with options to filter by specific repositories,
    users, or PR state (open/closed/merged). Useful for finding similar changes or
    tracking development activity.

    Args:
        keyword: Search term for PR titles and descriptions
        repo: Optional. Search within specific repository (format: "owner/repo")
        user: Optional. Search within repositories owned by specific user/organization
        state: Optional. Filter by PR state: 'open', 'closed', or 'all'
        per_page: Number of results to return (default: 20, max: 100)

    Returns:
        A formatted string containing PR information including titles, numbers,
        current state, and direct URLs to the pull requests.
    """
    try:
        client = get_github_client()
        result = client.search_pr(
            keyword=keyword,
            repo=repo,
            user=user,
            state=state,
            per_page=per_page
        )

        if not result["items"]:
            return f"No pull requests found for keyword: {keyword}"

        output = [f"Found {result['total']} pull requests for '{keyword}':\n"]

        for item in result["items"]:
            title = item["name"] or "Unknown"
            number = item["extra"]["number"]
            repo_name = item["extra"]["repo"]
            state = item["extra"]["state"]
            url = item["url"]

            output.append(f"PR #{number}: {title}")
            output.append(f"Repository: {repo_name}")
            output.append(f"State: {state}")
            output.append(f"URL: {url}")
            output.append("---")

        return "\n".join(output)

    except Exception as e:
        return f"Error searching pull requests: {str(e)}"


@mcp.tool()
def get_repository_readme(owner: str, repo: str) -> str:
    """
    Retrieve the README content from a GitHub repository.

    This tool fetches the main README file from a repository, which typically contains
    important documentation, installation instructions, usage examples, and project
    descriptions. Essential for understanding new projects.

    Args:
        owner: The repository owner's username or organization name
        repo: The repository name

    Returns:
        The full content of the repository's README file in Markdown format.
        Includes file metadata such as name, path, and URL to the raw file.
    """
    try:
        client = get_github_client()
        readme_data = client.get_repo_readme(owner, repo)

        output = [
            f"README from {owner}/{repo}",
            f"File: {readme_data['path']}",
            f"URL: {readme_data['html_url']}",
            f"\n--- Content ---\n",
            readme_data['content']
        ]

        return "\n".join(output)

    except Exception as e:
        return f"Error retrieving README: {str(e)}"


@mcp.tool()
def comprehensive_github_search(keyword: str, search_type: str = "all", user: Optional[str] = None,
                              language: Optional[str] = None, per_page: int = 10) -> str:
    """
    Perform a comprehensive search across multiple GitHub entity types.

    This tool provides a unified search experience across repositories, code, users,
    issues, and pull requests with a single query. Useful for broad exploration
    or when you're not sure what type of GitHub entity you're looking for.

    Args:
        keyword: The search term to use across all entity types
        search_type: Type of search to perform: 'all', 'repos', 'code', 'users', 'issues', 'prs'
        user: Optional. Filter results to entities owned by this user/organization
        language: Optional. Filter results by programming language (for repos and code)
        per_page: Number of results per category (default: 10, max: 50)

    Returns:
        A comprehensive report combining search results from multiple GitHub entity types,
        neatly organized by category with counts and top results for each type.
    """
    try:
        client = get_github_client()
        results = []

        if search_type in ["all", "repos"]:
            repo_result = client.search_repos(keyword, user=user, language=language, per_page=per_page)
            if repo_result["items"]:
                results.append(f"REPOSITORIES ({repo_result['total']} found):")
                for item in repo_result["items"][:5]:  # Show top 5
                    results.append(f"  - {item['full_name']} - Stars: {item['extra']['stars']} - Language: {item['extra']['language'] or 'Unknown'}")
                results.append("")

        if search_type in ["all", "code"]:
            code_result = client.search_code(keyword, user=user, language=language, per_page=per_page)
            if code_result["items"]:
                results.append(f"CODE ({code_result['total']} found):")
                for item in code_result["items"][:5]:  # Show top 5
                    repo_name = item['full_name'] or 'Unknown'
                    file_path = item['extra']['path']
                    results.append(f"  - {repo_name}:{file_path}")
                results.append("")

        if search_type in ["all", "users"]:
            user_result = client.search_users(keyword, per_page=per_page)
            if user_result["items"]:
                results.append(f"USERS ({user_result['total']} found):")
                for item in user_result["items"][:5]:  # Show top 5
                    results.append(f"  - {item['full_name']} - ID: {item['extra']['id']}")
                results.append("")

        if search_type in ["all", "issues"]:
            issue_result = client.search_issues(keyword, user=user, per_page=per_page)
            if issue_result["items"]:
                results.append(f"ISSUES ({issue_result['total']} found):")
                for item in issue_result["items"][:5]:  # Show top 5
                    repo = item['extra']['repo']
                    number = item['extra']['number']
                    title = item['name'] or 'Unknown'
                    results.append(f"  - {repo}#{number}: {title[:50]}{'...' if len(title) > 50 else ''}")
                results.append("")

        if search_type in ["all", "prs"]:
            pr_result = client.search_pr(keyword, user=user, per_page=per_page)
            if pr_result["items"]:
                results.append(f"PULL REQUESTS ({pr_result['total']} found):")
                for item in pr_result["items"][:5]:  # Show top 5
                    repo = item['extra']['repo']
                    number = item['extra']['number']
                    title = item['name'] or 'Unknown'
                    results.append(f"  - {repo}#{number}: {title[:50]}{'...' if len(title) > 50 else ''}")
                results.append("")

        if not results:
            return f"No results found for '{keyword}' across all GitHub entities."

        header = [f"Comprehensive GitHub Search Results for '{keyword}':\n", "=" * 60, ""]
        return "\n".join(header + results)

    except Exception as e:
        return f"Error in comprehensive search: {str(e)}"


if __name__ == "__main__":
    mcp.run()
"""Memos Uploader Module.

This module provides a unified interface for uploading various content to Memos system,
including WeChat official account articles and custom text content.
"""

import os
import sys
import json
import uuid
import requests

sys.path.insert(0, os.getcwd())
from typing import List, Dict, Any, Optional
from pathlib import Path
from config.config_loader import Config
from core.logger import get_logger

logger = get_logger("sai_update", "sai_update")


class MemosUploader:
    """Uploader for Memos memory system.

    This class provides methods to upload content to Memos, including:
    - Batch upload WeChat official account articles from JSON file
    - Upload custom text content with automatic splitting
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Memos uploader.

        Args:
            config: Config instance. If None, will get global instance.
        """
        self.config = config or Config.get_instance()
        self._load_memos_config()

    def _load_memos_config(self) -> None:
        """Load Memos configuration from config instance."""
        self.api_key = os.environ.get("MEMOS_API_KEY")
        self.base_url = os.environ.get("MEMOS_BASE_URL")

        if not self.api_key or not self.base_url:
            raise ValueError(
                "Memos configuration not found. "
                "Ensure MEMOS_API_KEY and MEMOS_BASE_URL are set in config.yaml or environment."
            )

        print(f"Memos uploader initialized with base_url: {self.base_url}")

    def _add_message(self, conversation_id: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Add messages to a conversation in Memos.

        Args:
            conversation_id: Unique conversation identifier
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Response JSON from Memos API

        Raises:
            requests.RequestException: If API request fails
        """
        data = {
            "user_id": "memos_user_geekcenter",
            "conversation_id": conversation_id,
            "messages": messages,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
        }

        url = f"{self.base_url}/add/message"

        logger.debug(f"Sending request to {url}")
        logger.debug(f"Messages: {json.dumps(messages, ensure_ascii=False, indent=2)}")

        try:
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to add message: {e}")
            raise

    def _split_text(self, text: str, n: int) -> List[str]:
        """
        Split text into n equal parts.

        Args:
            text: Text to split
            n: Number of parts

        Returns:
            List of text parts
        """
        length = len(text)
        part_size = length // n
        parts = []

        for i in range(n):
            start = i * part_size
            end = None if i == n - 1 else (i + 1) * part_size
            parts.append(text[start:end])

        return parts

    def upload_article(self, article_data: Dict[str, Any]) -> str:
        """
        Upload a single WeChat official account article to Memos.

        Args:
            article_data: Article dict containing:
                - title: Article title
                - author: Author name
                - content: Article content
                - publish_time: Publish time
                - url: Article URL (optional)

        Returns:
            Conversation ID for the uploaded article

        Raises:
            KeyError: If required fields are missing
            requests.RequestException: If upload fails
        """
        required_fields = ["title", "author", "content", "publish_time"]
        for field in required_fields:
            if field not in article_data:
                raise KeyError(f"Missing required field: {field}")

        title = article_data["title"]
        author = article_data["author"]
        content = article_data["content"]
        publish_time = article_data["publish_time"]
        url = article_data.get("url", "")

        conversation_id = str(uuid.uuid4())

        user_message = f"请阅读以下文章：\n标题：{title}\n作者：{author}\n发布时间：{publish_time}\n链接：{url}"

        self._add_message(
            conversation_id=conversation_id,
            messages=[{"role": "user", "content": user_message}]
        )

        text_parts = self._split_text(content, 4)

        for idx, part in enumerate(text_parts, start=1):
            self._add_message(
                conversation_id=conversation_id,
                messages=[
                    {
                        "role": "assistant",
                        "content": f"（第 {idx}/4 部分）\n{part}"
                    }
                ],
            )

        print(f"Successfully uploaded article: {title} (conversation_id: {conversation_id})")
        return conversation_id

    def batch_upload_articles(self, articles_path: str) -> List[str]:
        """
        Batch upload WeChat official account articles from JSON file.

        Args:
            articles_path: Path to articles JSON file

        Returns:
            List of conversation IDs for uploaded articles

        Raises:
            FileNotFoundError: If articles file not found
            json.JSONDecodeError: If JSON parsing fails
            requests.RequestException: If any upload fails
        """
        articles_file = Path(articles_path)

        if not articles_file.exists():
            raise FileNotFoundError(f"Articles file not found: {articles_path}")

        with open(articles_file, "r", encoding="utf-8") as f:
            articles = json.load(f)

        if not isinstance(articles, list):
            raise ValueError("Articles JSON must be a list of article objects")

        print(f"Starting batch upload of {len(articles)} articles from {articles_path}")

        conversation_ids = []
        failed_articles = []

        for idx, article in enumerate(articles, start=1):
            try:
                title = article.get("title", "Unknown")
                print(f"[{idx}/{len(articles)}] Uploading article: {title}")

                conversation_id = self.upload_article(article)
                conversation_ids.append(conversation_id)

            except Exception as e:
                logger.error(f"Failed to upload article {idx}: {e}")
                failed_articles.append({"index": idx, "article": article, "error": str(e)})

        print(f"Batch upload completed: {len(conversation_ids)} succeeded, {len(failed_articles)} failed")

        if failed_articles:
            logger.warning(f"Failed articles: {len(failed_articles)}")
            for failure in failed_articles:
                logger.warning(f"  - Article {failure['index']}: {failure['error']}")

        return conversation_ids

    def upload_text(
        self,
        text: str,
        user_query: str = "",
        parts: int = 1
    ) -> str:
        """
        Upload custom text content to Memos.

        Args:
            text: Text content to upload
            user_query: User query/prompt to associate with the text
            parts: Number of parts to split the text into (default: 1)

        Returns:
            Conversation ID for the uploaded text

        Raises:
            requests.RequestException: If upload fails
        """
        if not text:
            raise ValueError("Text content cannot be empty")

        conversation_id = str(uuid.uuid4())

        if user_query:
            self._add_message(
                conversation_id=conversation_id,
                messages=[{"role": "user", "content": user_query}]
            )

        text_parts = self._split_text(text, parts)

        for idx, part in enumerate(text_parts, start=1):
            part_label = f"（第 {idx}/{parts} 部分）" if parts > 1 else ""
            self._add_message(
                conversation_id=conversation_id,
                messages=[
                    {
                        "role": "assistant",
                        "content": f"{part_label}\n{part}"
                    }
                ],
            )

        print(f"Successfully uploaded custom text (conversation_id: {conversation_id})")
        return conversation_id


def main():
    """Main function for manual testing."""
    config = Config(config_file_path="config/config.yaml")
    config.load_config(override=True)

    uploader = MemosUploader(config)

    articles_path = "articles/articles.json"
    conversation_ids = uploader.batch_upload_articles(articles_path)

    print(f"Upload Summary: {len(conversation_ids)} articles uploaded successfully")
    print(f"Conversation IDs: {conversation_ids}")


if __name__ == "__main__":
    main()

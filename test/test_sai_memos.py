"""Test suite for SAI Memos search functionality.

This test suite validates the SAI Memos search tool which allows users to search
through conversation memory stored in Memos system.

Make sure the environment is properly configured before running tests:

1. Set up config/config.yaml with valid MEMOS_API_KEY and MEMOS_BASE_URL
2. Ensure Memos service is accessible

Then run tests:

    pytest test/test_sai_memos.py -v
"""

import pytest
import requests
import os
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

sys.path.insert(0, os.getcwd())

from config.config_loader import Config
from core.logger import get_logger

logger = get_logger(__name__)

# Test results directory
TEST_RESULTS_DIR = Path("test/test_results")
TEST_RESULTS_DIR.mkdir(exist_ok=True, parents=True)


def save_test_result(test_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> str:
    """
    Save test result to JSON file with timestamp.

    Args:
        test_name: Name of the test
        inputs: Test input parameters
        outputs: Test output/results

    Returns:
        Path to saved result file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = TEST_RESULTS_DIR / filename

    result = {
        "test_name": test_name,
        "timestamp": datetime.now().isoformat(),
        "inputs": inputs,
        "outputs": outputs,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Test result saved to: {filepath}")
    return str(filepath)


@pytest.fixture(autouse=True)
def clear_test_results():
    """Optional: Clear test results before each test run."""
    yield
    # Uncomment below to clear results after each test
    # for file in TEST_RESULTS_DIR.glob("*.json"):
    #     file.unlink()
    pass


class TestSAIMemosConfiguration:
    """Test Memos configuration and connection."""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup configuration for tests."""
        self.config = Config.get_instance()
        self.api_key = os.environ.get("MEMOS_API_KEY")
        self.base_url = os.environ.get("MEMOS_BASE_URL")

    def test_config_loaded(self):
        """Test that configuration is properly loaded."""
        assert self.api_key is not None, "MEMOS_API_KEY should be set"
        assert self.base_url is not None, "MEMOS_BASE_URL should be set"
        logger.info(f"Config loaded: base_url={self.base_url}")

    def test_memos_connection(self):
        """Test connection to Memos service."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
        }

        test_data = {
            "query": "test connection",
            "user_id": "memos_user_geekcenter",
            "conversation_id": str(uuid.uuid4()),
        }

        try:
            response = requests.post(
                f"{self.base_url}/search/memory",
                headers=headers,
                data=json.dumps(test_data),
                timeout=10
            )

            assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code}"
            logger.info(f"Connection test response status: {response.status_code}")

        except requests.exceptions.ConnectionError as e:
            pytest.fail(
                f"Cannot connect to Memos service at {self.base_url}. "
                f"Please check if the service is running and accessible.\nError: {e}"
            )
        except Exception as e:
            pytest.fail(f"Failed to connect to Memos service: {e}")


class TestSAIMemosSearch:
    """Test SAI Memos search functionality via tool calls."""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup configuration for tests."""
        self.config = Config.get_instance()
        self.api_key = os.environ.get("MEMOS_API_KEY")
        self.base_url = os.environ.get("MEMOS_BASE_URL")
        self.user_id = "memos_user_geekcenter"

    def _search_memory(self, query: str, conversation_id: str = None) -> dict:
        """
        Helper method to perform Memos search.

        Args:
            query: Search query string
            conversation_id: Optional conversation ID

        Returns:
            Response JSON as dict
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        data = {
            "query": query,
            "user_id": self.user_id,
            "conversation_id": conversation_id,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
        }

        url = f"{self.base_url}/search/memory"
        response = requests.post(url=url, headers=headers, data=json.dumps(data))

        return response.json()

    def test_search_basic(self):
        """Test basic search functionality."""
        query = "人工智能学院"
        result = self._search_memory(query)

        assert result is not None
        logger.info(f"Basic search result: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # Save test result
        save_test_result(
            test_name="test_search_basic",
            inputs={"query": query},
            outputs={"result": result}
        )

    def test_search_with_custom_conversation_id(self):
        """Test search with custom conversation ID."""
        custom_id = str(uuid.uuid4())
        query = "上海交通大学"
        result = self._search_memory(query, conversation_id=custom_id)

        assert result is not None
        logger.info(f"Search with custom conversation_id: {custom_id}")

        # Save test result
        save_test_result(
            test_name="test_search_with_custom_conversation_id",
            inputs={"query": query, "conversation_id": custom_id},
            outputs={"result": result}
        )

    def test_search_empty_query(self):
        """Test search with empty query."""
        query = ""
        result = self._search_memory(query)

        assert result is not None
        logger.info(f"Empty query search result: {result}")

    def test_search_chinese_query(self):
        """Test search with Chinese query."""
        query = "星图 AI 引擎"
        result = self._search_memory(query)

        assert result is not None
        logger.info(f"Chinese search completed for query: {query}")

    def test_search_english_query(self):
        """Test search with English query."""
        query = "machine learning"
        result = self._search_memory(query)

        assert result is not None
        logger.info(f"English search completed for query: {query}")

    def test_search_multiple_queries_same_conversation(self):
        """Test multiple searches in the same conversation."""
        conversation_id = str(uuid.uuid4())

        queries = [
            "人工智能",
            "学术讲座",
            "球类运动"
        ]

        results = []
        for query in queries:
            result = self._search_memory(query, conversation_id=conversation_id)
            results.append(result)
            logger.info(f"Query '{query}' in conversation {conversation_id}")

        assert len(results) == len(queries)
        logger.info(f"Completed {len(queries)} searches in conversation {conversation_id}")

        # Save test result
        save_test_result(
            test_name="test_search_multiple_queries_same_conversation",
            inputs={"conversation_id": conversation_id, "queries": queries},
            outputs={"results": results}
        )


class TestSAIMemosToolIntegration:
    """Integration tests simulating actual tool usage."""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup configuration for tests."""
        self.config = Config.get_instance()
        self.api_key = os.environ.get("MEMOS_API_KEY")
        self.base_url = os.environ.get("MEMOS_BASE_URL")
        self.user_id = "memos_user_geekcenter"

    def test_simulate_user_conversation_flow(self):
        """Simulate a typical user conversation with multiple searches."""
        conversation_id = str(uuid.uuid4())

        conversation_turns = [
            "上海交大人工智能学院的介绍",
            "学院有什么学术讲座",
            "星图是什么",
        ]

        turn_results = []
        for turn_num, query in enumerate(conversation_turns, start=1):
            data = {
                "query": query,
                "user_id": self.user_id,
                "conversation_id": conversation_id,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.api_key}",
            }

            response = requests.post(
                f"{self.base_url}/search/memory",
                headers=headers,
                data=json.dumps(data)
            )

            assert response.status_code in [200, 404]
            result = response.json()

            turn_results.append({
                "turn": turn_num,
                "query": query,
                "status_code": response.status_code,
                "result_keys": list(result.keys())
            })

            logger.info(f"Turn {turn_num}: Query='{query}'")
            logger.info(f"Response keys: {result.keys()}")

        logger.info(f"Conversation flow completed with {len(conversation_turns)} turns")

        # Save test result
        save_test_result(
            test_name="test_simulate_user_conversation_flow",
            inputs={"conversation_id": conversation_id, "conversation_turns": conversation_turns},
            outputs={"turn_results": turn_results}
        )

    def test_search_with_special_characters(self):
        """Test search with special characters in query."""
        special_queries = [
            "AI & Deep Learning?",
            "机器学习（人工智能）",
            "C++、Python 编程",
        ]

        for query in special_queries:
            data = {
                "query": query,
                "user_id": self.user_id,
                "conversation_id": str(uuid.uuid4()),
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.api_key}",
            }

            response = requests.post(
                f"{self.base_url}/search/memory",
                headers=headers,
                data=json.dumps(data)
            )

            assert response.status_code in [200, 404]
            logger.info(f"Special character query handled: {query}")


class TestSAIMemosErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup configuration for tests."""
        self.config = Config.get_instance()
        self.api_key = os.environ.get("MEMOS_API_KEY")
        self.base_url = os.environ.get("MEMOS_BASE_URL")
        self.user_id = "memos_user_geekcenter"

    def test_search_invalid_api_key(self):
        """Test search with invalid API key."""
        invalid_key = "invalid_api_key_12345"

        data = {
            "query": "test",
            "user_id": self.user_id,
            "conversation_id": str(uuid.uuid4()),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {invalid_key}",
        }

        response = requests.post(
            f"{self.base_url}/search/memory",
            headers=headers,
            data=json.dumps(data)
        )

        assert response.status_code in [401, 403, 404]
        logger.info(f"Invalid API key handled correctly: status {response.status_code}")

    def test_search_missing_required_field(self):
        """Test search with missing required fields."""
        test_cases = [
            {"query": "test"},  # Missing user_id and conversation_id
            {"user_id": self.user_id},  # Missing query and conversation_id
        ]

        for data in test_cases:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.api_key}",
            }

            response = requests.post(
                f"{self.base_url}/search/memory",
                headers=headers,
                data=json.dumps(data)
            )

            logger.info(f"Missing fields test: status {response.status_code}")

    def test_search_very_long_query(self):
        """Test search with very long query."""
        long_query = "测试" * 500  # 1000 characters

        data = {
            "query": long_query,
            "user_id": self.user_id,
            "conversation_id": str(uuid.uuid4()),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
        }

        response = requests.post(
            f"{self.base_url}/search/memory",
            headers=headers,
            data=json.dumps(data)
        )

        assert response.status_code in [200, 404, 413]  # 413 = Payload Too Large
        logger.info(f"Long query handled: length={len(long_query)}, status={response.status_code}")


class TestSAIMemosPerformance:
    """Performance and stress tests."""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup configuration for tests."""
        self.config = Config.get_instance()
        self.api_key = os.environ.get("MEMOS_API_KEY")
        self.base_url = os.environ.get("MEMOS_BASE_URL")
        self.user_id = "memos_user_geekcenter"

    def test_concurrent_searches(self):
        """Test multiple concurrent searches."""
        import concurrent.futures

        def perform_search(query):
            data = {
                "query": query,
                "user_id": self.user_id,
                "conversation_id": str(uuid.uuid4()),
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.api_key}",
            }

            response = requests.post(
                f"{self.base_url}/search/memory",
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )

            return response.status_code

        queries = [f"search query {i}" for i in range(5)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(perform_search, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(status in [200, 404] for status in results)
        logger.info(f"Concurrent searches completed: {len(results)} requests")

    def test_search_response_time(self):
        """Test search response time."""
        import time

        query = "performance test"
        conversation_id = str(uuid.uuid4())

        data = {
            "query": query,
            "user_id": self.user_id,
            "conversation_id": conversation_id,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
        }

        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/search/memory",
            headers=headers,
            data=json.dumps(data)
        )
        elapsed_time = time.time() - start_time

        assert response.status_code in [200, 404]
        logger.info(f"Search response time: {elapsed_time:.3f} seconds")

        # Save test result
        save_test_result(
            test_name="test_search_response_time",
            inputs={"query": query, "conversation_id": conversation_id},
            outputs={
                "response_time_seconds": round(elapsed_time, 3),
                "status_code": response.status_code
            }
        )


@pytest.fixture(scope="session", autouse=True)
def verify_environment():
    """Verify test environment is properly configured."""
    try:
        config = Config(config_file_path="config/config.yaml")
        config.load_config(override=True)

        api_key = os.environ.get("MEMOS_API_KEY")
        base_url = os.environ.get("MEMOS_BASE_URL")

        if not api_key or not base_url:
            pytest.fail(
                "Memos configuration not found. Please ensure MEMOS_API_KEY and "
                "MEMOS_BASE_URL are set in config/config.yaml under the 'env' section."
            )

        logger.info(f"Environment verified: base_url={base_url}")

    except RuntimeError as e:
        if "singleton" in str(e):
            config = Config.get_instance()
            api_key = os.environ.get("MEMOS_API_KEY")
            base_url = os.environ.get("MEMOS_BASE_URL")
            logger.info(f"Environment verified (using existing instance): base_url={base_url}")
        else:
            raise
    except Exception as e:
        pytest.fail(f"Failed to verify test environment: {e}")


if __name__ == "__main__":
    config = Config(config_file_path="config/config.yaml")
    config.load_config(override=True)
    pytest.main([__file__, "-v", "--tb=short"])

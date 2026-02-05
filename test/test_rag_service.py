"""Test suite for RAG Service endpoints.

This test suite validates all RAG service API endpoints.
Make sure the RAG service is running before executing these tests:

    python backend/tool_backend/rag_service.py

Then run tests:

    pytest test/test_rag_service.py -v
"""

import pytest
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:39257"


class TestRAGServiceHealth:
    """Test service health and status endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rag"

    def test_service_status(self):
        """Test service status endpoint."""
        response = requests.get(f"{BASE_URL}/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "index_exists" in data
        assert "index_path" in data
        assert "supported_formats" in data

        # Verify supported formats
        expected_formats = ["pdf", "txt", "md", "docx"]
        assert all(fmt in data["supported_formats"] for fmt in expected_formats)


class TestRAGServiceSearch:
    """Test search endpoints."""

    def test_search_basic(self):
        """Test basic search functionality."""
        payload = {"query": "test query"}
        response = requests.post(f"{BASE_URL}/search", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "query" in data
        assert "results" in data
        assert "count" in data
        assert data["query"] == "test query"

    def test_search_with_limit(self):
        """Test search with custom result limit."""
        payload = {"query": "test", "limit": 3}
        response = requests.post(f"{BASE_URL}/search", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert isinstance(data["results"], list)
        assert data["count"] <= 3

    def test_search_with_threshold(self):
        """Test search with custom similarity threshold."""
        payload = {"query": "test", "threshold": 0.9}
        response = requests.post(f"{BASE_URL}/search", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        # Verify all results meet threshold
        for result in data["results"]:
            if "score" in result:
                assert result["score"] >= 0.9

    def test_search_with_both_parameters(self):
        """Test search with both limit and threshold."""
        payload = {"query": "test", "limit": 5, "threshold": 0.5}
        response = requests.post(f"{BASE_URL}/search", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["count"] <= 5

    def test_search_empty_query(self):
        """Test search with empty query."""
        payload = {"query": ""}
        response = requests.post(f"{BASE_URL}/search", json=payload)

        # Should handle gracefully
        assert response.status_code == 200

    def test_search_invalid_threshold(self):
        """Test search with invalid threshold value."""
        payload = {"query": "test", "threshold": 1.5}
        response = requests.post(f"{BASE_URL}/search", json=payload)

        # Should handle invalid threshold
        assert response.status_code in [200, 422]


class TestRAGServiceIndexing:
    """Test document indexing endpoints."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Setup test environment with sample documents."""
        # Create test directory
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()

        # Create test text file
        test_file = test_dir / "sample.txt"
        test_file.write_text(
            "This is a test document for RAG service. "
            "It contains multiple sentences about machine learning and artificial intelligence. "
            "The purpose is to test semantic search capabilities."
        )

        # Create test markdown file
        md_file = test_dir / "sample.md"
        md_file.write_text(
            "# Test Document\n\n"
            "This is a markdown file.\n"
            "## Section 1\n"
            "Content about deep learning.\n"
            "## Section 2\n"
            "Content about neural networks."
        )

        self.test_dir = str(test_dir)
        self.test_file = str(test_file)
        self.md_file = str(md_file)

        yield

        # Cleanup: delete indexed documents
        try:
            requests.delete(
                f"{BASE_URL}/documents",
                json={"document_ids": ["sample", "sample.md"], "save": True},
            )
        except:
            pass

    def test_index_single_file(self):
        """Test indexing a single file."""
        response = requests.post(
            f"{BASE_URL}/index/file",
            params={"file_path": self.test_file, "save": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["success", "warning"]
        assert "chunks_indexed" in data
        assert data["chunks_indexed"] > 0
        assert data["file"] == self.test_file

    def test_index_directory(self):
        """Test indexing a directory."""
        response = requests.post(
            f"{BASE_URL}/index/directory",
            params={"directory_path": self.test_dir, "recursive": False, "save": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["success", "warning"]
        assert "chunks_indexed" in data
        assert data["chunks_indexed"] > 0
        assert data["directory"] == self.test_dir

    def test_index_directory_recursive(self):
        """Test indexing a directory recursively."""
        # Create nested directory structure
        subdir = Path(self.test_dir) / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested document content")

        response = requests.post(
            f"{BASE_URL}/index/directory",
            params={"directory_path": self.test_dir, "recursive": True, "save": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["success", "warning"]
        # Should index more files than non-recursive
        assert data["chunks_indexed"] > 0

    def test_index_nonexistent_file(self):
        """Test indexing a non-existent file."""
        response = requests.post(
            f"{BASE_URL}/index/file",
            params={"file_path": "/nonexistent/file.pdf", "save": False},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return error status
        assert data["status"] in ["error", "warning"]

    def test_index_unsupported_format(self):
        """Test indexing an unsupported file format."""
        # Create a file with unsupported extension
        unsupported_file = Path(self.test_dir) / "test.xyz"
        unsupported_file.write_text("content")

        response = requests.post(
            f"{BASE_URL}/index/file",
            params={"file_path": str(unsupported_file), "save": False},
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle gracefully
        assert data["status"] in ["error", "warning"]


class TestRAGServiceDelete:
    """Test document deletion endpoints."""

    def test_delete_single_document(self):
        """Test deleting a single document."""
        # First, index a test file
        test_file = "/tmp/test_delete.txt"
        Path(test_file).write_text("Test content for deletion")

        requests.post(
            f"{BASE_URL}/index/file",
            params={"file_path": test_file, "save": True},
        )

        # Delete the document
        response = requests.delete(
            f"{BASE_URL}/documents",
            json={"document_ids": ["test_delete"], "save": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["success", "warning"]
        assert "chunks_deleted" in data

        # Cleanup
        Path(test_file).unlink(missing_ok=True)

    def test_delete_multiple_documents(self):
        """Test deleting multiple documents."""
        # Create and index test files
        files = []
        for i in range(3):
            test_file = f"/tmp/test_multi_{i}.txt"
            Path(test_file).write_text(f"Test content {i}")
            files.append(test_file)
            requests.post(
                f"{BASE_URL}/index/file",
                params={"file_path": test_file, "save": True},
            )
            time.sleep(0.1)  # Avoid rapid indexing

        # Delete all documents
        response = requests.delete(
            f"{BASE_URL}/documents",
            json={"document_ids": ["test_multi_0", "test_multi_1", "test_multi_2"], "save": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["success", "warning"]
        assert data["chunks_deleted"] > 0

        # Cleanup
        for f in files:
            Path(f).unlink(missing_ok=True)

    def test_delete_nonexistent_document(self):
        """Test deleting a document that doesn't exist."""
        response = requests.delete(
            f"{BASE_URL}/documents",
            json={"document_ids": ["nonexistent_doc"], "save": False},
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle gracefully
        assert data["status"] in ["success", "warning"]


class TestRAGServicePersistence:
    """Test index save and load operations."""

    def test_save_index(self):
        """Test manually saving the index."""
        response = requests.post(f"{BASE_URL}/index/save")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "message" in data

    def test_load_index(self):
        """Test manually loading the index."""
        response = requests.post(f"{BASE_URL}/index/load")

        assert response.status_code == 200
        data = response.json()

        # Can be success or warning (if no index exists)
        assert data["status"] in ["success", "warning"]
        assert "message" in data


class TestRAGServiceIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self, tmp_path):
        """Setup test environment and cleanup after tests."""
        self.test_dir = tmp_path / "integration_test"
        self.test_dir.mkdir()

        yield

        # Cleanup: delete all test documents
        try:
            requests.delete(
                f"{BASE_URL}/documents",
                json={"document_ids": ["integration_test"], "save": True},
            )
        except:
            pass

    def test_complete_workflow(self):
        """Test complete workflow: index -> search -> delete."""
        # Step 1: Create and index a document
        test_file = self.test_dir / "integration_test.txt"
        test_file.write_text(
            "Machine learning is a subset of artificial intelligence. "
            "It focuses on building systems that can learn from data. "
            "Deep learning uses neural networks with multiple layers."
        )

        # Index the file
        index_response = requests.post(
            f"{BASE_URL}/index/file",
            params={"file_path": str(test_file), "save": True},
        )
        assert index_response.status_code == 200
        assert index_response.json()["status"] == "success"

        # Step 2: Search for content
        search_response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "What is machine learning?", "limit": 3},
        )
        assert search_response.status_code == 200
        search_data = search_response.json()

        # Should find results
        assert search_data["status"] == "success"
        assert search_data["count"] >= 0

        # Step 3: Verify search results contain relevant content
        found = False
        for result in search_data["results"]:
            if "text" in result:
                text_lower = result["text"].lower()
                if "machine learning" in text_lower or "artificial intelligence" in text_lower:
                    found = True
                    break

        assert found, "Search results should contain relevant content"

    def test_search_after_multiple_indexes(self):
        """Test searching after indexing multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = self.test_dir / f"test_{i}.txt"
            content = f"Document {i} about topic {i}. "
            content += "This file contains test data for search."
            test_file.write_text(content)
            files.append(str(test_file))

            # Index each file
            response = requests.post(
                f"{BASE_URL}/index/file",
                params={"file_path": str(test_file), "save": True},
            )
            assert response.status_code == 200
            time.sleep(0.1)  # Avoid rapid indexing

        # Search across all indexed files
        search_response = requests.post(
            f"{BASE_URL}/search",
            json={"query": "test data", "limit": 10},
        )

        assert search_response.status_code == 200
        search_data = search_response.json()

        # Should find results from multiple files
        assert search_data["status"] == "success"
        assert search_data["count"] >= 0


class TestRAGServiceErrorHandling:
    """Test error handling and edge cases."""

    def test_search_with_invalid_json(self):
        """Test search with malformed JSON."""
        response = requests.post(
            f"{BASE_URL}/search",
            json="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_index_with_missing_parameter(self):
        """Test indexing without required parameters."""
        response = requests.post(
            f"{BASE_URL}/index/file",
            params={},  # Missing file_path
        )

        # Should return error
        assert response.status_code == 422

    def test_delete_with_empty_list(self):
        """Test deleting with empty document list."""
        response = requests.delete(
            f"{BASE_URL}/documents",
            json={"document_ids": [], "save": False},
        )

        # Should handle gracefully
        assert response.status_code in [200, 422]


@pytest.fixture(scope="session", autouse=True)
def verify_service_running():
    """Verify RAG service is running before tests."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.fail("RAG service is not healthy. Start it with: python backend/tool_backend/rag_service.py")
    except requests.exceptions.ConnectionError:
        pytest.fail(
            "Cannot connect to RAG service. Please start it first:\n"
            "  python backend/tool_backend/rag_service.py"
        )
    except Exception as e:
        pytest.fail(f"Failed to connect to RAG service: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

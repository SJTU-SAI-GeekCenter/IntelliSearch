"""
Global pytest configuration and fixtures for IntelliSearch testing suite

This conftest.py provides shared functionality for all test suites.
All tests are organized under test_standard_toolkit/ directory and use
JSON parameter files for test case generation.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.

    This hook is called at the beginning of test run.
    """
    # Register custom markers
    config.addinivalue_line("markers", "mcp: MCP server tests")
    config.addinivalue_line("markers", "standard_toolkit: Standard toolkit tests")
    config.addinivalue_line("markers", "asyncio: Async tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "integration: Integration tests")


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_results_dir(project_root):
    """
    Get or create test results directory.

    Returns:
        Path: Path to test results directory
    """
    results_dir = Path(__file__).parent / "test_results"
    results_dir.mkdir(exist_ok=True, parents=True)
    return results_dir


def pytest_report_header(config):
    """
    Add custom header to pytest output.

    This provides helpful information about the test environment.
    """
    headers = [
        "\n=== IntelliSearch Testing Suite for Standard MCP ToolKit ===",
        f"Test root: {Path(__file__).parent}",
        f"Python version: {sys.version.split()[0]}",
        "",
        "Testing Structure:",
        "  All tests organized under: test_standard_toolkit/",
        "  Test parameters: test_standard_toolkit/test_params/*.json",
        "",
        "Available MCP Servers:",
    ]

    # List available test parameter files
    params_dir = Path(__file__).parent / "test_standard_toolkit" / "test_params"
    if params_dir.exists():
        for param_file in sorted(params_dir.glob("*.json")):
            headers.append(f"  {param_file.stem}")

    headers.extend([
        "",
        "Usage Examples:",
        "  pytest                                   # Run all tests",
        "  pytest test_standard_toolkit/            # Run all standard toolkit tests",
        "  pytest -k search_local                   # Run search_local tests",
        "  pytest -k search_sai                     # Run search_sai tests",
        "  pytest -k base_toolkit                   # Run base_toolkit tests",
        "=" * 35 + "\n"
    ])

    return "\n".join(str(h) for h in headers)


def pytest_collection_modifyitems(config, items):
    """
    Modify collected test items.

    This hook is called after test collection is completed.
    Automatically adds markers based on test location.
    """
    for item in items:
        # All tests in test_standard_toolkit are MCP tests
        test_path = Path(item.fspath).relative_to(Path(__file__).parent)

        if "test_standard_toolkit" in test_path.parts:
            item.add_marker(pytest.mark.mcp)
            item.add_marker(pytest.mark.standard_toolkit)
            item.add_marker(pytest.mark.asyncio)

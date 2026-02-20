"""
Pytest configuration and fixtures for Standard MCP Toolkit testing

This conftest provides shared functionality for testing standard MCP servers:
- test_search_local: RAG service (search_local MCP server)
- test_search_sai: SAI Memos service (search_sai MCP server)
- test_mcp_standard: Other MCP servers (base_toolkit, search_web, etc.)
"""

import pytest
import json
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.getcwd())
from config.config_loader import Config
from core.logger import get_logger

logger = get_logger("tool_test", "tool_test")


# =============================================================================
# Global Configuration Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def project_config():
    """
    Load project configuration.

    Returns:
        Config: Configuration instance
    """
    try:
        config = Config(config_file_path="config/config.yaml")
        config.load_config(override=True)
        return config
    except Exception as e:
        pytest.skip(f"Failed to load configuration: {e}")


@pytest.fixture(scope="session")
def test_results_dir():
    """Get or create test results directory."""
    results_dir = Path(__file__).parent.parent / "test_results"
    results_dir.mkdir(exist_ok=True, parents=True)
    return results_dir


# =============================================================================
# MCP Standard Servers Configuration
# =============================================================================


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--config",
        action="store",
        default="config/config.yaml",
        help="Path to MCP server config file",
    )
    parser.addoption(
        "--params-dir",
        action="store",
        default="test/test_standard_toolkit/test_params",
        help="Directory containing MCP test parameter files",
    )


def pytest_generate_tests(metafunc):
    """
    Generate test cases dynamically from JSON parameter files.

    This function discovers all JSON files in test_params directory
    and generates test cases for each tool test defined in them.
    """
    if "test_case" in metafunc.fixturenames:
        params_dir = Path(metafunc.config.getoption("--params-dir"))

        test_cases = []
        test_ids = []

        # Find all JSON parameter files
        for param_file in params_dir.glob("*.json"):
            try:
                with open(param_file, "r", encoding="utf-8") as f:
                    param_data = json.load(f)

                server_name = param_file.stem
                tests = param_data.get("tests", [])

                for test in tests:
                    test_cases.append(
                        {
                            "server": server_name,
                            "tool": test.get("tool"),
                            "input_params": test.get("input_params", {}),
                            "param_file": str(param_file),
                        }
                    )
                    test_ids.append(f"{server_name}::{test.get('tool', 'unknown')}")

            except Exception as e:
                print(f"Warning: Failed to load {param_file}: {e}")

        metafunc.parametrize("test_case", test_cases, ids=test_ids)


@pytest.fixture(scope="session")
def config_path(request):
    """Get config path from command line options"""
    return request.config.getoption("--config")


@pytest.fixture(scope="session")
def session_result_collector(request):
    """
    Session-wide test result collector.

    This fixture creates a single collector for the entire test session,
    collects all test results, and saves them to one JSON file at the end.

    Note: When using pytest-xdist with -n option, this fixture runs in each worker.
    We use a shared file-based approach to handle concurrent collection.
    """
    # Import here to avoid circular imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from test_standard_toolkit.test_mcp_standard import TestResultCollector

    collector = TestResultCollector()

    # Register finalizer to generate summary report at session end
    def save_results():
        # Generate summary report at the end of the session
        print(f"\n[DEBUG] save_results() called, total_tests={collector.total_tests}")
        if collector.total_tests > 0:
            try:
                summary_path = collector.generate_summary_report()
                if summary_path:
                    print(f"\n{'='*60}")
                    print(f"Test results saved to: {summary_path}")
                    print(f"JSONL raw data: {summary_path.parent / f'test_results_{collector.timestamp_str}.jsonl'}")
                    print(f"Total tests: {collector.total_tests}")
                    print(f"Passed: {collector.total_passed}, Failed: {collector.total_failed}")
                    print(f"Total time: {collector.total_time_ms:.2f}ms")
                    print(f"{'='*60}")
            except Exception as e:
                print(f"\nWarning: Failed to generate summary: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[DEBUG] No tests collected, skipping summary generation")

    request.addfinalizer(save_results)
    return collector


@pytest.fixture(scope="session")
def mcp_config(config_path):
    """Load and verify MCP configuration."""
    try:
        config = Config(config_file_path=config_path)
        config.load_config(override=True)

        all_servers = config.get("all_servers", {})
        if not all_servers:
            pytest.skip(
                "No MCP servers configured in config.yaml. "
                "Please configure servers before running MCP tests."
            )

        return config

    except Exception as e:
        pytest.skip(f"Failed to load MCP configuration: {e}")


# =============================================================================
# Test Result Saving Helper
# =============================================================================


def save_test_result(
    test_name: str, inputs: dict, outputs: dict, results_dir: Path = None
) -> str:
    """
    Save test result to JSON file with timestamp.

    Args:
        test_name: Name of the test
        inputs: Test input parameters
        outputs: Test output/results
        results_dir: Directory to save results (defaults to test/test_results)

    Returns:
        Path to saved result file
    """

    if results_dir is None:
        results_dir = Path(__file__).parent.parent / "test_results"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = results_dir / filename

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

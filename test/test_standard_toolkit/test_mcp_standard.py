import pytest
import sys
import time
import json
import tempfile
import yaml
import threading
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import Config
from tools.mcp_base import MCPBase


class TestResultCollector:
    """
    Session-wide test result collector.

    Collects all test results from all servers and saves them to a single JSON file.

    Note: This is not a test class despite the name starting with 'Test'.
    It's a utility class for collecting test results.
    """
    __test__ = False  # Tell pytest this is not a test class

    def __init__(self):
        self.session_start_time = datetime.now().isoformat()
        self.timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")  # Only seconds precision

        # Use JSONL format - one test result per line
        self.all_results: Dict[str, List[Dict[str, Any]]] = {}  # server_name -> tests (for in-memory tracking)
        self.total_time_ms = 0.0
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0
        self._lock = threading.Lock()  # Thread-safe lock for in-memory data

    def add_test_result(
        self,
        server_name: str,
        tool_name: str,
        input_params: Dict[str, Any],
        success: bool,
        result: Dict[str, Any],
        error: str = None,
        duration_ms: float = 0.0
    ):
        """
        Add a single test result and immediately append to JSONL file (thread-safe).

        This method is thread-safe and can be called concurrently from multiple tests.
        Each test result is immediately written to the JSONL file as a separate line.
        """
        with self._lock:
            # Update in-memory tracking
            if server_name not in self.all_results:
                self.all_results[server_name] = []

            test_record = {
                "tool": tool_name,
                "input_params": input_params,
                "success": success,
                "result": result,
                "error": error,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                "server": server_name
            }

            self.all_results[server_name].append(test_record)

            self.total_time_ms += duration_ms
            self.total_tests += 1
            if success:
                self.total_passed += 1
            else:
                self.total_failed += 1

            # Immediately append to JSONL file
            self._append_to_jsonl(test_record)

    def _append_to_jsonl(self, test_record: Dict[str, Any]):
        """
        Append a single test result to the JSONL file (thread-safe).

        JSONL format: one JSON object per line.
        This is perfect for concurrent writes - each append is atomic.
        """
        output_dir = Path(__file__).parent.parent / "test_results"
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate JSONL filename
        filename = f"test_results_{self.timestamp_str}.jsonl"
        output_path = output_dir / filename

        # Append to JSONL file (atomic operation)
        try:
            with open(output_path, "a", encoding="utf-8") as f:
                # Write one JSON object per line
                json.dump(test_record, f, ensure_ascii=False)
                f.write("\n")  # Newline after each record
        except Exception as e:
            print(f"[ERROR] Failed to write to JSONL file: {e}")

    def generate_summary_report(self, output_dir: Path = None) -> Path:
        """
        Generate a human-readable summary JSON file from the JSONL data.

        This is called at the end of the test session to create a summary.
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "test_results"

        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Read all JSONL records
        jsonl_file = output_dir / f"test_results_{self.timestamp_str}.jsonl"
        if not jsonl_file.exists():
            print(f"[WARNING] JSONL file not found: {jsonl_file}")
            return None

        all_records = []
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            all_records.append(record)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[ERROR] Failed to read JSONL file: {e}")
            return None

        if not all_records:
            print(f"[WARNING] No test records found in JSONL file")
            return None

        # Group by server
        servers = {}
        for record in all_records:
            server = record.get("server", "unknown")
            if server not in servers:
                servers[server] = []
            servers[server].append(record)

        # Generate summary for each server
        servers_data = []
        for server_name, records in servers.items():
            passed = sum(1 for r in records if r.get("success", False))
            failed = len(records) - passed
            total_time = sum(r.get("duration_ms", 0) for r in records)

            servers_data.append({
                "server": server_name,
                "tests": records,
                "summary": {
                    "total": len(records),
                    "passed": passed,
                    "failed": failed,
                    "total_time_ms": total_time,
                    "avg_time_ms": total_time / len(records) if records else 0.0
                }
            })

        # Create summary data
        summary_data = {
            "session_start_time": self.session_start_time,
            "session_end_time": datetime.now().isoformat(),
            "servers": servers_data,
            "overall_summary": {
                "total_tests": len(all_records),
                "total_passed": sum(1 for r in all_records if r.get("success", False)),
                "total_failed": sum(1 for r in all_records if not r.get("success", False)),
                "total_time_ms": sum(r.get("duration_ms", 0) for r in all_records),
                "avg_time_ms": sum(r.get("duration_ms", 0) for r in all_records) / len(all_records) if all_records else 0.0
            }
        }

        # Save summary JSON
        summary_file = output_dir / f"test_results_{self.timestamp_str}_summary.json"
        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            return summary_file
        except Exception as e:
            print(f"[ERROR] Failed to write summary file: {e}")
            return None


class TestMCPServers:
    """Test suite for MCP servers"""

    @pytest.fixture(autouse=True)
    def setup(self, config_path, session_result_collector):
        """Setup test configuration"""
        # Reset config singleton for each test
        Config.reset_instance()

        self.config_path = config_path
        self.config = Config(config_file_path=config_path)
        self.config.load_config(override=True)
        self.mcp_base = None
        self.session_result_collector = session_result_collector

        yield

        # Cleanup after test
        Config.reset_instance()

    def _create_temp_config(self, server_name: str) -> str:
        """Create temporary config for testing a single server"""
        test_config = {
            "all_servers": self.config.get("all_servers", {}),
            "server_choice": [server_name],
        }

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{server_name}.yaml", delete=False
        )
        yaml.dump(test_config, temp_file, allow_unicode=True)
        temp_file.close()

        return temp_file.name

    @pytest.mark.asyncio
    async def test_mcp_tool(self, test_case: Dict[str, Any]):
        """
        Test a single MCP tool.

        This test is automatically parameterized by conftest.py
        based on JSON files in test_mcp_params directory.

        Args:
            test_case: Dictionary containing server, tool, and input_params
        """
        server_name = test_case["server"]
        tool_name = test_case["tool"]
        input_params = test_case["input_params"]

        # Verify server exists in config
        all_servers = self.config.get("all_servers", {})
        if server_name not in all_servers:
            pytest.skip(f"Server '{server_name}' not found in config")

        # Create temporary config
        temp_config = self._create_temp_config(server_name)

        # Variables to store test result
        success = False
        result_data = None
        error_message = None
        duration_ms = 0.0

        try:
            # Initialize MCP connection
            if not self.mcp_base:
                self.mcp_base = MCPBase(config_path=temp_config)

            # List available tools
            tools = await self.mcp_base.list_tools()
            tool_names = [tool.get("name") for tool in tools.values()]

            if tool_name not in tool_names:
                error_message = f"Tool '{tool_name}' not found. Available: {', '.join(tool_names)}"
                pytest.fail(error_message)

            # Find full tool name (server:tool format)
            tool_name_long = None
            for tool_info in tools.values():
                if tool_info.get("name") == tool_name:
                    tool_name_long = (
                        f"{tool_info.get('server')}:{tool_info.get('name')}"
                    )
                    break

            if not tool_name_long:
                error_message = f"Could not find full tool name for '{tool_name}'"
                pytest.fail(error_message)

            start_time = time.time()

            response = await self.mcp_base.get_tool_response(
                tool_name=tool_name_long, call_params=input_params
            )

            duration_ms = (time.time() - start_time) * 1000

            # Assert response exists
            assert response is not None, "Tool returned None response"

            # Get response data (no truncation for JSON storage)
            result_data = response.model_dump()
            success = True

            # Print detailed output for debugging (with truncation for console)
            print(f"\n{'='*60}")
            print(f"Tool: {tool_name}")
            print(f"Input: {input_params}")
            print(f"Duration: {duration_ms:.2f}ms")
            print(f"Output:")
            print(self._format_output(result_data, max_length=500))
            print(f"{'='*60}")

        except Exception as e:
            error_message = str(e)
            pytest.fail(f"Tool execution failed: {error_message}")

        finally:
            # Add test result to session collector (save complete data without truncation)
            self.session_result_collector.add_test_result(
                server_name=server_name,
                tool_name=tool_name,
                input_params=input_params,
                success=success,
                result=result_data,
                error=error_message,
                duration_ms=duration_ms
            )

            # Cleanup temp config
            try:
                Path(temp_config).unlink(missing_ok=True)
            except:
                pass

    def _format_output(self, content: Any, max_length: int = 500) -> str:
        """Format output with length limit"""
        if isinstance(content, (dict, list)):
            try:
                content_str = json.dumps(content, indent=2, ensure_ascii=False)
            except:
                content_str = str(content)
        else:
            content_str = str(content)

        if len(content_str) > max_length:
            return (
                content_str[:max_length]
                + f"\n... (truncated, total {len(content_str)} chars)"
            )

        return content_str

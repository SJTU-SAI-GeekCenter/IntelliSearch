#!/usr/bin/env python3
"""
Comprehensive test suite for IPython Backend Server.
Tests all API endpoints with various scenarios.
"""

import requests
import time
import json
import sys
from typing import Dict, Any, List

# Backend server configuration
BACKEND_URL = "http://localhost:8889"


class IPythonBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.created_sessions = []
        self.created_cells = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append(
            {"test": test_name, "status": status, "message": message}
        )
        print(f"[{status}] {test_name}")
        if message:
            print(f"    {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to the backend."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return {
                "status_code": response.status_code,
                "data": response.json() if response.text else {},
            }
        except Exception as e:
            return {"status_code": 0, "data": {"error": str(e)}}

    def test_01_health_check(self):
        """Test health check endpoint."""
        response = self.make_request("GET", "/health")
        passed = response["status_code"] == 200 and "status" in response["data"]
        self.log_test("Health Check", passed, response.get("data", {}).get("error", ""))

    def test_02_create_single_session(self):
        """Test creating a single session."""
        response = self.make_request("POST", "/sessions")
        passed = (
            response["status_code"] == 200
            and "session_id" in response["data"]
            and response["data"]["session_id"].startswith("session_")
        )

        if passed:
            self.created_sessions.append(response["data"]["session_id"])

        self.log_test(
            "Create Single Session",
            passed,
            f"Session ID: {response.get('data', {}).get('session_id', 'N/A')}",
        )

    def test_03_create_multiple_sessions(self):
        """Test creating multiple sessions."""
        session_ids = []
        for i in range(3):
            response = self.make_request("POST", "/sessions")
            if response["status_code"] == 200 and "session_id" in response["data"]:
                session_ids.append(response["data"]["session_id"])

        passed = len(session_ids) == 3
        if passed:
            self.created_sessions.extend(session_ids)

        self.log_test(
            "Create Multiple Sessions", passed, f"Created {len(session_ids)} sessions"
        )

    def test_04_list_all_sessions(self):
        """Test listing all sessions."""
        response = self.make_request("GET", "/sessions")
        passed = (
            response["status_code"] == 200
            and "sessions" in response["data"]
            and isinstance(response["data"]["sessions"], list)
        )

        self.log_test(
            "List All Sessions",
            passed,
            f"Found {len(response.get('data', {}).get('sessions', []))} sessions",
        )

    def test_05_get_specific_session(self):
        """Test getting a specific session."""
        if not self.created_sessions:
            self.log_test("Get Specific Session", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        response = self.make_request("GET", f"/sessions/{session_id}")
        passed = response["status_code"] == 200 and response["data"]["id"] == session_id

        self.log_test(
            "Get Specific Session",
            passed,
            f"Session {session_id}: {'Found' if passed else 'Not found'}",
        )

    def test_06_get_nonexistent_session(self):
        """Test getting a non-existent session."""
        response = self.make_request("GET", "/sessions/nonexistent_session")
        passed = response["status_code"] == 404
        self.log_test(
            "Get Non-existent Session",
            passed,
            f"Status code: {response['status_code']}",
        )

    def test_07_add_code_cell(self):
        """Test adding a code cell."""
        if not self.created_sessions:
            self.log_test("Add Code Cell", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        test_code = "x = 42\nprint('Hello from cell 1')"
        response = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": test_code}
        )

        passed = response["status_code"] == 200 and "cell_id" in response["data"]

        if passed:
            cell_id = response["data"]["cell_id"]
            self.created_cells.append((session_id, cell_id))

        self.log_test(
            "Add Code Cell",
            passed,
            f"Cell ID: {response.get('data', {}).get('cell_id', 'N/A')}",
        )

    def test_08_add_multiple_cells(self):
        """Test adding multiple cells to a session."""
        if not self.created_sessions:
            self.log_test("Add Multiple Cells", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        cell_ids = []

        test_codes = [
            "y = x * 2\nprint(f'y = {y}')",
            "import math\nresult = math.sqrt(y)\nprint(f'sqrt({y}) = {result}')",
            "# Final calculation\nfinal_result = x + y + result\nprint(f'Final: {final_result}')",
        ]

        for code in test_codes:
            response = self.make_request(
                "POST", f"/sessions/{session_id}/cells", {"code": code}
            )
            if response["status_code"] == 200 and "cell_id" in response["data"]:
                cell_ids.append((session_id, response["data"]["cell_id"]))

        passed = len(cell_ids) == 3
        if passed:
            self.created_cells.extend(cell_ids)

        self.log_test("Add Multiple Cells", passed, f"Added {len(cell_ids)} cells")

    def test_09_list_cells_in_session(self):
        """Test listing all cells in a session."""
        if not self.created_sessions:
            self.log_test("List Cells in Session", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        response = self.make_request("GET", f"/sessions/{session_id}/cells")

        passed = (
            response["status_code"] == 200
            and "cells" in response["data"]
            and isinstance(response["data"]["cells"], list)
        )

        self.log_test(
            "List Cells in Session",
            passed,
            f"Found {len(response.get('data', {}).get('cells', []))} cells",
        )

    def test_10_get_specific_cell(self):
        """Test getting a specific cell."""
        if not self.created_cells:
            self.log_test("Get Specific Cell", False, "No cells available")
            return

        session_id, cell_id = self.created_cells[0]
        response = self.make_request("GET", f"/sessions/{session_id}/cells/{cell_id}")

        passed = response["status_code"] == 200 and response["data"]["id"] == cell_id

        self.log_test(
            "Get Specific Cell",
            passed,
            f"Cell {cell_id}: {'Found' if passed else 'Not found'}",
        )

    def test_11_get_nonexistent_cell(self):
        """Test getting a non-existent cell."""
        if not self.created_sessions:
            self.log_test("Get Non-existent Cell", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        response = self.make_request("GET", f"/sessions/{session_id}/cells/999")

        passed = response["status_code"] == 404
        self.log_test(
            "Get Non-existent Cell", passed, f"Status code: {response['status_code']}"
        )

    def test_12_execute_simple_code(self):
        """Test executing simple Python code."""
        if not self.created_sessions:
            self.log_test("Execute Simple Code", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        test_code = "print('Hello, World!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')"

        response = self.make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": test_code}
        )

        passed = (
            response["status_code"] == 200
            and response["data"]["success"]
            and "Hello, World!" in response["data"]["result"]
            and "2 + 2 = 4" in response["data"]["result"]
        )

        self.log_test(
            "Execute Simple Code",
            passed,
            f"Success: {response.get('data', {}).get('success', False)}",
        )

    def test_13_execute_code_with_variables(self):
        """Test executing code that uses variables from previous executions."""
        if not self.created_sessions:
            self.log_test("Execute Code with Variables", False, "No sessions available")
            return

        session_id = self.created_sessions[0]

        # First execution to set variable
        first_code = "shared_var = 'Hello from previous execution'"
        first_response = self.make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": first_code}
        )

        # Second execution to use the variable
        second_code = "print(f'Message: {shared_var}')\nnew_var = shared_var.upper()\nprint(f'Uppercase: {new_var}')"
        second_response = self.make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": second_code}
        )

        passed = (
            first_response["status_code"] == 200
            and first_response["data"]["success"]
            and second_response["status_code"] == 200
            and second_response["data"]["success"]
            and "Hello from previous execution" in second_response["data"]["result"]
        )

        self.log_test(
            "Execute Code with Variables", passed, "Variable persistence test"
        )

    def test_14_execute_code_with_error(self):
        """Test executing code that produces an error."""
        if not self.created_sessions:
            self.log_test("Execute Code with Error", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        error_code = "print(undefined_variable)"

        response = self.make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": error_code}
        )

        passed = (
            response["status_code"] == 200
            and not response["data"]["success"]
            and "Error" in response["data"]["result"]
        )

        self.log_test(
            "Execute Code with Error", passed, f"Error handled correctly: {passed}"
        )

    def test_15_execute_code_with_imports(self):
        """Test executing code with imports."""
        if not self.created_sessions:
            self.log_test("Execute Code with Imports", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        import_code = """
import random
import datetime
numbers = [random.randint(1, 10) for _ in range(5)]
print(f"Random numbers: {numbers}")
print(f"Current time: {datetime.datetime.now()}")
"""

        response = self.make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": import_code}
        )

        passed = response["status_code"] == 200 and response["data"]["success"]

        self.log_test(
            "Execute Code with Imports", passed, f"Import test successful: {passed}"
        )

    def test_16_delete_cell(self):
        """Test deleting a cell."""
        if len(self.created_cells) < 2:
            self.log_test("Delete Cell", False, "Not enough cells available")
            return

        session_id, cell_id = self.created_cells[1]  # Delete the second cell
        response = self.make_request(
            "DELETE", f"/sessions/{session_id}/cells/{cell_id}"
        )

        passed = response["status_code"] == 200

        if passed:
            # Verify cell is actually deleted
            verify_response = self.make_request(
                "GET", f"/sessions/{session_id}/cells/{cell_id}"
            )
            passed = verify_response["status_code"] == 404
            if passed:
                self.created_cells.remove((session_id, cell_id))

        self.log_test(
            "Delete Cell",
            passed,
            f"Cell {cell_id}: {'Deleted' if passed else 'Not deleted'}",
        )

    def test_17_delete_nonexistent_cell(self):
        """Test deleting a non-existent cell."""
        if not self.created_sessions:
            self.log_test("Delete Non-existent Cell", False, "No sessions available")
            return

        session_id = self.created_sessions[0]
        response = self.make_request("DELETE", f"/sessions/{session_id}/cells/999")

        passed = response["status_code"] == 404
        self.log_test(
            "Delete Non-existent Cell",
            passed,
            f"Status code: {response['status_code']}",
        )

    def test_18_delete_session(self):
        """Test deleting a session."""
        if len(self.created_sessions) < 2:
            self.log_test("Delete Session", False, "Not enough sessions available")
            return

        session_id = self.created_sessions[-1]  # Delete the last created session
        response = self.make_request("DELETE", f"/sessions/{session_id}")

        passed = response["status_code"] == 200

        if passed:
            # Verify session is actually deleted
            verify_response = self.make_request("GET", f"/sessions/{session_id}")
            passed = verify_response["status_code"] == 404
            if passed:
                self.created_sessions.remove(session_id)
                # Remove associated cells
                self.created_cells = [
                    (s, c) for s, c in self.created_cells if s != session_id
                ]

        self.log_test(
            "Delete Session",
            passed,
            f"Session {session_id}: {'Deleted' if passed else 'Not deleted'}",
        )

    def test_19_delete_nonexistent_session(self):
        """Test deleting a non-existent session."""
        response = self.make_request("DELETE", "/sessions/nonexistent_session")

        passed = response["status_code"] == 404
        self.log_test(
            "Delete Non-existent Session",
            passed,
            f"Status code: {response['status_code']}",
        )

    def test_20_complex_calculation_workflow(self):
        """Test a complex workflow with multiple steps and variable sharing."""
        if not self.created_sessions:
            self.log_test(
                "Complex Calculation Workflow", False, "No sessions available"
            )
            return

        session_id = self.created_sessions[0]

        # Step 1: Initialize data
        step1_code = """
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(f"Initial data: {data}")
"""

        # Step 2: Calculate statistics
        step2_code = """
import statistics
mean_val = statistics.mean(data)
median_val = statistics.median(data)
std_val = statistics.stdev(data)
print(f"Mean: {mean_val}")
print(f"Median: {median_val}")
print(f"Std Dev: {std_val}")
"""

        # Step 3: Transform data
        step3_code = """
normalized_data = [(x - mean_val) / std_val for x in data]
print(f"Normalized data: {[round(x, 3) for x in normalized_data]}")
"""

        # Execute all steps
        responses = []
        for i, code in enumerate([step1_code, step2_code, step3_code], 1):
            response = self.make_request(
                "POST", f"/sessions/{session_id}/execute", {"code": code}
            )
            responses.append(response)

        passed = all(
            r["status_code"] == 200 and r["data"]["success"] for r in responses
        )

        self.log_test(
            "Complex Calculation Workflow",
            passed,
            f"Multi-step calculation: {'Successful' if passed else 'Failed'}",
        )

    def test_21_concurrent_sessions(self):
        """Test operations on multiple concurrent sessions."""
        # Create two sessions
        session1_response = self.make_request("POST", "/sessions")
        session2_response = self.make_request("POST", "/sessions")

        if (
            session1_response["status_code"] != 200
            or session2_response["status_code"] != 200
        ):
            self.log_test("Concurrent Sessions", False, "Failed to create sessions")
            return

        session1_id = session1_response["data"]["session_id"]
        session2_id = session2_response["data"]["session_id"]

        # Execute different code in each session
        code1 = "session_var = 'Session 1 data'\nprint(f'Session 1: {session_var}')"
        code2 = "session_var = 'Session 2 data'\nprint(f'Session 2: {session_var}')"

        response1 = self.make_request(
            "POST", f"/sessions/{session1_id}/execute", {"code": code1}
        )
        response2 = self.make_request(
            "POST", f"/sessions/{session2_id}/execute", {"code": code2}
        )

        # Verify sessions are independent
        verify1 = self.make_request(
            "POST",
            f"/sessions/{session1_id}/execute",
            {"code": "print(f'Verify 1: {session_var}')"},
        )
        verify2 = self.make_request(
            "POST",
            f"/sessions/{session2_id}/execute",
            {"code": "print(f'Verify 2: {session_var}')"},
        )

        passed = (
            response1["status_code"] == 200
            and response1["data"]["success"]
            and response2["status_code"] == 200
            and response2["data"]["success"]
            and verify1["status_code"] == 200
            and verify1["data"]["success"]
            and verify2["status_code"] == 200
            and verify2["data"]["success"]
            and "Session 1 data" in verify1["data"]["result"]
            and "Session 2 data" in verify2["data"]["result"]
        )

        # Clean up
        self.make_request("DELETE", f"/sessions/{session1_id}")
        self.make_request("DELETE", f"/sessions/{session2_id}")

        self.log_test("Concurrent Sessions", passed, "Session isolation test")

    def test_22_large_code_execution(self):
        """Test executing a large amount of code."""
        if not self.created_sessions:
            self.log_test("Large Code Execution", False, "No sessions available")
            return

        session_id = self.created_sessions[0]

        # Generate a large code block with simpler fibonacci to avoid recursion issues
        large_code = """
# Fibonacci sequence calculation (iterative version)
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# Calculate first 10 Fibonacci numbers
fib_results = []
for i in range(10):
    fib_results.append(fibonacci(i))

print(f"First 10 Fibonacci numbers: {fib_results}")

# Matrix operations
matrix_a = [[1, 2], [3, 4]]
matrix_b = [[5, 6], [7, 8]]

def matrix_multiply(a, b):
    result = [[0, 0], [0, 0]]
    for i in range(2):
        for j in range(2):
            for k in range(2):
                result[i][j] += a[i][k] * b[k][j]
    return result

matrix_result = matrix_multiply(matrix_a, matrix_b)
print(f"Matrix multiplication result: {matrix_result}")

# Additional calculations
total = sum(fib_results)
print(f"Sum of Fibonacci numbers: {total}")
"""

        response = self.make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": large_code}
        )

        result_text = response.get("data", {}).get("result", "")

        passed = (
            response["status_code"] == 200
            and response["data"]["success"]
            and "Fibonacci numbers" in result_text
            and "Matrix multiplication" in result_text
            and "Sum of Fibonacci" in result_text
        )

        self.log_test("Large Code Execution", passed, f"Large code execution - result contains expected outputs: {passed}")

    def test_23_execute_all_cells(self):
        """Test executing all cells in a session."""
        # Create a fresh session for this test to avoid interference from previous tests
        session_response = self.make_request("POST", "/sessions")
        if session_response["status_code"] != 200:
            self.log_test("Execute All Cells", False, "Failed to create session")
            return

        session_id = session_response["data"]["session_id"]
        self.created_sessions.append(session_id)

        # Add multiple cells with dependent code
        cells_data = [
            "base_value = 10\nprint(f'Set base_value: {base_value}')",
            "multiplier = 5\nresult = base_value * multiplier\nprint(f'base_value * multiplier = {result}')",
            "final_result = result + 100\nprint(f'Final result: {final_result}')",
        ]

        for code in cells_data:
            self.make_request("POST", f"/sessions/{session_id}/cells", {"code": code})

        # Execute all cells
        response = self.make_request("POST", f"/sessions/{session_id}/execute-all")

        passed = (
            response["status_code"] == 200
            and response["data"]["success"]
            and "Cell" in response["data"]["result"]
            and "Final result: 150" in response["data"]["result"]
        )

        self.log_test("Execute All Cells", passed, "Sequential execution of all cells")

    def test_24_execute_specific_cell(self):
        """Test executing a specific cell in a session."""
        if not self.created_sessions:
            self.log_test("Execute Specific Cell", False, "No sessions available")
            return

        session_id = self.created_sessions[0]

        # Add cells
        cell1_code = "cell_var = 'initial'\nprint(f'Cell 1: {cell_var}')"
        cell2_code = "cell_var = 'modified'\nprint(f'Cell 2: {cell_var}')"

        response1 = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": cell1_code}
        )
        response2 = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": cell2_code}
        )

        if response1["status_code"] != 200 or response2["status_code"] != 200:
            self.log_test("Execute Specific Cell", False, "Failed to add cells")
            return

        cell2_id = response2["data"]["cell_id"]

        # Execute only cell 2
        response = self.make_request(
            "POST", f"/sessions/{session_id}/execute-cell/{cell2_id}"
        )

        passed = (
            response["status_code"] == 200
            and response["data"]["success"]
            and "Cell 2: modified" in response["data"]["result"]
        )

        self.log_test(
            "Execute Specific Cell", passed, f"Execution of cell {cell2_id} only"
        )

    def test_25_get_execution_status(self):
        """Test getting execution status of a session."""
        if not self.created_sessions:
            self.log_test("Get Execution Status", False, "No sessions available")
            return

        session_id = self.created_sessions[0]

        # Add a cell and execute it through execute-cell endpoint
        cell_response = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": "status_var = 42\nprint('Cell executed')"}
        )

        if cell_response["status_code"] != 200:
            self.log_test("Get Execution Status", False, "Failed to add cell")
            return

        cell_id = cell_response["data"]["cell_id"]

        # Execute the specific cell
        self.make_request(
            "POST", f"/sessions/{session_id}/execute-cell/{cell_id}"
        )

        # Get execution status
        response = self.make_request("GET", f"/sessions/{session_id}/execution-status")

        passed = (
            response["status_code"] == 200
            and "total_cells" in response["data"]
            and "executed_cells" in response["data"]
            and "variables" in response["data"]
            and "cells" in response["data"]
        )

        if passed:
            # Check if variables are tracked
            variables = response["data"]["variables"]
            has_status_var = "status_var" in variables

            # Check if cell is marked as executed
            cell_executed = False
            for cell in response["data"]["cells"]:
                if cell["cell_id"] == cell_id:
                    cell_executed = cell["executed"]
                    break

            final_passed = passed and has_status_var and cell_executed
            self.log_test(
                "Get Execution Status",
                final_passed,
                f"Tracked {len(variables)} variables, cell executed: {cell_executed}",
            )
        else:
            self.log_test(
                "Get Execution Status", False, "Failed to get execution status"
            )

    def test_26_execution_status_with_empty_session(self):
        """Test execution status with an empty session."""
        if not self.created_sessions:
            self.log_test(
                "Execution Status with Empty Session", False, "No sessions available"
            )
            return

        # Create a new empty session
        session_response = self.make_request("POST", "/sessions")
        if session_response["status_code"] != 200:
            self.log_test(
                "Execution Status with Empty Session", False, "Failed to create session"
            )
            return

        empty_session_id = session_response["data"]["session_id"]
        self.created_sessions.append(empty_session_id)

        # Get execution status of empty session
        response = self.make_request(
            "GET", f"/sessions/{empty_session_id}/execution-status"
        )

        passed = (
            response["status_code"] == 200
            and response["data"]["total_cells"] == 0
            and response["data"]["executed_cells"] == 0
            and len(response["data"]["variables"]) == 0
        )

        self.log_test(
            "Execution Status with Empty Session",
            passed,
            "Empty session status tracking",
        )

    def test_27_execute_all_cells_empty_session(self):
        """Test executing all cells in an empty session."""
        if not self.created_sessions:
            self.log_test(
                "Execute All Cells Empty Session", False, "No sessions available"
            )
            return

        # Use the empty session from previous test
        empty_session_id = self.created_sessions[-1]

        response = self.make_request(
            "POST", f"/sessions/{empty_session_id}/execute-all"
        )

        passed = (
            response["status_code"] == 200
            and response["data"]["success"]
            and "No cells found" in response["data"]["result"]
        )

        self.log_test(
            "Execute All Cells Empty Session",
            passed,
            "Empty session execution handling",
        )

    def test_28_cell_execution_state_persistence(self):
        """Test that cell execution state is properly tracked."""
        if not self.created_sessions:
            self.log_test(
                "Cell Execution State Persistence", False, "No sessions available"
            )
            return

        session_id = self.created_sessions[0]

        # Add a cell
        cell_code = "persist_var = 'persistent'\nprint('Cell executed')"
        cell_response = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": cell_code}
        )

        if cell_response["status_code"] != 200:
            self.log_test(
                "Cell Execution State Persistence", False, "Failed to add cell"
            )
            return

        cell_id = cell_response["data"]["cell_id"]

        # Check initial status (should not be executed)
        status_before = self.make_request(
            "GET", f"/sessions/{session_id}/execution-status"
        )
        before_executed = False
        if status_before["status_code"] == 200:
            for cell in status_before["data"]["cells"]:
                if cell["cell_id"] == cell_id:
                    before_executed = cell["executed"]
                    break

        # Execute the specific cell
        exec_response = self.make_request(
            "POST", f"/sessions/{session_id}/execute-cell/{cell_id}"
        )

        # Check status after execution
        status_after = self.make_request(
            "GET", f"/sessions/{session_id}/execution-status"
        )
        after_executed = False
        if status_after["status_code"] == 200:
            for cell in status_after["data"]["cells"]:
                if cell["cell_id"] == cell_id:
                    after_executed = cell["executed"]
                    break

        passed = (
            not before_executed
            and after_executed
            and exec_response["status_code"] == 200
            and exec_response["data"]["success"]
        )

        self.log_test(
            "Cell Execution State Persistence",
            passed,
            f"Cell {cell_id}: {before_executed} -> {after_executed}",
        )

    def test_29_variable_persistence_across_cell_executions(self):
        """Test that variables persist across different cell executions."""
        if not self.created_sessions:
            self.log_test(
                "Variable Persistence Across Cell Executions",
                False,
                "No sessions available",
            )
            return

        session_id = self.created_sessions[0]

        # Add two dependent cells
        cell1_code = "calc_base = 5\ncalc_multiplier = 3"
        cell2_code = "final_calc = calc_base * calc_multiplier\nprint(f'Calculation result: {final_calc}')"

        cell1_response = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": cell1_code}
        )
        cell2_response = self.make_request(
            "POST", f"/sessions/{session_id}/cells", {"code": cell2_code}
        )

        if cell1_response["status_code"] != 200 or cell2_response["status_code"] != 200:
            self.log_test(
                "Variable Persistence Across Cell Executions",
                False,
                "Failed to add cells",
            )
            return

        cell1_id = cell1_response["data"]["cell_id"]
        cell2_id = cell2_response["data"]["cell_id"]

        # Execute first cell
        exec1_response = self.make_request(
            "POST", f"/sessions/{session_id}/execute-cell/{cell1_id}"
        )

        # Execute second cell (should use variables from first)
        exec2_response = self.make_request(
            "POST", f"/sessions/{session_id}/execute-cell/{cell2_id}"
        )

        passed = (
            exec1_response["status_code"] == 200
            and exec1_response["data"]["success"]
            and exec2_response["status_code"] == 200
            and exec2_response["data"]["success"]
            and "Calculation result: 15" in exec2_response["data"]["result"]
        )

        self.log_test(
            "Variable Persistence Across Cell Executions",
            passed,
            "Variables shared across cell executions",
        )

    def cleanup(self):
        """Clean up all created sessions and cells."""
        print("\nCleaning up test resources...")

        # Delete all remaining sessions
        for session_id in self.created_sessions[
            :
        ]:  # Use slice to avoid modification during iteration
            try:
                self.make_request("DELETE", f"/sessions/{session_id}")
                print(f"Deleted session: {session_id}")
            except Exception as e:
                print(f"Failed to delete session {session_id}: {e}")

        self.created_sessions.clear()
        self.created_cells.clear()

    def run_all_tests(self):
        """Run all tests and generate a summary."""
        print("Starting IPython Backend Test Suite")
        print("=" * 50)

        # Check if server is running
        health_response = self.make_request("GET", "/health")
        if health_response["status_code"] != 200:
            print("❌ Server is not running. Start the server first.")
            print("Run: python3 ipython_backend.py")
            return

        print("✅ Server is running. Starting tests...\n")

        # Run all test methods
        test_methods = [
            method
            for method in dir(self)
            if method.startswith("test_") and callable(getattr(self, method))
        ]

        for test_method_name in test_methods:
            try:
                test_method = getattr(self, test_method_name)
                test_method()
                time.sleep(0.1)  # Small delay between tests
            except Exception as e:
                self.log_test(test_method_name, False, f"Test crashed: {str(e)}")

        # Generate summary
        print("\n" + "=" * 50)
        print("Test Summary:")

        passed_count = sum(
            1 for result in self.test_results if result["status"] == "PASS"
        )
        total_count = len(self.test_results)

        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_symbol} {result['test']}")

        print(f"\nResults: {passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total_count - passed_count} test(s) failed")

        # Cleanup
        self.cleanup()

        return passed_count == total_count


def main():
    """Main function to run tests."""
    tester = IPythonBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Debug test for IPython backend to isolate issues with code execution
"""

import requests
import json

BACKEND_URL = "http://localhost:8889"

def test_basic_execution():
    """Test basic code execution to ensure backend is working"""
    print("=== Testing Basic Code Execution ===")

    try:
        # Create session
        session_response = requests.post(f"{BACKEND_URL}/sessions",
                                        headers={"Content-Type": "application/json"})
        print(f"Create session status: {session_response.status_code}")

        if session_response.status_code != 200:
            print(f"Session creation failed: {session_response.text}")
            return False

        session_id = session_response.json()["session_id"]
        print(f"Created session: {session_id}")

        # Test simple variable assignment
        simple_code = "x = 42\nprint(f'x = {x}')"
        exec_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/execute",
                                     headers={"Content-Type": "application/json"},
                                     json={"code": simple_code})

        print(f"Simple execution status: {exec_response.status_code}")
        if exec_response.status_code == 200:
            result = exec_response.json()
            print(f"Success: {result['success']}")
            print(f"Result: {result['result'][:200]}...")
        else:
            print(f"Execution failed: {exec_response.text}")
            return False

        # Test function definition and usage
        func_code = """
def test_func(n):
    return n * 2

result = test_func(5)
print(f'test_func(5) = {result}')
"""

        func_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/execute",
                                    headers={"Content-Type": "application/json"},
                                    json={"code": func_code})

        print(f"Function execution status: {func_response.status_code}")
        if func_response.status_code == 200:
            result = func_response.json()
            print(f"Success: {result['success']}")
            print(f"Result: {result['result'][:200]}...")
        else:
            print(f"Function execution failed: {func_response.text}")

        # Test fibonacci function (like in Large Code Execution test)
        fib_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

fib_result = fibonacci(5)
print(f'fibonacci(5) = {fib_result}')
"""

        fib_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/execute",
                                    headers={"Content-Type": "application/json"},
                                    json={"code": fib_code})

        print(f"Fibonacci execution status: {fib_response.status_code}")
        if fib_response.status_code == 200:
            result = fib_response.json()
            print(f"Success: {result['success']}")
            print(f"Result: {result['result'][:200]}...")

            # Check if result contains expected output
            if "fibonacci(5) = 5" in result['result']:
                print("✅ Fibonacci test PASSED")
                return True
            else:
                print("❌ Fibonacci test FAILED - unexpected output")
                print(f"Expected: 'fibonacci(5) = 5'")
                print(f"Got: {result['result']}")
                return False
        else:
            print(f"Fibonacci execution failed: {fib_response.text}")
            return False

    except Exception as e:
        print(f"Test failed with exception: {e}")
        return False
    finally:
        # Cleanup
        try:
            requests.delete(f"{BACKEND_URL}/sessions/{session_id}")
        except:
            pass

def test_cell_execution():
    """Test cell-based execution"""
    print("\n=== Testing Cell Execution ===")

    try:
        # Create session
        session_response = requests.post(f"{BACKEND_URL}/sessions",
                                        headers={"Content-Type": "application/json"})

        if session_response.status_code != 200:
            print(f"Session creation failed: {session_response.text}")
            return False

        session_id = session_response.json()["session_id"]
        print(f"Created session: {session_id}")

        # Add cells
        cell1_code = "base_value = 10\nprint(f'Set base_value: {base_value}')"
        cell2_code = "multiplier = 5\nresult = base_value * multiplier\nprint(f'base_value * multiplier = {result}')"
        cell3_code = "final_result = result + 100\nprint(f'Final result: {final_result}')"

        cells = []
        for i, code in enumerate([cell1_code, cell2_code, cell3_code], 1):
            cell_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/cells",
                                         headers={"Content-Type": "application/json"},
                                         json={"code": code})
            print(f"Add cell {i} status: {cell_response.status_code}")

            if cell_response.status_code == 200:
                cell_id = cell_response.json()["cell_id"]
                cells.append(cell_id)
                print(f"Cell {i} ID: {cell_id}")
            else:
                print(f"Failed to add cell {i}: {cell_response.text}")
                return False

        # Execute all cells
        exec_all_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/execute-all",
                                         headers={"Content-Type": "application/json"})

        print(f"Execute all cells status: {exec_all_response.status_code}")
        if exec_all_response.status_code == 200:
            result = exec_all_response.json()
            print(f"Success: {result['success']}")
            print(f"Result preview: {result['result'][:300]}...")

            # Check if result contains expected output
            if "Final result: 150" in result['result']:
                print("✅ Execute All Cells test PASSED")
                return True
            else:
                print("❌ Execute All Cells test FAILED - unexpected output")
                print(f"Expected: 'Final result: 150'")
                print(f"Got result: {result['result']}")
                return False
        else:
            print(f"Execute all cells failed: {exec_all_response.text}")
            return False

    except Exception as e:
        print(f"Test failed with exception: {e}")
        return False
    finally:
        # Cleanup
        try:
            requests.delete(f"{BACKEND_URL}/sessions/{session_id}")
        except:
            pass

if __name__ == "__main__":
    print("Testing IPython Backend...")

    basic_passed = test_basic_execution()
    cell_passed = test_cell_execution()

    print(f"\n=== SUMMARY ===")
    print(f"Basic Execution Test: {'PASSED' if basic_passed else 'FAILED'}")
    print(f"Cell Execution Test: {'PASSED' if cell_passed else 'FAILED'}")

    if basic_passed and cell_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")
#!/usr/bin/env python3
"""
Quick test to verify Execute All Cells fix
"""

import requests
import json

BACKEND_URL = "http://localhost:8889"

def test_execute_all_cells():
    """Test the Execute All Cells functionality"""
    print("=== Testing Execute All Cells Fix ===")

    try:
        # Create a fresh session
        session_response = requests.post(f"{BACKEND_URL}/sessions",
                                        headers={"Content-Type": "application/json"})
        print(f"Create session status: {session_response.status_code}")

        if session_response.status_code != 200:
            print(f"Session creation failed: {session_response.text}")
            return False

        session_id = session_response.json()["session_id"]
        print(f"Created session: {session_id}")

        # Add cells with dependent code (exact same as in the test)
        cells_data = [
            "base_value = 10\nprint(f'Set base_value: {base_value}')",
            "multiplier = 5\nresult = base_value * multiplier\nprint(f'base_value * multiplier = {result}')",
            "final_result = result + 100\nprint(f'Final result: {final_result}')",
        ]

        for i, code in enumerate(cells_data, 1):
            cell_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/cells",
                                         headers={"Content-Type": "application/json"},
                                         json={"code": code})
            print(f"Add cell {i} status: {cell_response.status_code}")

            if cell_response.status_code != 200:
                print(f"Failed to add cell {i}: {cell_response.text}")
                return False

            cell_id = cell_response.json()["cell_id"]
            print(f"Cell {i} ID: {cell_id}")

        # Execute all cells
        exec_all_response = requests.post(f"{BACKEND_URL}/sessions/{session_id}/execute-all",
                                         headers={"Content-Type": "application/json"})

        print(f"Execute all cells status: {exec_all_response.status_code}")
        if exec_all_response.status_code == 200:
            result = exec_all_response.json()
            print(f"Success: {result['success']}")
            print(f"Result preview: {result['result'][:200]}...")

            # Check if result contains expected output
            if "Final result: 150" in result['result']:
                print("✅ Execute All Cells test PASSED - Found 'Final result: 150'")
                print("✅ Cell dependency working correctly!")
                return True
            else:
                print("❌ Execute All Cells test FAILED")
                print(f"Expected: 'Final result: 150'")
                print(f"Actual result preview: {result['result'][:300]}...")
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
            print("✅ Session cleaned up")
        except:
            pass

if __name__ == "__main__":
    success = test_execute_all_cells()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
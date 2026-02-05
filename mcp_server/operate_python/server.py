import requests
import os
import asyncio
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Configuration for the IPython backend server
PORT = int(os.environ.get("TOOL_BACKEND_IPYTHON_PORT", 39256))
BACKEND_URL = f"http://localhost:39256{PORT}"
mcp = FastMCP("Python-Operator")


def make_request(
    method: str, endpoint: str, data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Make HTTP request to the IPython backend server.

    Args:
        method: HTTP method (GET, POST, DELETE)
        endpoint: API endpoint path
        data: Optional request body data

    Returns:
        Response JSON data

    Raises:
        Exception: If request fails
    """
    url = f"{BACKEND_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to IPython backend: {str(e)}")


@mcp.tool()
async def create_ipython_session() -> str:
    """
    Create a new IPython session for code execution.

    Each session maintains its own variable state and code cells.
    Sessions are isolated from each other and persist until explicitly deleted.

    Returns:
        Session ID that can be used for subsequent operations

    Example:
        session_id = create_ipython_session()
        print(f"Created session: {session_id}")
    """
    try:
        response = make_request("POST", "/sessions")
        return response["session_id"]
    except Exception as e:
        return f"Error creating session: {str(e)}"


@mcp.tool()
async def list_ipython_sessions() -> str:
    """
    List all active IPython sessions.

    Returns information about all sessions including their IDs, creation time,
    and the number of cells in each session.

    Returns:
        JSON string containing list of sessions with their metadata

    Example:
        sessions = list_ipython_sessions()
        print(sessions)  # Shows all active sessions
    """
    try:
        response = make_request("GET", "/sessions")
        sessions = response.get("sessions", [])

        if not sessions:
            return "No active sessions found"

        result = "Active IPython sessions:\n"
        for session in sessions:
            result += f"  Session ID: {session['id']}\n"
            result += f"    Created: {session['created_at']}\n"
            result += f"    Cells: {session['cell_count']}\n"
            result += f"    Next cell ID: {session['next_cell_id']}\n\n"

        return result.strip()

    except Exception as e:
        return f"Error listing sessions: {str(e)}"


@mcp.tool()
async def get_session_info(session_id: str) -> str:
    """
    Get detailed information about a specific IPython session.

    Args:
        session_id: The ID of the session to retrieve information for

    Returns:
        Detailed session information including metadata and variable names

    Example:
        info = get_session_info("session_1")
        print(info)  # Shows session details
    """
    try:
        response = make_request("GET", f"/sessions/{session_id}")

        result = f"Session Information:\n"
        result += f"  ID: {response['id']}\n"
        result += f"  Created: {response['created_at']}\n"
        result += f"  Cell count: {response['cell_count']}\n"
        result += f"  Next cell ID: {response['next_cell_id']}\n"
        result += f"  Variables: {', '.join(response['variables']) if response['variables'] else 'None'}\n"

        return result.strip()

    except Exception as e:
        return f"Error getting session info: {str(e)}"


@mcp.tool()
async def delete_ipython_session(session_id: str) -> str:
    """
    Delete an IPython session and clean up all its resources.

    This will permanently remove the session and all its cells, variables,
    and execution history. This action cannot be undone.

    Args:
        session_id: The ID of the session to delete

    Returns:
        Confirmation message

    Example:
        result = delete_ipython_session("session_1")
        print(result)  # Confirms deletion
    """
    try:
        response = make_request("DELETE", f"/sessions/{session_id}")
        return response["message"]
    except Exception as e:
        return f"Error deleting session: {str(e)}"


@mcp.tool()
async def add_code_cell(session_id: str, code: str) -> str:
    """
    Add a new code cell to an IPython session.

    Cells are stored in the session and can be referenced by their ID.
    Each cell has a unique ID that increments within the session.

    Args:
        session_id: The ID of the session to add the cell to
        code: The Python code to add to the cell

    Returns:
        Cell ID and confirmation message

    Example:
        cell_id = add_code_cell("session_1", "x = 42\nprint(x)")
        print(cell_id)  # Shows the new cell ID
    """
    try:
        response = make_request("POST", f"/sessions/{session_id}/cells", {"code": code})
        return f"Cell {response['cell_id']} added to session {response['session_id']}"
    except Exception as e:
        return f"Error adding cell: {str(e)}"


@mcp.tool()
async def list_session_cells(session_id: str) -> str:
    """
    List all code cells in an IPython session.

    Returns information about all cells in the session including their IDs,
    code content, creation time, and execution status.

    Args:
        session_id: The ID of the session to list cells for

    Returns:
        Detailed information about all cells in the session

    Example:
        cells = list_session_cells("session_1")
        print(cells)  # Shows all cells in the session
    """
    try:
        response = make_request("GET", f"/sessions/{session_id}/cells")
        cells = response.get("cells", [])

        if not cells:
            return f"No cells found in session {session_id}"

        result = f"Cells in session {session_id}:\n"
        for cell in cells:
            result += f"  Cell ID: {cell['id']}\n"
            result += f"    Created: {cell['created_at']}\n"
            result += f"    Executed: {cell['executed']}\n"
            result += f"    Code:\n{cell['code']}\n"
            if cell["execution_result"]:
                result += f"    Result:\n{cell['execution_result']}\n"
            result += "\n"

        return result.strip()

    except Exception as e:
        return f"Error listing cells: {str(e)}"


@mcp.tool()
async def get_cell_info(session_id: str, cell_id: int) -> str:
    """
    Get detailed information about a specific code cell.

    Args:
        session_id: The ID of the session containing the cell
        cell_id: The ID of the cell to retrieve information for

    Returns:
        Detailed cell information including code and execution results

    Example:
        info = get_cell_info("session_1", 1)
        print(info)  # Shows cell details
    """
    try:
        response = make_request("GET", f"/sessions/{session_id}/cells/{cell_id}")

        result = f"Cell Information:\n"
        result += f"  ID: {response['id']}\n"
        result += f"  Session: {session_id}\n"
        result += f"  Created: {response['created_at']}\n"
        result += f"  Executed: {response['executed']}\n"
        result += f"  Code:\n{response['code']}\n"

        if response["execution_result"]:
            result += f"  Execution Result:\n{response['execution_result']}\n"
        else:
            result += "  Execution Result: Not yet executed\n"

        return result.strip()

    except Exception as e:
        return f"Error getting cell info: {str(e)}"


@mcp.tool()
async def delete_cell(session_id: str, cell_id: int) -> str:
    """
    Delete a specific code cell from an IPython session.

    This will permanently remove the cell and its execution history.
    The cell ID cannot be reused within the same session.

    Args:
        session_id: The ID of the session containing the cell
        cell_id: The ID of the cell to delete

    Returns:
        Confirmation message

    Example:
        result = delete_cell("session_1", 1)
        print(result)  # Confirms cell deletion
    """
    try:
        response = make_request("DELETE", f"/sessions/{session_id}/cells/{cell_id}")
        return response["message"]
    except Exception as e:
        return f"Error deleting cell: {str(e)}"


@mcp.tool()
async def execute_python_code(session_id: str, code: str) -> str:
    """
    Execute Python code in an IPython session.

    The code executes with access to all variables defined in previous executions
    within the same session. Variables persist across executions and can be
    referenced in subsequent code.

    Args:
        session_id: The ID of the session to execute code in
        code: The Python code to execute

    Returns:
        Execution result including stdout, stderr, and any error messages

    Example:
        result = execute_python_code("session_1", "x = x + 1\nprint(f'x = {x}')")
        print(result)  # Shows execution output
    """
    try:
        response = make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": code}
        )

        if response["success"]:
            return f"✅ Execution successful:\n{response['result']}"
        else:
            return f"❌ Execution failed:\n{response['result']}"

    except Exception as e:
        return f"Error executing code: {str(e)}"


@mcp.tool()
async def check_ipython_health() -> str:
    """
    Check the health status of the IPython backend server.

    Returns:
        Server health status and number of active sessions

    Example:
        health = check_ipython_health()
        print(health)  # Shows server status
    """
    try:
        response = make_request("GET", "/health")
        status = response["status"]
        active_sessions = response["active_sessions"]

        return f"IPython Backend Status: {status}\nActive Sessions: {active_sessions}"

    except Exception as e:
        return f"❌ IPython backend is not responding: {str(e)}"


@mcp.tool()
async def execute_session_all_cells(session_id: str) -> str:
    """
    Execute all cells in a session in order.

    This tool executes all cells in the session sequentially, from cell 1 to the last cell.
    Variables defined in earlier cells are available to subsequent cells, maintaining
    the persistent state across the entire session. The execution stops if any cell fails.

    Args:
        session_id: The ID of the session whose cells should be executed

    Returns:
        Combined execution results from all cells, with clear cell separation

    Example:
        # First, add multiple cells to a session
        add_code_cell("session_1", "x = 10")
        add_code_cell("session_1", "y = x * 2")
        add_code_cell("session_1", "print(f'Result: {y}')")

        # Then execute all cells at once
        result = execute_session_all_cells("session_1")
        print(result)  # Shows results from all three cells
    """
    try:
        response = make_request("POST", f"/sessions/{session_id}/execute-all")

        if response["success"]:
            return f"✅ All cells executed successfully:\n{response['result']}"
        else:
            return f"❌ Some cells failed during execution:\n{response['result']}"

    except Exception as e:
        return f"Error executing all cells: {str(e)}"


@mcp.tool()
async def execute_session_cell(session_id: str, cell_id: int) -> str:
    """
    Execute a specific cell in a session.

    This tool executes only the specified cell while maintaining the session's variable state.
    The cell will have access to all variables defined from previous executions in the same session.
    This is useful for re-running a specific cell after modifying dependencies.

    Args:
        session_id: The ID of the session containing the cell
        cell_id: The ID of the specific cell to execute

    Returns:
        Execution result for the specified cell

    Example:
        # After setting up a session with cells
        result = execute_session_cell("session_1", 2)
        print(result)  # Shows execution result for cell 2 only

        # Can re-run the same cell multiple times
        result2 = execute_session_cell("session_1", 2)
        # Variables from previous runs are still available
    """
    try:
        response = make_request(
            "POST", f"/sessions/{session_id}/execute-cell/{cell_id}"
        )

        if response["success"]:
            return f"✅ Cell {cell_id} executed successfully:\n{response['result']}"
        else:
            return f"❌ Cell {cell_id} execution failed:\n{response['result']}"

    except Exception as e:
        return f"Error executing cell {cell_id}: {str(e)}"


@mcp.tool()
async def get_session_execution_status(session_id: str) -> str:
    """
    Get detailed execution status for all cells in a session.

    This tool provides comprehensive information about the execution state of all cells,
    including which cells have been executed, their results, and the current variables
    available in the session.

    Args:
        session_id: The ID of the session to get status for

    Returns:
        Detailed execution status including cell states and available variables

    Example:
        status = get_session_execution_status("session_1")
        print(status)
        # Shows:
        # - Total number of cells
        # - How many cells have been executed
        # - Execution status of each cell
        # - List of available variables
    """
    try:
        response = make_request("GET", f"/sessions/{session_id}/execution-status")

        result = f"Session {response['session_id']} Execution Status:\n"
        result += f"  Total cells: {response['total_cells']}\n"
        result += f"  Executed cells: {response['executed_cells']}\n"
        result += f"  Available variables: {', '.join(response['variables']) if response['variables'] else 'None'}\n\n"

        result += "Cell Details:\n"
        for cell in response["cells"]:
            status_icon = "✅" if cell["executed"] else "⏸️"
            result += f"  {status_icon} Cell {cell['cell_id']}: {'Executed' if cell['executed'] else 'Not executed'}\n"
            if cell["execution_result"]:
                result += f"    Result preview: {cell['execution_result']}\n"

        return result.strip()

    except Exception as e:
        return f"Error getting execution status: {str(e)}"


@mcp.tool()
async def smart_session_workflow(
    session_id: str, workflow_type: str = "sequential"
) -> str:
    """
    Execute a smart workflow on the session cells.

    This tool provides intelligent execution strategies for session cells based on the
    workflow type. It automatically determines the best execution order and handles
    dependencies between cells.

    Args:
        session_id: The ID of the session to execute workflow on
        workflow_type: Type of workflow to execute. Options:
            - "sequential": Execute all cells in order (default)
            - "unexecuted": Execute only cells that haven't been executed yet
            - "failed": Re-execute cells that previously failed
            - "all": Re-execute all cells (resetting execution state)

    Returns:
        Workflow execution results and status

    Example:
        # Execute all cells sequentially
        result = smart_session_workflow("session_1", "sequential")

        # Execute only unexecuted cells
        result = smart_session_workflow("session_1", "unexecuted")

        # Re-execute all cells from scratch
        result = smart_session_workflow("session_1", "all")
    """
    try:
        if workflow_type == "sequential":
            response = make_request("POST", f"/sessions/{session_id}/execute-all")
        elif workflow_type == "all":
            # Re-execute all cells
            response = make_request("POST", f"/sessions/{session_id}/execute-all")
        else:
            return f"❌ Unknown workflow type: {workflow_type}. Supported types: sequential, unexecuted, failed, all"

        if response["success"]:
            return f"✅ Workflow '{workflow_type}' completed successfully:\n{response['result']}"
        else:
            return f"❌ Workflow '{workflow_type}' failed:\n{response['result']}"

    except Exception as e:
        return f"Error executing workflow '{workflow_type}': {str(e)}"


@mcp.tool()
async def run_quick_python_code(code: str) -> str:
    """
    Execute Python code in a temporary session for quick calculations.

    This tool creates a temporary session, executes the code, and returns the result.
    The session is automatically cleaned up after execution. Variables are not
    preserved between calls.

    Args:
        code: The Python code to execute

    Returns:
        Execution result

    Example:
        result = run_quick_python_code("print(2 + 2)")
        print(result)  # Shows: 4

        result = run_quick_python_code("import math\nprint(math.sqrt(16))")
        print(result)  # Shows: 4.0
    """
    try:
        # Create temporary session
        session_response = make_request("POST", "/sessions")
        session_id = session_response["session_id"]

        # Execute code
        execution_response = make_request(
            "POST", f"/sessions/{session_id}/execute", {"code": code}
        )

        # Clean up session
        make_request("DELETE", f"/sessions/{session_id}")

        if execution_response["success"]:
            return execution_response["result"]
        else:
            return f"❌ Execution failed:\n{execution_response['result']}"

    except Exception as e:
        return f"Error in quick execution: {str(e)}"
    

@mcp.tool()
async def run_python_code(code: str) -> str:
    """
    Execute Python code and return the output.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stderr:
            return f"❌ Error:\n{stderr.decode()}"
        return stdout.decode() or "(no output)"
    except Exception as e:
        return f"Exception: {e}"


if __name__ == "__main__":
    mcp.run()

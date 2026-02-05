from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import io
import contextlib
import traceback
import logging
from pathlib import Path


# Configure logging
def setup_logging():
    """Setup logging configuration with file output."""
    # Create log directory if it doesn't exist
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "ipython_backend.log"),
            logging.StreamHandler(),
        ],
    )

    # Set up logger for this module
    logger = logging.getLogger("ipython_backend")
    return logger


# Initialize logging
logger = setup_logging()

app = FastAPI(title="IPython Backend Server", version="1.0.0")


class Cell(BaseModel):
    id: int
    code: str
    created_at: datetime
    executed: bool = False
    execution_result: Optional[str] = None


class Session(BaseModel):
    id: str
    created_at: datetime
    cells: Dict[int, Cell] = {}
    next_cell_id: int = 1
    variables: Dict[str, Any] = {}


class SessionCreateResponse(BaseModel):
    session_id: str
    message: str


class CellCreateResponse(BaseModel):
    cell_id: int
    session_id: str
    message: str


class CodeExecutionRequest(BaseModel):
    code: str


class CodeExecutionResponse(BaseModel):
    result: str
    success: bool
    error: Optional[str] = None


class IPythonBackend:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.session_counter = 0

    def _generate_session_id(self) -> str:
        """Generate a unique session ID with incrementing counter."""
        self.session_counter += 1
        return f"session_{self.session_counter}"

    def create_session(self) -> str:
        """Create a new IPython session."""
        session_id = self._generate_session_id()
        session = Session(id=session_id, created_at=datetime.now())
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions."""
        return [
            {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "cell_count": len(session.cells),
                "next_cell_id": session.next_cell_id,
            }
            for session in self.sessions.values()
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            del self.sessions[session_id]
            logger.info(
                f"Deleted session: {session_id} with {len(session.cells)} cells"
            )
            return True
        logger.warning(f"Attempted to delete non-existent session: {session_id}")
        return False

    def add_cell(self, session_id: str, code: str) -> Optional[int]:
        """Add a new cell to a session."""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(
                f"Attempted to add cell to non-existent session: {session_id}"
            )
            return None

        cell_id = session.next_cell_id
        cell = Cell(id=cell_id, code=code, created_at=datetime.now())
        session.cells[cell_id] = cell
        session.next_cell_id += 1
        logger.info(f"Added cell {cell_id} to session {session_id}")
        return cell_id

    def get_cell(self, session_id: str, cell_id: int) -> Optional[Cell]:
        """Get a specific cell from a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        return session.cells.get(cell_id)

    def get_all_cells(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all cells in a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return [
            {
                "id": cell.id,
                "code": cell.code,
                "created_at": cell.created_at.isoformat(),
                "executed": cell.executed,
                "execution_result": cell.execution_result,
            }
            for cell in session.cells.values()
        ]

    def delete_cell(self, session_id: str, cell_id: int) -> bool:
        """Delete a cell from a session."""
        session = self.sessions.get(session_id)
        if not session or cell_id not in session.cells:
            logger.warning(
                f"Attempted to delete cell {cell_id} from session {session_id} - not found"
            )
            return False

        del session.cells[cell_id]
        logger.info(f"Deleted cell {cell_id} from session {session_id}")
        return True

    def _execute_code_internal(
        self, session: Session, code: str
    ) -> CodeExecutionResponse:
        """Internal method to execute Python code in a session."""
        # Prepare execution environment
        local_vars = session.variables

        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Execute code with captured output
            with (
                contextlib.redirect_stdout(stdout_capture),
                contextlib.redirect_stderr(stderr_capture),
            ):
                # Use session variables as both globals and locals for function definitions
                exec(code, local_vars, local_vars)

            # Update session variables
            session.variables = local_vars

            # Get captured output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()

            # Combine outputs
            if stdout_output and stderr_output:
                result = f"STDOUT:\n{stdout_output}\nSTDERR:\n{stderr_output}"
            elif stdout_output:
                result = stdout_output
            elif stderr_output:
                result = stderr_output
            else:
                result = "(Code executed successfully, no output)"

            return CodeExecutionResponse(result=result, success=True)

        except Exception as e:
            error_msg = f"Error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return CodeExecutionResponse(result=error_msg, success=False, error=str(e))

    def execute_code(self, session_id: str, code: str) -> CodeExecutionResponse:
        """Execute Python code in a session."""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(
                f"Code execution attempted on non-existent session: {session_id}"
            )
            raise HTTPException(status_code=404, detail="Session not found")

        result = self._execute_code_internal(session, code)

        if result.success:
            logger.info(f"Code executed successfully in session {session_id}")
        else:
            logger.error(
                f"Code execution failed in session {session_id}: {result.error}"
            )

        return result


# Global backend instance
backend = IPythonBackend()


@app.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    """Create a new IPython session."""
    logger.info("API request: Create new session")
    session_id = backend.create_session()
    logger.info(f"API response: Created session {session_id}")
    return SessionCreateResponse(
        session_id=session_id, message="Session created successfully"
    )


@app.get("/sessions")
async def get_all_sessions():
    """Get all sessions."""
    return {"sessions": backend.get_all_sessions()}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session."""
    session = backend.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "created_at": session.created_at.isoformat(),
        "cell_count": len(session.cells),
        "next_cell_id": session.next_cell_id,
        "variables": list(session.variables.keys()),
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    logger.info(f"API request: Delete session {session_id}")
    success = backend.delete_session(session_id)
    if not success:
        logger.warning(f"API response: Session {session_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"API response: Successfully deleted session {session_id}")
    return {"message": "Session deleted successfully"}


@app.post("/sessions/{session_id}/cells", response_model=CellCreateResponse)
async def add_cell(session_id: str, request: CodeExecutionRequest):
    """Add a new cell to a session."""
    cell_id = backend.add_cell(session_id, request.code)
    if cell_id is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return CellCreateResponse(
        cell_id=cell_id, session_id=session_id, message="Cell added successfully"
    )


@app.get("/sessions/{session_id}/cells")
async def get_all_cells(session_id: str):
    """Get all cells in a session."""
    cells = backend.get_all_cells(session_id)
    if cells is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"cells": cells}


@app.get("/sessions/{session_id}/cells/{cell_id}")
async def get_cell(session_id: str, cell_id: int):
    """Get a specific cell from a session."""
    cell = backend.get_cell(session_id, cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")

    return {
        "id": cell.id,
        "code": cell.code,
        "created_at": cell.created_at.isoformat(),
        "executed": cell.executed,
        "execution_result": cell.execution_result,
    }


@app.delete("/sessions/{session_id}/cells/{cell_id}")
async def delete_cell(session_id: str, cell_id: int):
    """Delete a cell from a session."""
    success = backend.delete_cell(session_id, cell_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cell or session not found")

    return {"message": "Cell deleted successfully"}


@app.post("/sessions/{session_id}/execute", response_model=CodeExecutionResponse)
async def execute_code(session_id: str, request: CodeExecutionRequest):
    """Execute Python code in a session."""
    code_preview = request.code[:50] + "..." if len(request.code) > 50 else request.code
    logger.info(
        f"API request: Execute code in session {session_id} - Code: {code_preview}"
    )
    result = backend.execute_code(session_id, request.code)
    if result.success:
        logger.info(f"API response: Code executed successfully in session {session_id}")
    else:
        logger.error(f"API response: Code execution failed in session {session_id}")
    return result


@app.post("/sessions/{session_id}/execute-all", response_model=CodeExecutionResponse)
async def execute_all_cells(session_id: str):
    """Execute all cells in a session in order."""
    logger.info(f"API request: Execute all cells in session {session_id}")

    session = backend.get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found for execute-all operation")
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.cells:
        return CodeExecutionResponse(
            result="No cells found in session to execute", success=True
        )

    # Sort cells by ID to ensure execution order
    sorted_cells = sorted(session.cells.items(), key=lambda x: x[0])

    all_results = []
    execution_success = True

    for cell_id, cell in sorted_cells:
        logger.info(f"Executing cell {cell_id} in session {session_id}")

        # Execute the cell using the same logic as execute_code
        result = backend._execute_code_internal(session, cell.code)

        # Update cell execution status
        cell.executed = True
        cell.execution_result = result.result

        all_results.append(f"--- Cell {cell_id} ---\n{result.result}")

        if not result.success:
            execution_success = False
            logger.error(f"Cell {cell_id} execution failed in session {session_id}")
            break

    combined_result = "\n\n".join(all_results)

    if execution_success:
        logger.info(f"All cells executed successfully in session {session_id}")
    else:
        logger.error(f"Some cells failed to execute in session {session_id}")

    return CodeExecutionResponse(result=combined_result, success=execution_success)


@app.post(
    "/sessions/{session_id}/execute-cell/{cell_id}",
    response_model=CodeExecutionResponse,
)
async def execute_specific_cell(session_id: str, cell_id: int):
    """Execute a specific cell in a session."""
    logger.info(f"API request: Execute specific cell {cell_id} in session {session_id}")

    session = backend.get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found for execute-cell operation")
        raise HTTPException(status_code=404, detail="Session not found")

    cell = session.cells.get(cell_id)
    if not cell:
        logger.error(f"Cell {cell_id} not found in session {session_id}")
        raise HTTPException(status_code=404, detail="Cell not found")

    # Execute the cell using the same logic as execute_code
    result = backend._execute_code_internal(session, cell.code)

    # Update cell execution status and result
    cell.executed = True
    cell.execution_result = result.result

    if result.success:
        logger.info(f"Cell {cell_id} executed successfully in session {session_id}")
    else:
        logger.error(
            f"Cell {cell_id} execution failed in session {session_id}: {result.error}"
        )

    return CodeExecutionResponse(
        result=result.result, success=result.success, error=result.error
    )


@app.get("/sessions/{session_id}/execution-status")
async def get_execution_status(session_id: str):
    """Get the execution status of all cells in a session."""
    logger.info(f"API request: Get execution status for session {session_id}")

    session = backend.get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found for execution-status")
        raise HTTPException(status_code=404, detail="Session not found")

    cells_status = []
    for cell_id, cell in session.cells.items():
        cells_status.append(
            {
                "cell_id": cell_id,
                "executed": cell.executed,
                "execution_result": (
                    cell.execution_result[:100] + "..."
                    if cell.execution_result and len(cell.execution_result) > 100
                    else cell.execution_result
                ),
            }
        )

    return {
        "session_id": session_id,
        "total_cells": len(session.cells),
        "executed_cells": sum(1 for cell in session.cells.values() if cell.executed),
        "variables": list(session.variables.keys()),
        "cells": cells_status,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_sessions": len(backend.sessions)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=39256)

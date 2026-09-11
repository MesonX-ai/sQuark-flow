"""Execution API endpoints."""
from fastapi import APIRouter, Query, StreamingResponse
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid
import json
from ..models.workflow import ExecutionRequest, ExecutionResult
from ..services.executor import WorkflowExecutor, ExecutionCache

router = APIRouter(prefix="/api/v1", tags=["executions"])

# Initialize executor and cache
cache = ExecutionCache()
executor = WorkflowExecutor(cache=cache)

# In-memory store
executions_db: dict = {}


@router.post("/executions")
async def execute_workflow(request: ExecutionRequest):
    """Execute workflow synchronously."""
    result = await executor.execute(request)
    executions_db[result.execution_id] = result
    return result


@router.post("/executions/stream")
async def execute_workflow_streaming(request: ExecutionRequest):
    """Execute workflow with streaming output."""
    
    async def event_generator():
        async for event in executor.execute_streaming(request):
            yield json.dumps(event.model_dump(mode="json"), default=str) + "\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/executions")
async def list_executions(
    workspace_id: str = Query(...),
    workflow_id: str = Query(None),
    status: str = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List executions with optional filters."""
    items = list(executions_db.values())
    
    if workspace_id:
        items = [e for e in items if e.workspace_id == workspace_id]
    if workflow_id:
        items = [e for e in items if e.workflow_id == workflow_id]
    if status:
        items = [e for e in items if e.status == status]
    
    total = len(items)
    items = items[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, workspace_id: str = Query(...)):
    """Get execution result by ID."""
    if execution_id not in executions_db:
        return {"error": "Execution not found"}, 404
    
    execution = executions_db[execution_id]
    if execution.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    return execution


@router.get("/executions/{execution_id}/cost")
async def get_execution_cost(execution_id: str, workspace_id: str = Query(...)):
    """Get cost breakdown for execution."""
    if execution_id not in executions_db:
        return {"error": "Execution not found"}, 404
    
    execution = executions_db[execution_id]
    if execution.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    return {
        "execution_id": execution_id,
        "token_usage": execution.token_usage.model_dump(),
        "total_cost_usd": execution.total_cost_usd,
        "breakdown": {
            "input_tokens": execution.token_usage.input_tokens,
            "output_tokens": execution.token_usage.output_tokens,
            "cost_per_input": execution.token_usage.input_tokens * 15e-6,
            "cost_per_output": execution.token_usage.output_tokens * 75e-6,
        }
    }


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str, workspace_id: str = Query(...)):
    """Cancel a running execution."""
    if execution_id not in executions_db:
        return {"error": "Execution not found"}, 404
    
    execution = executions_db[execution_id]
    if execution.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    execution.status = "cancelled"
    return {"status": "cancelled", "id": execution_id}


@router.post("/executions/{execution_id}/retry")
async def retry_execution(execution_id: str, workspace_id: str = Query(...)):
    """Retry a failed execution."""
    if execution_id not in executions_db:
        return {"error": "Execution not found"}, 404
    
    original = executions_db[execution_id]
    if original.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    request = ExecutionRequest(
        workflow_id=original.workflow_id,
        workspace_id=workspace_id,
    )
    result = await executor.execute(request)
    executions_db[result.execution_id] = result
    
    return {
        "original_id": execution_id,
        "new_id": result.execution_id,
        "status": "retried"
    }

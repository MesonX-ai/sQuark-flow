"""Workflow API endpoints."""
from fastapi import APIRouter, Query
from datetime import datetime
import uuid
from ..models.workflow import WorkflowDefinition, ExecutionRequest

router = APIRouter(prefix="/api/v1", tags=["workflows"])

# In-memory store (replace with DynamoDB in production)
workflows_db: dict = {}


@router.post("/workflows")
async def create_or_update_workflow(workflow: WorkflowDefinition):
    """Create or update a workflow."""
    if not workflow.id:
        workflow.id = str(uuid.uuid4())
    
    workflow.updated_at = datetime.utcnow()
    workflows_db[workflow.id] = workflow
    
    return {"id": workflow.id, "status": "created", "workflow": workflow}


@router.get("/workflows")
async def list_workflows(
    workspace_id: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List workflows for a workspace."""
    ws_workflows = [w for w in workflows_db.values() if w.workspace_id == workspace_id]
    total = len(ws_workflows)
    items = ws_workflows[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, workspace_id: str = Query(...)):
    """Get workflow by ID."""
    if workflow_id not in workflows_db:
        return {"error": "Workflow not found"}, 404
    
    workflow = workflows_db[workflow_id]
    if workflow.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    return workflow


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, workspace_id: str = Query(...)):
    """Delete a workflow."""
    if workflow_id not in workflows_db:
        return {"error": "Workflow not found"}, 404
    
    workflow = workflows_db[workflow_id]
    if workflow.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    del workflows_db[workflow_id]
    return {"status": "deleted", "id": workflow_id}


@router.post("/workflows/{workflow_id}/versions")
async def save_version(workflow_id: str, workflow: WorkflowDefinition):
    """Save new workflow version."""
    if workflow_id not in workflows_db:
        return {"error": "Workflow not found"}, 404
    
    workflow.version = workflows_db[workflow_id].version + 1
    workflow.updated_at = datetime.utcnow()
    workflows_db[workflow_id] = workflow
    
    return {"version": workflow.version, "status": "saved"}


@router.post("/workflows/{workflow_id}/duplicate")
async def duplicate_workflow(workflow_id: str, workspace_id: str = Query(...)):
    """Duplicate a workflow."""
    if workflow_id not in workflows_db:
        return {"error": "Workflow not found"}, 404
    
    original = workflows_db[workflow_id]
    if original.workspace_id != workspace_id:
        return {"error": "Unauthorized"}, 403
    
    new_workflow = WorkflowDefinition(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        name=f"{original.name} (copy)",
        description=original.description,
        nodes=original.nodes,
        edges=original.edges,
        version=1,
    )
    
    workflows_db[new_workflow.id] = new_workflow
    return {"id": new_workflow.id, "status": "duplicated"}

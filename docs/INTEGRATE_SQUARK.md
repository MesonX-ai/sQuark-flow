# 🌐 Integrate Unified Backend with sQuark Web

**Project**: sQuark Web (FastAPI proxy + React)  
**Frontend Type**: Web application with server component  
**Integration Pattern**: FastAPI proxy to unified backend  
**Estimated Time**: 15-20 minutes

---

## Prerequisites

- ✅ Unified backend deployed
- ✅ API endpoint saved
- ✅ sQuark Web cloned locally
- ✅ Python 3.11+ and Node.js 18+ installed

---

## Step 1: Configure Environment

**File**: `.env`

```env
# Backend Configuration
UNIFIED_BACKEND_URL=https://abc123.execute-api.us-east-2.amazonaws.com/production
UNIFIED_WORKSPACE_ID=squark-web-workspace
UNIFIED_CACHE_TTL=3600

# Frontend
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WORKSPACE_ID=squark-web-workspace
```

---

## Step 2: Create FastAPI Proxy Service

**File**: `backend/routes/workflows.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import httpx
import os
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["workflows"])

BACKEND_URL = os.getenv("UNIFIED_BACKEND_URL")
WORKSPACE_ID = os.getenv("UNIFIED_WORKSPACE_ID")

async def get_backend_client():
    """Get HTTP client for backend communication."""
    async with httpx.AsyncClient(
        base_url=BACKEND_URL,
        timeout=30.0,
    ) as client:
        yield client


@router.post("/workflows")
async def create_workflow(
    workflow: dict,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Create workflow - proxy to unified backend."""
    try:
        workflow["workspace_id"] = WORKSPACE_ID
        response = await client.post("/api/v1/workflows", json=workflow)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.get("/workflows")
async def list_workflows(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """List workflows - proxy to unified backend."""
    try:
        response = await client.get(
            "/api/v1/workflows",
            params={
                "workspace_id": WORKSPACE_ID,
                "limit": limit,
                "offset": offset,
            },
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Get workflow - proxy to unified backend."""
    try:
        response = await client.get(
            f"/api/v1/workflows/{workflow_id}",
            params={"workspace_id": WORKSPACE_ID},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Delete workflow - proxy to unified backend."""
    try:
        response = await client.delete(
            f"/api/v1/workflows/{workflow_id}",
            params={"workspace_id": WORKSPACE_ID},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")
```

---

## Step 3: Create Execution Proxy

**File**: `backend/routes/executions.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx
import os
import json

router = APIRouter(prefix="/api/v1", tags=["executions"])

BACKEND_URL = os.getenv("UNIFIED_BACKEND_URL")
WORKSPACE_ID = os.getenv("UNIFIED_WORKSPACE_ID")

async def get_backend_client():
    async with httpx.AsyncClient(
        base_url=BACKEND_URL,
        timeout=30.0,
    ) as client:
        yield client


@router.post("/executions")
async def execute_workflow(
    payload: dict,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Execute workflow synchronously."""
    try:
        payload["workspace_id"] = WORKSPACE_ID
        response = await client.post("/api/v1/executions", json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.post("/executions/stream")
async def execute_workflow_streaming(
    payload: dict,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Execute workflow with streaming."""
    try:
        payload["workspace_id"] = WORKSPACE_ID
        
        async def stream_response():
            async with client.stream(
                "POST",
                "/api/v1/executions/stream",
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield line + "\n"
        
        return StreamingResponse(
            stream_response(),
            media_type="application/x-ndjson",
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Get execution result."""
    try:
        response = await client.get(
            f"/api/v1/executions/{execution_id}",
            params={"workspace_id": WORKSPACE_ID},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.get("/executions/{execution_id}/cost")
async def get_execution_cost(
    execution_id: str,
    client: httpx.AsyncClient = Depends(get_backend_client),
):
    """Get execution cost."""
    try:
        response = await client.get(
            f"/api/v1/executions/{execution_id}/cost",
            params={"workspace_id": WORKSPACE_ID},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")
```

---

## Step 4: Create Agent Proxy

**File**: `backend/routes/agents.py`

```python
from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter(prefix="/api/v1", tags=["agents"])

BACKEND_URL = os.getenv("UNIFIED_BACKEND_URL")

async def get_backend_client():
    async with httpx.AsyncClient(
        base_url=BACKEND_URL,
        timeout=10.0,
    ) as client:
        yield client


@router.get("/agents")
async def list_agents(category: str = None):
    """List available agents."""
    try:
        async with httpx.AsyncClient() as client:
            params = {}
            if category:
                params["category"] = category
            
            response = await client.get(
                f"{BACKEND_URL}/api/v1/agents",
                params=params,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/agents/{agent_id}",
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")


@router.get("/agents/models/list")
async def list_models():
    """List LLM models."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/agents/models/list",
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")
```

---

## Step 5: Create React Hook

**File**: `frontend/src/hooks/useUnifiedBackend.ts`

```typescript
import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';

interface ExecutionResult {
  execution_id: string;
  workflow_id: string;
  status: string;
  result: any;
  token_usage: any;
  total_cost_usd: number;
  duration_ms: number;
}

export function useUnifiedBackend() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    // Test health
    axios
      .get(`${baseURL}/health`)
      .then(() => setIsHealthy(true))
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [baseURL]);

  // Workflows
  const createWorkflow = useCallback(
    async (workflow: any) => {
      const response = await axios.post(`${baseURL}/api/v1/workflows`, workflow);
      return response.data;
    },
    [baseURL]
  );

  const getWorkflow = useCallback(
    async (workflowId: string) => {
      const response = await axios.get(
        `${baseURL}/api/v1/workflows/${workflowId}`
      );
      return response.data;
    },
    [baseURL]
  );

  const listWorkflows = useCallback(
    async (limit = 10, offset = 0) => {
      const response = await axios.get(`${baseURL}/api/v1/workflows`, {
        params: { limit, offset },
      });
      return response.data;
    },
    [baseURL]
  );

  // Executions
  const executeWorkflow = useCallback(
    async (workflowId: string, input?: any): Promise<ExecutionResult> => {
      const response = await axios.post(`${baseURL}/api/v1/executions`, {
        workflow_id: workflowId,
        initial_input: input || {},
      });
      return response.data;
    },
    [baseURL]
  );

  const streamWorkflow = useCallback(
    async (
      workflowId: string,
      onEvent: (event: any) => void,
      input?: any
    ) => {
      const response = await axios.post(
        `${baseURL}/api/v1/executions/stream`,
        {
          workflow_id: workflowId,
          initial_input: input || {},
        },
        { responseType: 'stream' }
      );

      let buffer = '';
      return new Promise((resolve, reject) => {
        response.data.on('data', (chunk: Buffer) => {
          buffer += chunk.toString();
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          lines.forEach((line) => {
            if (line) {
              try {
                onEvent(JSON.parse(line));
              } catch (e) {
                console.error('Failed to parse event:', e);
              }
            }
          });
        });

        response.data.on('end', resolve);
        response.data.on('error', reject);
      });
    },
    [baseURL]
  );

  const getExecution = useCallback(
    async (executionId: string) => {
      const response = await axios.get(
        `${baseURL}/api/v1/executions/${executionId}`
      );
      return response.data;
    },
    [baseURL]
  );

  // Agents
  const listAgents = useCallback(async () => {
    const response = await axios.get(`${baseURL}/api/v1/agents`);
    return response.data;
  }, [baseURL]);

  const listModels = useCallback(async () => {
    const response = await axios.get(`${baseURL}/api/v1/agents/models/list`);
    return response.data;
  }, [baseURL]);

  return {
    isHealthy,
    isLoading,
    error,
    workflows: {
      create: createWorkflow,
      get: getWorkflow,
      list: listWorkflows,
    },
    executions: {
      execute: executeWorkflow,
      stream: streamWorkflow,
      get: getExecution,
    },
    agents: {
      list: listAgents,
      models: listModels,
    },
  };
}
```

---

## Step 6: Create React Component

**File**: `frontend/src/components/WorkflowBuilder.tsx`

```typescript
import React, { useState } from 'react';
import { useUnifiedBackend } from '../hooks/useUnifiedBackend';

export function WorkflowBuilder() {
  const backend = useUnifiedBackend();
  const [workflowName, setWorkflowName] = useState('');
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [executionStatus, setExecutionStatus] = useState('');
  const [totalCost, setTotalCost] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const loadWorkflows = async () => {
    setIsLoading(true);
    try {
      const data = await backend.workflows.list(10, 0);
      setWorkflows(data.items || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecute = async (workflowId: string) => {
    setExecutionStatus('');
    setTotalCost(0);

    try {
      await backend.executions.stream(workflowId, (event) => {
        switch (event.event_type) {
          case 'step_started':
            setExecutionStatus(
              (prev) => prev + `\n▶️ ${event.node_id} started`
            );
            break;
          case 'token_streamed':
            setExecutionStatus((prev) => prev + event.data.token);
            break;
          case 'step_completed':
            setTotalCost((prev) => prev + (event.data.cost_usd || 0));
            break;
          case 'execution_completed':
            setExecutionStatus((prev) => prev + '\n✅ Complete!');
            break;
        }
      });
    } catch (error) {
      setExecutionStatus(`Error: ${error}`);
    }
  };

  if (backend.isLoading) return <div>Loading...</div>;
  if (!backend.isHealthy) return <div>Backend not available</div>;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Workflow Builder</h1>

      <button
        onClick={loadWorkflows}
        disabled={isLoading}
        className="px-4 py-2 bg-blue-600 text-white rounded mb-4"
      >
        {isLoading ? 'Loading...' : 'Load Workflows'}
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Workflows List */}
        <div>
          <h2 className="text-xl font-semibold mb-2">Workflows</h2>
          <div className="space-y-2">
            {workflows.map((wf) => (
              <div key={wf.id} className="p-2 border rounded">
                <div className="font-semibold">{wf.name}</div>
                <button
                  onClick={() => handleExecute(wf.id)}
                  className="mt-1 px-3 py-1 text-sm bg-green-600 text-white rounded"
                >
                  Execute
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Execution Output */}
        <div>
          <h2 className="text-xl font-semibold mb-2">Execution</h2>
          {totalCost > 0 && (
            <div className="mb-2 p-2 bg-blue-50 rounded">
              Cost: ${totalCost.toFixed(4)}
            </div>
          )}
          <pre className="p-2 bg-gray-900 text-green-400 rounded overflow-auto h-64 text-xs">
            {executionStatus || '(No output)'}
          </pre>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 7: Install Dependencies

```bash
cd /Users/mesonx/MY\ LAB/sQuark/

# Backend
cd backend
pip install -r requirements.txt
# Add to requirements.txt: httpx>=0.25.0

# Frontend
cd ../frontend
npm install
```

---

## Step 8: Start Application

```bash
# Backend (one terminal)
cd /Users/mesonx/MY\ LAB/sQuark/backend
uvicorn main:app --reload --port 8000

# Frontend (another terminal)
cd /Users/mesonx/MY\ LAB/sQuark/frontend
npm start
# Open http://localhost:3000
```

---

## ✅ Verification

- [ ] Backend proxy responds on http://localhost:8000/api/v1/agents
- [ ] Frontend connects to proxy
- [ ] Can load workflows
- [ ] Workflow execution displays results
- [ ] Cost tracking works
- [ ] Streaming output displays real-time

---

## 🚀 Production Deployment

```bash
# Backend
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Frontend
npm run build
npm run serve
```

---

**sQuark Web is now integrated! 🌐**

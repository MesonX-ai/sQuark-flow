# 🏠 Integrate Unified Backend with myfamilyassistant

**Project**: myfamilyassistant (Next.js 14 + React Flow)  
**Frontend Type**: Web application  
**Integration Pattern**: Direct API calls  
**Estimated Time**: 15-20 minutes

---

## Prerequisites

- ✅ Unified backend deployed (see [DEPLOY.md](../DEPLOY.md))
- ✅ API endpoint URL saved
- ✅ myfamilyassistant cloned locally
- ✅ Node.js 18+ and npm installed

---

## Step 1: Get Your API Endpoint

```bash
cd /Users/mesonx/MY\ LAB/unified-backend-complete/terraform

# Save this output - you'll need it
terraform output -raw api_endpoint
# Example: https://abc123.execute-api.us-east-2.amazonaws.com/production
```

---

## Step 2: Create Environment Variables

In your myfamilyassistant project:

```bash
# .env.local
NEXT_PUBLIC_UNIFIED_BACKEND_URL=https://abc123.execute-api.us-east-2.amazonaws.com/production
NEXT_PUBLIC_WORKSPACE_ID=myfamilyassistant-workspace
NEXT_PUBLIC_LOG_LEVEL=info

# Optional: Adjust if needed
NEXT_PUBLIC_EXECUTION_TIMEOUT_MS=30000
NEXT_PUBLIC_ENABLE_STREAMING=true
NEXT_PUBLIC_CACHE_RESULTS=true
```

---

## Step 3: Install Dependencies

```bash
cd /Users/mesonx/MY\ LAB/myfamilyassistant

npm install --save @unified-agentic/backend-sdk
# or use the local SDK:
npm install --save ../unified-backend-complete/sdk/typescript
```

---

## Step 4: Create Backend Service

**File**: `src/services/unifiedBackend.ts`

```typescript
// Unified Backend Service
import axios, { AxiosInstance } from 'axios';

interface ExecutionResult {
  execution_id: string;
  workflow_id: string;
  status: 'success' | 'error' | 'cancelled';
  result: any;
  token_usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    cost_usd: number;
  };
  total_cost_usd: number;
  duration_ms: number;
}

interface WorkflowDefinition {
  id: string;
  workspace_id: string;
  name: string;
  nodes: any[];
  edges: any[];
}

class UnifiedBackendService {
  private client: AxiosInstance;
  private workspaceId: string;

  constructor(baseUrl: string, workspaceId: string) {
    this.workspaceId = workspaceId;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Workflows
  async createWorkflow(workflow: Partial<WorkflowDefinition>) {
    return this.client.post('/api/v1/workflows', {
      ...workflow,
      workspace_id: this.workspaceId,
    });
  }

  async getWorkflow(workflowId: string) {
    return this.client.get(`/api/v1/workflows/${workflowId}`, {
      params: { workspace_id: this.workspaceId },
    });
  }

  async listWorkflows(limit = 10, offset = 0) {
    return this.client.get('/api/v1/workflows', {
      params: {
        workspace_id: this.workspaceId,
        limit,
        offset,
      },
    });
  }

  async deleteWorkflow(workflowId: string) {
    return this.client.delete(`/api/v1/workflows/${workflowId}`, {
      params: { workspace_id: this.workspaceId },
    });
  }

  // Executions
  async executeWorkflow(
    workflowId: string,
    initialInput: any = {}
  ): Promise<ExecutionResult> {
    const response = await this.client.post('/api/v1/executions', {
      workflow_id: workflowId,
      workspace_id: this.workspaceId,
      initial_input: initialInput,
      streaming: false,
    });
    return response.data;
  }

  async executeWorkflowStreaming(
    workflowId: string,
    initialInput: any = {},
    onEvent: (event: any) => void
  ) {
    const response = await this.client.post(
      '/api/v1/executions/stream',
      {
        workflow_id: workflowId,
        workspace_id: this.workspaceId,
        initial_input: initialInput,
        streaming: true,
      },
      { responseType: 'stream' }
    );

    return new Promise((resolve, reject) => {
      let executionId = '';
      let buffer = '';

      response.data.on('data', (chunk: Buffer) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        lines.forEach((line) => {
          if (line) {
            try {
              const event = JSON.parse(line);
              if (event.execution_id) executionId = event.execution_id;
              onEvent(event);
            } catch (e) {
              console.error('Failed to parse event:', e);
            }
          }
        });
      });

      response.data.on('end', () => {
        resolve({ execution_id: executionId });
      });

      response.data.on('error', reject);
    });
  }

  async getExecution(executionId: string) {
    return this.client.get(`/api/v1/executions/${executionId}`, {
      params: { workspace_id: this.workspaceId },
    });
  }

  async getExecutionCost(executionId: string) {
    return this.client.get(
      `/api/v1/executions/${executionId}/cost`,
      {
        params: { workspace_id: this.workspaceId },
      }
    );
  }

  async listExecutions(
    workflowId?: string,
    status?: string,
    limit = 10,
    offset = 0
  ) {
    return this.client.get('/api/v1/executions', {
      params: {
        workspace_id: this.workspaceId,
        workflow_id: workflowId,
        status,
        limit,
        offset,
      },
    });
  }

  // Agents
  async listAgents() {
    return this.client.get('/api/v1/agents');
  }

  async getAgent(agentId: string) {
    return this.client.get(`/api/v1/agents/${agentId}`);
  }

  async testAgent(agentId: string) {
    return this.client.post(`/api/v1/agents/${agentId}/test`);
  }

  // Health
  async healthCheck() {
    return this.client.get('/health');
  }
}

export default UnifiedBackendService;
```

---

## Step 5: Create React Hook

**File**: `src/hooks/useUnifiedBackend.ts`

```typescript
import { useEffect, useState, useCallback } from 'react';
import UnifiedBackendService from '@/services/unifiedBackend';

export function useUnifiedBackend() {
  const [service, setService] = useState<UnifiedBackendService | null>(null);
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initService = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_UNIFIED_BACKEND_URL;
        const workspaceId = process.env.NEXT_PUBLIC_WORKSPACE_ID;

        if (!baseUrl || !workspaceId) {
          throw new Error('Backend URL or workspace ID not configured');
        }

        const svc = new UnifiedBackendService(baseUrl, workspaceId);

        // Test health
        await svc.healthCheck();
        setIsHealthy(true);
        setService(svc);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize backend');
      } finally {
        setIsLoading(false);
      }
    };

    initService();
  }, []);

  const executeWorkflow = useCallback(
    async (workflowId: string, input?: any) => {
      if (!service) throw new Error('Backend not initialized');
      return service.executeWorkflow(workflowId, input);
    },
    [service]
  );

  const streamWorkflow = useCallback(
    async (
      workflowId: string,
      onEvent: (event: any) => void,
      input?: any
    ) => {
      if (!service) throw new Error('Backend not initialized');
      return service.executeWorkflowStreaming(workflowId, input, onEvent);
    },
    [service]
  );

  return {
    service,
    isHealthy,
    isLoading,
    error,
    executeWorkflow,
    streamWorkflow,
  };
}
```

---

## Step 6: Use in React Component

**File**: `src/components/WorkflowCanvas.tsx`

```typescript
import { useUnifiedBackend } from '@/hooks/useUnifiedBackend';
import { useState } from 'react';

export function WorkflowCanvas() {
  const { service, streamWorkflow } = useUnifiedBackend();
  const [isExecuting, setIsExecuting] = useState(false);
  const [output, setOutput] = useState<string>('');
  const [cost, setCost] = useState<number>(0);

  const handleExecute = async () => {
    if (!service) return;

    setIsExecuting(true);
    setOutput('');
    setCost(0);

    try {
      let totalCost = 0;

      await streamWorkflow('my-workflow', (event) => {
        switch (event.event_type) {
          case 'step_started':
            setOutput((prev) => prev + `\n▶️ ${event.node_id} started...`);
            break;

          case 'token_streamed':
            setOutput((prev) => prev + event.data.token);
            break;

          case 'step_completed':
            totalCost += event.data.cost_usd || 0;
            setCost(totalCost);
            setOutput((prev) => prev + `\n✅ Step completed (${event.data.cost_usd?.toFixed(4)})`);
            break;

          case 'execution_completed':
            setOutput((prev) => prev + `\n\n✨ Execution complete! Total cost: $${totalCost.toFixed(4)}`);
            break;

          case 'execution_error':
            setOutput((prev) => prev + `\n❌ Error: ${event.data.error}`);
            break;
        }
      });
    } catch (error) {
      setOutput(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Workflow Execution</h2>

      <button
        onClick={handleExecute}
        disabled={isExecuting}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isExecuting ? 'Executing...' : 'Execute Workflow'}
      </button>

      {cost > 0 && (
        <div className="mt-4 p-3 bg-gray-100 rounded">
          💰 Cost: ${cost.toFixed(4)}
        </div>
      )}

      {output && (
        <pre className="mt-4 p-4 bg-gray-900 text-green-400 rounded overflow-auto max-h-64 font-mono text-sm">
          {output}
        </pre>
      )}
    </div>
  );
}
```

---

## Step 7: Update Your App

**File**: `src/app/layout.tsx` or `src/app.tsx`

```typescript
import { WorkflowCanvas } from '@/components/WorkflowCanvas';

export default function Home() {
  return (
    <main className="container mx-auto">
      <WorkflowCanvas />
    </main>
  );
}
```

---

## Step 8: Test Integration

```bash
cd /Users/mesonx/MY\ LAB/myfamilyassistant

# Start development server
npm run dev

# Open browser
open http://localhost:3000

# Click "Execute Workflow" button
# You should see real-time streaming output!
```

---

## 🔄 Advanced: React Flow Canvas Integration

To connect your React Flow canvas to the backend:

```typescript
import { useCallback } from 'react';
import { useUnifiedBackend } from '@/hooks/useUnifiedBackend';
import ReactFlow, { Node, Edge } from 'reactflow';

export function CanvasWithBackend() {
  const { service } = useUnifiedBackend();

  const handleSave = useCallback(async (nodes: Node[], edges: Edge[]) => {
    if (!service) return;

    // Convert React Flow format to workflow format
    const workflow = {
      name: 'My Workflow',
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data,
      })),
      edges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
      })),
    };

    // Save to backend
    const result = await service.createWorkflow(workflow);
    console.log('Workflow saved:', result.data);
  }, [service]);

  const handleExecute = useCallback(async (workflowId: string) => {
    if (!service) return;

    const result = await service.executeWorkflow(workflowId);
    console.log('Execution result:', result.data);
    console.log('Cost: $' + result.data.total_cost_usd);
  }, [service]);

  return (
    <div>
      <ReactFlow nodes={nodes} edges={edges}>
        {/* Your canvas UI */}
      </ReactFlow>
      <button onClick={() => handleSave(nodes, edges)}>Save Workflow</button>
      <button onClick={() => handleExecute('workflow-id')}>Execute</button>
    </div>
  );
}
```

---

## ✅ Verification Checklist

- [ ] Environment variables set correctly
- [ ] Backend health endpoint accessible
- [ ] Can create workflows via API
- [ ] Can execute workflows
- [ ] Streaming output displays in real-time
- [ ] Cost tracking shows correct values
- [ ] No CORS errors in browser console
- [ ] Workflow canvas saves to backend

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| `CORS error` | Check `cors_origins` includes your frontend URL |
| `Backend not found` | Verify API endpoint URL is correct |
| `Streaming not working` | Ensure `ENABLE_STREAMING=true` in backend |
| `Execution timeout` | Increase `NEXT_PUBLIC_EXECUTION_TIMEOUT_MS` |
| `Cost not showing` | Check token usage in execution response |

---

## 📊 Example Workflow Structure

```json
{
  "id": "workflow-1",
  "workspace_id": "myfamilyassistant-workspace",
  "name": "Email Draft to Post",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger",
      "position": { "x": 0, "y": 0 },
      "data": { "label": "Start" }
    },
    {
      "id": "agent-1",
      "type": "llm_agent",
      "position": { "x": 200, "y": 0 },
      "data": { "label": "Summarize Email" }
    },
    {
      "id": "output-1",
      "type": "output",
      "position": { "x": 400, "y": 0 },
      "data": { "label": "Return Summary" }
    }
  ],
  "edges": [
    { "id": "edge-1", "source": "trigger-1", "target": "agent-1" },
    { "id": "edge-2", "source": "agent-1", "target": "output-1" }
  ]
}
```

---

## 📚 Additional Resources

- [Backend API Reference](../README.md)
- [Deployment Guide](../DEPLOY.md)
- [React Flow Docs](https://reactflow.dev)
- [FastAPI Docs](https://fastapi.tiangolo.com)

---

**Integration complete! Your myfamilyassistant is now connected to the unified backend! 🎉**

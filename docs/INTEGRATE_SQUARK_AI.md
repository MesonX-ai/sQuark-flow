# 🤖 Integrate Unified Backend with sQuark.ai

**Project**: sQuark.ai (Next.js 15 + React Flow)  
**Frontend Type**: AI orchestration platform  
**Integration Pattern**: React Flow canvas to backend  
**Estimated Time**: 15-20 minutes

---

## Prerequisites

- ✅ Unified backend deployed
- ✅ API endpoint saved
- ✅ sQuark.ai cloned locally
- ✅ Node.js 18+ and npm installed

---

## Step 1: Configure Environment

**File**: `packages/frontend/.env.local`

```env
NEXT_PUBLIC_UNIFIED_BACKEND_API=https://abc123.execute-api.us-east-2.amazonaws.com/production
NEXT_PUBLIC_WORKSPACE_ID=squark-ai-workspace
NEXT_PUBLIC_ENABLE_REAL_TIME_EXECUTION=true
NEXT_PUBLIC_ENABLE_COST_TRACKING=true
```

---

## Step 2: Create Backend Integration Layer

**File**: `packages/frontend/lib/workflows/backendClient.ts`

```typescript
import axios from 'axios';
import { Node, Edge } from 'reactflow';

export interface WorkflowPayload {
  name: string;
  description?: string;
  nodes: any[];
  edges: any[];
}

export interface ExecutionPayload {
  workflow_id: string;
  initial_input?: Record<string, any>;
}

class BackendClient {
  private baseURL: string;
  private workspaceId: string;

  constructor(baseURL: string, workspaceId: string) {
    this.baseURL = baseURL;
    this.workspaceId = workspaceId;
  }

  // ==================== Workflows ====================

  async createWorkflow(payload: WorkflowPayload) {
    const response = await axios.post(`${this.baseURL}/api/v1/workflows`, {
      ...payload,
      workspace_id: this.workspaceId,
    });
    return response.data;
  }

  async getWorkflow(workflowId: string) {
    const response = await axios.get(
      `${this.baseURL}/api/v1/workflows/${workflowId}`,
      {
        params: { workspace_id: this.workspaceId },
      }
    );
    return response.data;
  }

  async listWorkflows(limit = 20, offset = 0) {
    const response = await axios.get(`${this.baseURL}/api/v1/workflows`, {
      params: {
        workspace_id: this.workspaceId,
        limit,
        offset,
      },
    });
    return response.data;
  }

  async updateWorkflow(workflowId: string, payload: Partial<WorkflowPayload>) {
    const response = await axios.post(`${this.baseURL}/api/v1/workflows`, {
      id: workflowId,
      ...payload,
      workspace_id: this.workspaceId,
    });
    return response.data;
  }

  async deleteWorkflow(workflowId: string) {
    const response = await axios.delete(
      `${this.baseURL}/api/v1/workflows/${workflowId}`,
      {
        params: { workspace_id: this.workspaceId },
      }
    );
    return response.data;
  }

  async duplicateWorkflow(workflowId: string) {
    const response = await axios.post(
      `${this.baseURL}/api/v1/workflows/${workflowId}/duplicate`,
      {},
      { params: { workspace_id: this.workspaceId } }
    );
    return response.data;
  }

  // ==================== Executions ====================

  async executeWorkflow(
    workflowId: string,
    initialInput: Record<string, any> = {}
  ) {
    const response = await axios.post(`${this.baseURL}/api/v1/executions`, {
      workflow_id: workflowId,
      workspace_id: this.workspaceId,
      initial_input: initialInput,
      streaming: false,
    });
    return response.data;
  }

  async *executeWorkflowStreaming(
    workflowId: string,
    initialInput: Record<string, any> = {}
  ): AsyncGenerator<any> {
    const response = await axios.post(
      `${this.baseURL}/api/v1/executions/stream`,
      {
        workflow_id: workflowId,
        workspace_id: this.workspaceId,
        initial_input: initialInput,
        streaming: true,
      },
      { responseType: 'stream' }
    );

    let buffer = '';
    for await (const chunk of response.data) {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim()) {
          yield JSON.parse(line);
        }
      }
    }
  }

  async getExecution(executionId: string) {
    const response = await axios.get(
      `${this.baseURL}/api/v1/executions/${executionId}`,
      {
        params: { workspace_id: this.workspaceId },
      }
    );
    return response.data;
  }

  async getExecutionCost(executionId: string) {
    const response = await axios.get(
      `${this.baseURL}/api/v1/executions/${executionId}/cost`,
      {
        params: { workspace_id: this.workspaceId },
      }
    );
    return response.data;
  }

  async listExecutions(filters: any = {}) {
    const response = await axios.get(`${this.baseURL}/api/v1/executions`, {
      params: {
        workspace_id: this.workspaceId,
        ...filters,
      },
    });
    return response.data;
  }

  // ==================== Agents ====================

  async getAgents() {
    const response = await axios.get(`${this.baseURL}/api/v1/agents`);
    return response.data;
  }

  async getAgent(agentId: string) {
    const response = await axios.get(`${this.baseURL}/api/v1/agents/${agentId}`);
    return response.data;
  }

  async listModels() {
    const response = await axios.get(`${this.baseURL}/api/v1/agents/models/list`);
    return response.data;
  }

  async testAgent(agentId: string) {
    const response = await axios.post(
      `${this.baseURL}/api/v1/agents/${agentId}/test`
    );
    return response.data;
  }

  // ==================== Health ====================

  async healthCheck() {
    const response = await axios.get(`${this.baseURL}/health`);
    return response.data;
  }
}

export default BackendClient;
```

---

## Step 3: Create React Hook for Canvas

**File**: `packages/frontend/hooks/useWorkflowCanvas.ts`

```typescript
import { useCallback, useEffect, useState } from 'react';
import { Node, Edge } from 'reactflow';
import BackendClient from '@/lib/workflows/backendClient';

interface UseWorkflowCanvasProps {
  workflowId?: string;
  onExecutionStart?: () => void;
  onExecutionComplete?: (cost: number) => void;
}

export function useWorkflowCanvas({
  workflowId,
  onExecutionStart,
  onExecutionComplete,
}: UseWorkflowCanvasProps = {}) {
  const [client, setClient] = useState<BackendClient | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<string>('');
  const [totalCost, setTotalCost] = useState<number>(0);

  // Initialize client
  useEffect(() => {
    const baseURL = process.env.NEXT_PUBLIC_UNIFIED_BACKEND_API;
    const workspaceId = process.env.NEXT_PUBLIC_WORKSPACE_ID;

    if (baseURL && workspaceId) {
      const newClient = new BackendClient(baseURL, workspaceId);
      setClient(newClient);

      // Load workflow if ID provided
      if (workflowId) {
        loadWorkflow(newClient, workflowId);
      }
    }
  }, [workflowId]);

  const loadWorkflow = useCallback(
    async (client: BackendClient, id: string) => {
      try {
        const workflow = await client.getWorkflow(id);
        setNodes(workflow.nodes);
        setEdges(workflow.edges);
      } catch (error) {
        console.error('Failed to load workflow:', error);
      }
    },
    []
  );

  // Save workflow to backend
  const saveWorkflow = useCallback(
    async (name: string, description?: string) => {
      if (!client) return;

      try {
        const result = await client.createWorkflow({
          name,
          description,
          nodes,
          edges,
        });

        console.log('Workflow saved:', result.id);
        return result.id;
      } catch (error) {
        console.error('Failed to save workflow:', error);
        throw error;
      }
    },
    [client, nodes, edges]
  );

  // Execute workflow (streaming)
  const executeWorkflow = useCallback(
    async (workflowId: string, initialInput: any = {}) => {
      if (!client || isExecuting) return;

      setIsExecuting(true);
      setExecutionStatus('');
      setTotalCost(0);
      onExecutionStart?.();

      try {
        for await (const event of client.executeWorkflowStreaming(
          workflowId,
          initialInput
        )) {
          switch (event.event_type) {
            case 'step_started':
              setExecutionStatus(
                (prev) =>
                  prev + `\n▶️ Starting: ${event.node_id}`
              );
              break;

            case 'token_streamed':
              // Real-time token output
              setExecutionStatus((prev) => prev + event.data.token);
              break;

            case 'step_completed':
              const stepCost = event.data.cost_usd || 0;
              setTotalCost((prev) => prev + stepCost);
              setExecutionStatus(
                (prev) =>
                  prev +
                  `\n✅ Completed: ${event.node_id} ($${stepCost.toFixed(4)})`
              );
              break;

            case 'execution_completed':
              setExecutionStatus(
                (prev) =>
                  prev +
                  `\n\n✨ Workflow complete! Total cost: $${totalCost.toFixed(4)}`
              );
              onExecutionComplete?.(totalCost);
              break;

            case 'execution_error':
              setExecutionStatus(
                (prev) => prev + `\n❌ Error: ${event.data.error}`
              );
              break;
          }
        }
      } catch (error) {
        console.error('Execution failed:', error);
        setExecutionStatus(
          `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      } finally {
        setIsExecuting(false);
      }
    },
    [client, isExecuting, totalCost, onExecutionStart, onExecutionComplete]
  );

  return {
    client,
    nodes,
    setNodes,
    edges,
    setEdges,
    saveWorkflow,
    executeWorkflow,
    isExecuting,
    executionStatus,
    totalCost,
  };
}
```

---

## Step 4: Create Canvas Component

**File**: `packages/frontend/components/WorkflowCanvas.tsx`

```typescript
'use client';

import React, { useCallback, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useWorkflowCanvas } from '@/hooks/useWorkflowCanvas';
import ExecutionPanel from './ExecutionPanel';

export default function WorkflowCanvas() {
  const {
    nodes,
    setNodes,
    edges,
    setEdges,
    saveWorkflow,
    executeWorkflow,
    isExecuting,
    executionStatus,
    totalCost,
  } = useWorkflowCanvas();

  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [savedWorkflowId, setSavedWorkflowId] = useState<string | null>(null);

  const onNodesChange = useCallback(
    (changes: any) => {
      setNodes((nds) => {
        // Apply changes from React Flow
        return changes.reduce((acc, change) => {
          if (change.type === 'select') {
            return acc.map((n) =>
              n.id === change.id ? { ...n, selected: change.selected } : n
            );
          }
          if (change.type === 'position') {
            return acc.map((n) =>
              n.id === change.id
                ? { ...n, position: change.position }
                : n
            );
          }
          return acc;
        }, nds);
      });
    },
    [setNodes]
  );

  const onEdgesChange = useCallback(
    (changes: any) => {
      setEdges((eds) => {
        return changes.reduce((acc, change) => {
          if (change.type === 'select') {
            return acc.map((e) =>
              e.id === change.id ? { ...e, selected: change.selected } : e
            );
          }
          if (change.type === 'remove') {
            return acc.filter((e) => e.id !== change.id);
          }
          return acc;
        }, eds);
      });
    },
    [setEdges]
  );

  const onConnect = useCallback(
    (connection: any) => {
      setEdges((eds) => [
        ...eds,
        {
          id: `${connection.source}-${connection.target}`,
          source: connection.source,
          target: connection.target,
        },
      ]);
    },
    [setEdges]
  );

  const handleSave = async () => {
    try {
      const id = await saveWorkflow(workflowName);
      setSavedWorkflowId(id);
      alert(`Workflow saved: ${id}`);
    } catch (error) {
      alert('Failed to save workflow');
    }
  };

  const handleExecute = () => {
    if (!savedWorkflowId) {
      alert('Please save workflow first');
      return;
    }
    executeWorkflow(savedWorkflowId);
  };

  return (
    <div className="flex h-screen">
      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>

        {/* Toolbar */}
        <div className="absolute top-4 left-4 bg-white p-4 rounded shadow-lg">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="border px-2 py-1 mb-2 w-full"
            placeholder="Workflow name"
          />
          <button
            onClick={handleSave}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mb-2"
          >
            Save Workflow
          </button>
          <button
            onClick={handleExecute}
            disabled={isExecuting || !savedWorkflowId}
            className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
        </div>
      </div>

      {/* Execution Panel */}
      <ExecutionPanel
        isExecuting={isExecuting}
        status={executionStatus}
        totalCost={totalCost}
      />
    </div>
  );
}
```

---

## Step 5: Create Execution Panel Component

**File**: `packages/frontend/components/ExecutionPanel.tsx`

```typescript
import React from 'react';

interface ExecutionPanelProps {
  isExecuting: boolean;
  status: string;
  totalCost: number;
}

export default function ExecutionPanel({
  isExecuting,
  status,
  totalCost,
}: ExecutionPanelProps) {
  return (
    <div className="w-80 bg-gray-100 border-l p-4 flex flex-col">
      <h2 className="text-xl font-bold mb-4">Execution</h2>

      {/* Status Indicator */}
      <div className="mb-4">
        {isExecuting ? (
          <div className="flex items-center text-yellow-600">
            <div className="animate-spin mr-2">⏳</div>
            <span>Executing...</span>
          </div>
        ) : (
          <div className="text-gray-600">Ready</div>
        )}
      </div>

      {/* Cost Display */}
      {totalCost > 0 && (
        <div className="mb-4 p-3 bg-blue-50 rounded">
          <div className="text-sm text-gray-600">Total Cost</div>
          <div className="text-xl font-bold text-blue-600">
            ${totalCost.toFixed(4)}
          </div>
        </div>
      )}

      {/* Output */}
      <div className="flex-1 flex flex-col">
        <label className="text-sm font-semibold text-gray-700 mb-2">
          Output
        </label>
        <pre className="flex-1 p-3 bg-gray-900 text-green-400 rounded overflow-auto font-mono text-xs">
          {status || '(No output yet)'}
        </pre>
      </div>
    </div>
  );
}
```

---

## Step 6: Update Next.js Config

**File**: `next.config.js` or `next.config.mjs`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable streaming responses
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  // CORS headers
  headers: async () => [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Access-Control-Allow-Credentials', value: 'true' },
        { key: 'Access-Control-Allow-Origin', value: '*' },
        {
          key: 'Access-Control-Allow-Methods',
          value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT',
        },
        {
          key: 'Access-Control-Allow-Headers',
          value:
            'X-CSRF-Token, X-Forwarded-Host, X-URL-PATH-PREFIX, Content-Type, Accept',
        },
      ],
    },
  ],
};

module.exports = nextConfig;
```

---

## Step 7: Test Integration

```bash
cd /Users/mesonx/MY\ LAB/sQuark.ai

npm install
npm run dev

# Open http://localhost:3000
# Start creating workflows!
```

---

## ✅ Verification

- [ ] Backend API endpoint responds to health check
- [ ] Can create and save workflows
- [ ] Canvas displays correctly with React Flow
- [ ] Workflow executes with streaming output
- [ ] Cost tracking displays correctly
- [ ] Agents list loads successfully
- [ ] No CORS errors in browser console

---

## 🚀 Deployment to Production

```bash
# Build
npm run build

# Deploy to Vercel/AWS
npm run deploy
```

---

**sQuark.ai is now integrated with the unified backend! 🤖**

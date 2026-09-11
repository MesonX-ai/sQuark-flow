# 🖥️ Integrate Unified Backend with sQuark AI Browser (Desktop)

**Project**: sQuark AI Browser (PyQt Desktop Application)  
**Frontend Type**: Desktop application  
**Integration Pattern**: Direct Python HTTP to AWS backend  
**Estimated Time**: 15-20 minutes

---

## Prerequisites

- ✅ Unified backend deployed
- ✅ API endpoint saved
- ✅ sQuark (desktop app) cloned locally
- ✅ Python 3.11+ installed
- ✅ PyQt6 installed

---

## Step 1: Get Your API Endpoint

```bash
cd /Users/mesonx/MY\ LAB/sQuark-flow/terraform

# Save this output - you'll need it
terraform output -raw api_endpoint
# Example: https://abc123.execute-api.us-east-2.amazonaws.com/production
```

---

## Step 2: Create Environment Configuration

**File**: `config.py` (add to sQuark project)

```python
import os
from dataclasses import dataclass

@dataclass
class BackendConfig:
    """Configuration for unified agentic backend"""
    
    # API Configuration
    BACKEND_URL: str = os.getenv(
        "UNIFIED_BACKEND_URL",
        "https://abc123.execute-api.us-east-2.amazonaws.com/production"
    )
    
    # Workspace Configuration
    WORKSPACE_ID: str = os.getenv(
        "UNIFIED_WORKSPACE_ID",
        "squark-browser-workspace"
    )
    
    # Execution Configuration
    EXECUTION_TIMEOUT_SECONDS: int = int(os.getenv(
        "EXECUTION_TIMEOUT_SECONDS",
        "30"
    ))
    
    # Streaming Configuration
    ENABLE_STREAMING: bool = os.getenv(
        "ENABLE_STREAMING",
        "true"
    ).lower() == "true"
    
    # Cache Configuration
    ENABLE_CACHING: bool = os.getenv(
        "ENABLE_CACHING",
        "true"
    ).lower() == "true"
    
    CACHE_TTL_SECONDS: int = int(os.getenv(
        "CACHE_TTL_SECONDS",
        "3600"
    ))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Create default config
backend_config = BackendConfig()
```

---

## Step 3: Create Backend Client

**File**: `squark/backend_client.py`

```python
import httpx
import asyncio
import json
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from config import backend_config

@dataclass
class WorkflowDefinition:
    id: str
    name: str
    nodes: list
    edges: list
    workspace_id: str = None
    
    def __post_init__(self):
        if self.workspace_id is None:
            self.workspace_id = backend_config.WORKSPACE_ID

@dataclass
class ExecutionResult:
    execution_id: str
    workflow_id: str
    status: str  # success, error, cancelled
    result: Any
    token_usage: Dict[str, int]
    total_cost_usd: float
    duration_ms: float

class BackendClient:
    """Client for unified agentic backend"""
    
    def __init__(
        self,
        base_url: str = backend_config.BACKEND_URL,
        workspace_id: str = backend_config.WORKSPACE_ID,
        timeout: float = 30.0
    ):
        self.base_url = base_url
        self.workspace_id = workspace_id
        self.timeout = httpx.Timeout(timeout)
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    # ==================== Workflows ====================
    
    async def create_workflow(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """Create or update workflow"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        payload = {
            "id": workflow.id,
            "name": workflow.name,
            "nodes": workflow.nodes,
            "edges": workflow.edges,
            "workspace_id": workflow.workspace_id,
        }
        
        response = await self.client.post(
            "/api/v1/workflows",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.get(
            f"/api/v1/workflows/{workflow_id}",
            params={"workspace_id": self.workspace_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def list_workflows(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """List workflows"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.get(
            "/api/v1/workflows",
            params={
                "workspace_id": self.workspace_id,
                "limit": limit,
                "offset": offset
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete workflow"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.delete(
            f"/api/v1/workflows/{workflow_id}",
            params={"workspace_id": self.workspace_id}
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Executions ====================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        initial_input: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute workflow synchronously"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        payload = {
            "workflow_id": workflow_id,
            "workspace_id": self.workspace_id,
            "initial_input": initial_input or {}
        }
        
        response = await self.client.post(
            "/api/v1/executions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return ExecutionResult(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            status=data["status"],
            result=data.get("result"),
            token_usage=data.get("token_usage", {}),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            duration_ms=data.get("duration_ms", 0)
        )
    
    async def stream_workflow(
        self,
        workflow_id: str,
        initial_input: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream workflow execution with real-time output"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        payload = {
            "workflow_id": workflow_id,
            "workspace_id": self.workspace_id,
            "initial_input": initial_input or {}
        }
        
        async with self.client.stream(
            "POST",
            "/api/v1/executions/stream",
            json=payload
        ) as response:
            response.raise_for_status()
            buffer = ""
            
            async for chunk in response.aiter_text():
                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines[-1]
                
                for line in lines[:-1]:
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON: {line}")
    
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution result"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.get(
            f"/api/v1/executions/{execution_id}",
            params={"workspace_id": self.workspace_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_execution_cost(self, execution_id: str) -> Dict[str, Any]:
        """Get execution cost breakdown"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.get(
            f"/api/v1/executions/{execution_id}/cost",
            params={"workspace_id": self.workspace_id}
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Agents ====================
    
    async def list_agents(self) -> list:
        """List available agents"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.get("/api/v1/agents")
        response.raise_for_status()
        return response.json()
    
    async def list_models(self) -> list:
        """List LLM models"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        response = await self.client.get("/api/v1/agents/models/list")
        response.raise_for_status()
        return response.json()
```

---

## Step 4: Create PyQt Integration Widget

**File**: `squark/widgets/workflow_executor.py`

```python
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QComboBox, QSpinBox
)
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
from backend_client import BackendClient, WorkflowDefinition
from config import backend_config

class ExecutorWorker(QThread):
    """Worker thread for async backend operations"""
    
    # Signals
    execution_started = pyqtSignal()
    token_received = pyqtSignal(str)
    step_completed = pyqtSignal(dict)
    execution_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, workflow_id: str, initial_input: dict = None):
        super().__init__()
        self.workflow_id = workflow_id
        self.initial_input = initial_input or {}
        self.total_cost = 0.0
    
    def run(self):
        """Run async execution in thread"""
        try:
            asyncio.run(self._execute())
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    async def _execute(self):
        """Execute workflow with streaming"""
        self.execution_started.emit()
        
        async with BackendClient() as client:
            try:
                async for event in client.stream_workflow(
                    self.workflow_id,
                    self.initial_input
                ):
                    event_type = event.get("event_type")
                    
                    if event_type == "step_started":
                        self.step_completed.emit({
                            "status": "started",
                            "node_id": event.get("node_id")
                        })
                    
                    elif event_type == "token_streamed":
                        self.token_received.emit(
                            event.get("data", {}).get("token", "")
                        )
                    
                    elif event_type == "step_completed":
                        cost = event.get("data", {}).get("cost_usd", 0)
                        self.total_cost += cost
                        self.step_completed.emit({
                            "status": "completed",
                            "node_id": event.get("node_id"),
                            "cost": cost
                        })
                    
                    elif event_type == "execution_completed":
                        self.execution_completed.emit({
                            "execution_id": event.get("execution_id"),
                            "total_cost": self.total_cost,
                            "status": "success"
                        })
                    
                    elif event_type == "execution_error":
                        self.error_occurred.emit(
                            event.get("data", {}).get("error", "Unknown error")
                        )
            
            except Exception as e:
                self.error_occurred.emit(f"Execution failed: {str(e)}")

class WorkflowExecutorWidget(QWidget):
    """PyQt widget for workflow execution"""
    
    def __init__(self):
        super().__init__()
        self.workflows = []
        self.selected_workflow = None
        self.worker = None
        self.init_ui()
        self.load_workflows()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Workflow Executor")
        layout.addWidget(title)
        
        # Workflow selection
        workflow_layout = QHBoxLayout()
        workflow_layout.addWidget(QLabel("Workflow:"))
        self.workflow_combo = QComboBox()
        workflow_layout.addWidget(self.workflow_combo)
        layout.addLayout(workflow_layout)
        
        # Execute button
        self.execute_btn = QPushButton("Execute Workflow")
        self.execute_btn.clicked.connect(self.execute_workflow)
        layout.addWidget(self.execute_btn)
        
        # Output display
        layout.addWidget(QLabel("Output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        # Cost display
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel("Total Cost:"))
        self.cost_label = QLabel("$0.0000")
        cost_layout.addWidget(self.cost_label)
        cost_layout.addStretch()
        layout.addLayout(cost_layout)
        
        self.setLayout(layout)
    
    async def _load_workflows_async(self):
        """Load workflows from backend"""
        try:
            async with BackendClient() as client:
                is_healthy = await client.health_check()
                if not is_healthy:
                    self.output_text.setText("❌ Backend not available")
                    return
                
                workflows_data = await client.list_workflows()
                self.workflows = workflows_data.get("items", [])
                
                self.workflow_combo.clear()
                for wf in self.workflows:
                    self.workflow_combo.addItem(wf["name"], wf["id"])
                
                if self.workflows:
                    self.output_text.setText(
                        f"✅ Loaded {len(self.workflows)} workflows"
                    )
        except Exception as e:
            self.output_text.setText(f"❌ Error loading workflows: {e}")
    
    def load_workflows(self):
        """Load workflows in background"""
        try:
            asyncio.run(self._load_workflows_async())
        except Exception as e:
            self.output_text.setText(f"Error: {e}")
    
    def execute_workflow(self):
        """Execute selected workflow"""
        workflow_id = self.workflow_combo.currentData()
        if not workflow_id:
            self.output_text.setText("Please select a workflow")
            return
        
        self.output_text.clear()
        self.output_text.setText("Starting execution...\n")
        self.execute_btn.setEnabled(False)
        self.cost_label.setText("$0.0000")
        
        self.worker = ExecutorWorker(workflow_id)
        self.worker.token_received.connect(self.on_token)
        self.worker.step_completed.connect(self.on_step_completed)
        self.worker.execution_completed.connect(self.on_execution_completed)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_token(self, token: str):
        """Handle token output"""
        self.output_text.insertPlainText(token)
    
    def on_step_completed(self, data: dict):
        """Handle step completion"""
        status = data.get("status")
        node_id = data.get("node_id")
        cost = data.get("cost", 0)
        
        if status == "started":
            self.output_text.insertPlainText(f"\n▶️ {node_id} started\n")
        elif status == "completed":
            self.output_text.insertPlainText(
                f"\n✅ {node_id} completed (${cost:.4f})\n"
            )
    
    def on_execution_completed(self, data: dict):
        """Handle execution completion"""
        total_cost = data.get("total_cost", 0)
        self.output_text.insertPlainText(
            f"\n\n✨ Execution complete! Total cost: ${total_cost:.4f}"
        )
        self.cost_label.setText(f"${total_cost:.4f}")
        self.execute_btn.setEnabled(True)
    
    def on_error(self, error: str):
        """Handle error"""
        self.output_text.insertPlainText(f"\n❌ Error: {error}")
        self.execute_btn.setEnabled(True)
```

---

## Step 5: Add to Main Application

**File**: `main.py`

```python
import sys
import os
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from squark.widgets.workflow_executor import WorkflowExecutorWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("sQuark AI Browser")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Add executor widget
        executor = WorkflowExecutorWidget()
        layout.addWidget(executor)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

---

## Step 6: Set Environment Variables

**File**: `.env`

```env
# Unified Backend Configuration
UNIFIED_BACKEND_URL=https://abc123.execute-api.us-east-2.amazonaws.com/production
UNIFIED_WORKSPACE_ID=squark-browser-workspace

# Execution Configuration
EXECUTION_TIMEOUT_SECONDS=30
ENABLE_STREAMING=true
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600

# Logging
LOG_LEVEL=INFO
```

---

## Step 7: Install Dependencies

```bash
cd /Users/mesonx/MY\ LAB/sQuark

# Install backend client dependencies
pip install httpx PyQt6

# Or add to requirements.txt
echo "httpx>=0.25.0" >> requirements.txt
echo "PyQt6>=6.6.0" >> requirements.txt

pip install -r requirements.txt
```

---

## Step 8: Test Integration

```bash
cd /Users/mesonx/MY\ LAB/sQuark

# Set environment
export UNIFIED_BACKEND_URL=https://your-api-endpoint/production
export UNIFIED_WORKSPACE_ID=squark-browser-workspace

# Run application
python main.py
```

---

## ✅ Verification Checklist

- [ ] Backend health check passes
- [ ] Workflows load successfully
- [ ] Can select and execute workflow
- [ ] Real-time streaming output displays
- [ ] Cost tracking works
- [ ] Streaming events processed correctly
- [ ] Error handling works

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Check backend URL and ensure it's deployed |
| `Timeout errors` | Increase `EXECUTION_TIMEOUT_SECONDS` in .env |
| `Workflow list empty` | Verify workspace_id matches backend |
| `CORS errors` | Not applicable for desktop app (direct HTTP) |
| `UI freezes` | Worker thread handles async operations |

---

## 📊 Architecture Diagram

```
sQuark AI Browser (PyQt Desktop)
    ↓
BackendClient (Python httpx)
    ↓
AWS API Gateway v2
    ↓
Lambda Function (FastAPI)
    ↓
DynamoDB (Workflows, Executions, etc.)
```

---

**sQuark AI Browser is now integrated with the unified backend! 🖥️**

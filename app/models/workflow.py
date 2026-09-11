"""Data models for workflows, executions, and execution events."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class NodeType(str, Enum):
    """Supported node types in React Flow canvas."""
    TRIGGER = "trigger"
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    LLM_AGENT = "llm_agent"
    AGENT = "agent"
    CONTEXT = "context"
    MEMORY = "memory"
    TASK_DECOMPOSITION = "task_decomposition"
    MULTI_AGENT_ROUTER = "multi_agent_router"
    SEMANTIC_BRANCH = "semantic_branch"
    REFLECTION_LOOP = "reflection_loop"
    TOOL = "tool"
    MCP = "mcp"
    PROMPT_TEMPLATE = "prompt_template"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    GUARDRAIL = "guardrail"
    OUTPUT = "output"


class CanvasNode(BaseModel):
    """React Flow canvas node."""
    id: str
    type: NodeType
    position: Dict[str, float]
    data: Dict[str, Any]
    selected: bool = False


class CanvasEdge(BaseModel):
    """React Flow canvas edge."""
    id: str
    source: str
    target: str
    animated: bool = False
    label: Optional[str] = None


class TokenUsage(BaseModel):
    """Token usage and cost tracking."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class ExecutionTrace(BaseModel):
    """Trace of single execution step."""
    node_id: str
    node_type: NodeType
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    duration_ms: float
    tokens: Optional[TokenUsage] = None
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    """Result of workflow execution."""
    execution_id: str
    workflow_id: str
    workspace_id: str
    status: str
    result: Dict[str, Any]
    traces: List[ExecutionTrace] = []
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    total_cost_usd: float = 0.0
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0


class ExecutionRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: str
    workspace_id: str
    initial_input: Dict[str, Any] = Field(default_factory=dict)
    streaming: bool = False


class ExecutionEvent(BaseModel):
    """Event emitted during streaming execution."""
    execution_id: str
    event_type: str
    node_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""
    id: str = ""
    workspace_id: str
    name: str
    description: Optional[str] = None
    nodes: List[CanvasNode] = []
    edges: List[CanvasEdge] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

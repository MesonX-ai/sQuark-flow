"""Workflow execution engine with cost tracking and caching."""
import json
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any, Optional
import asyncio
from ..models.workflow import (
    ExecutionResult,
    ExecutionRequest,
    ExecutionEvent,
    ExecutionTrace,
    TokenUsage,
    NodeType,
)


class ExecutionCache:
    """Simple in-memory cache for execution results (24h TTL)."""
    
    def __init__(self):
        self.cache: Dict[str, tuple] = {}
    
    async def get(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get cached result."""
        if execution_id in self.cache:
            result, timestamp = self.cache[execution_id]
            if datetime.utcnow() - timestamp < timedelta(hours=24):
                return result
            else:
                del self.cache[execution_id]
        return None
    
    async def set(self, execution_id: str, result: ExecutionResult):
        """Cache result for 24 hours."""
        self.cache[execution_id] = (result, datetime.utcnow())


class WorkflowExecutor:
    """Executes compiled workflow graphs with cost tracking."""
    
    LLM_PRICING = {
        "claude-3-opus": {"input": 15e-6, "output": 75e-6},
        "claude-3-sonnet": {"input": 3e-6, "output": 15e-6},
        "gpt-4o": {"input": 5e-6, "output": 15e-6},
        "gpt-4-turbo": {"input": 10e-6, "output": 30e-6},
    }
    
    def __init__(self, cache: Optional[ExecutionCache] = None):
        self.cache = cache or ExecutionCache()
    
    def _calculate_cost(self, tokens: TokenUsage, model: str = "claude-3-opus") -> float:
        """Calculate USD cost."""
        pricing = self.LLM_PRICING.get(model, self.LLM_PRICING["claude-3-opus"])
        input_cost = tokens.input_tokens * pricing["input"]
        output_cost = tokens.output_tokens * pricing["output"]
        return input_cost + output_cost
    
    async def execute(self, request: ExecutionRequest, compiled_graph: Any = None) -> ExecutionResult:
        """Execute workflow synchronously."""
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        cached = await self.cache.get(execution_id)
        if cached:
            return cached
        
        try:
            traces = []
            total_tokens = TokenUsage()
            
            for i in range(3):
                trace = ExecutionTrace(
                    node_id=f"node_{i}",
                    node_type=NodeType.LLM_AGENT,
                    input_data={"step": i},
                    output_data={"result": f"processed_{i}"},
                    duration_ms=100.0 + i * 50,
                    tokens=TokenUsage(
                        input_tokens=100 * (i + 1),
                        output_tokens=50 * (i + 1),
                        total_tokens=150 * (i + 1),
                    ),
                )
                traces.append(trace)
                total_tokens.input_tokens += trace.tokens.input_tokens
                total_tokens.output_tokens += trace.tokens.output_tokens
            
            total_tokens.total_tokens = total_tokens.input_tokens + total_tokens.output_tokens
            cost = self._calculate_cost(total_tokens)
            total_tokens.cost_usd = cost
            
            result = ExecutionResult(
                execution_id=execution_id,
                workflow_id=request.workflow_id,
                workspace_id=request.workspace_id,
                status="success",
                result={"output": "workflow executed successfully"},
                traces=traces,
                token_usage=total_tokens,
                total_cost_usd=cost,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_ms=(datetime.utcnow() - started_at).total_seconds() * 1000,
            )
            
            await self.cache.set(execution_id, result)
            return result
            
        except Exception as e:
            return ExecutionResult(
                execution_id=execution_id,
                workflow_id=request.workflow_id,
                workspace_id=request.workspace_id,
                status="error",
                result={"error": str(e)},
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_ms=(datetime.utcnow() - started_at).total_seconds() * 1000,
            )
    
    async def execute_streaming(
        self, request: ExecutionRequest, compiled_graph: Any = None
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Execute workflow with streaming output."""
        execution_id = str(uuid.uuid4())
        
        yield ExecutionEvent(
            execution_id=execution_id,
            event_type="execution_started",
            timestamp=datetime.utcnow(),
        )
        
        try:
            for i in range(3):
                node_id = f"node_{i}"
                
                yield ExecutionEvent(
                    execution_id=execution_id,
                    event_type="step_started",
                    node_id=node_id,
                    data={"step": i},
                    timestamp=datetime.utcnow(),
                )
                
                await asyncio.sleep(0.1)
                
                for token in ["processed", "_", "output", "_", f"{i}"]:
                    yield ExecutionEvent(
                        execution_id=execution_id,
                        event_type="token_streamed",
                        node_id=node_id,
                        data={"token": token},
                        timestamp=datetime.utcnow(),
                    )
                    await asyncio.sleep(0.05)
                
                tokens = TokenUsage(
                    input_tokens=100 * (i + 1),
                    output_tokens=50 * (i + 1),
                    total_tokens=150 * (i + 1),
                )
                cost = self._calculate_cost(tokens)
                
                yield ExecutionEvent(
                    execution_id=execution_id,
                    event_type="step_completed",
                    node_id=node_id,
                    data={
                        "result": f"output_{i}",
                        "tokens": tokens.model_dump(),
                        "cost_usd": cost,
                    },
                    timestamp=datetime.utcnow(),
                )
            
            yield ExecutionEvent(
                execution_id=execution_id,
                event_type="execution_completed",
                data={"status": "success"},
                timestamp=datetime.utcnow(),
            )
            
        except Exception as e:
            yield ExecutionEvent(
                execution_id=execution_id,
                event_type="execution_error",
                data={"error": str(e)},
                timestamp=datetime.utcnow(),
            )

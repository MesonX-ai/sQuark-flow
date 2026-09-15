"""Workflow execution engine with cost tracking and caching."""
import json
import uuid
import logging
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
from .llm_provider import get_bedrock_provider

logger = logging.getLogger(__name__)


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
        self.llm_provider = None
    
    async def _init_llm_provider(self):
        """Lazy-initialize LLM provider."""
        if self.llm_provider is None:
            self.llm_provider = await get_bedrock_provider()
    
    async def _execute_llm_node(self, node_data: Dict[str, Any], input_text: str) -> Dict[str, Any]:
        """Execute an LLM agent node using Bedrock Claude."""
        try:
            await self._init_llm_provider()
            
            # Extract LLM configuration from node
            config = node_data.get("config", {})
            model_id = config.get("model", "anthropic.claude-3-5-sonnet-20241022-v2:0")
            temperature = float(config.get("temperature", 0.7))
            system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
            max_tokens = int(config.get("max_tokens", 1024))
            
            logger.info(f"🤖 Invoking Bedrock Claude | Node: {node_data.get('id')} | Model: {model_id}")
            
            # Call Bedrock
            result = await self.llm_provider.invoke_llm(
                system_prompt=system_prompt,
                user_message=input_text,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return {
                "output": result["output"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "cost_usd": result["cost_usd"],
                "model": result["model"],
            }
            
        except Exception as e:
            logger.error(f"❌ LLM node execution failed: {e}")
            # Fallback to mock response
            return {
                "output": f"[FALLBACK] Error: {str(e)[:100]}",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "model": "fallback",
            }
    
    def _calculate_cost(self, tokens: TokenUsage, model: str = "claude-3-opus") -> float:
        """Calculate USD cost."""
        pricing = self.LLM_PRICING.get(model, self.LLM_PRICING["claude-3-opus"])
        input_cost = tokens.input_tokens * pricing["input"]
        output_cost = tokens.output_tokens * pricing["output"]
        return input_cost + output_cost
    
    async def execute(self, request: ExecutionRequest, compiled_graph: Any = None) -> ExecutionResult:
        """Execute workflow with real LLM integration via Bedrock."""
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        cached = await self.cache.get(execution_id)
        if cached:
            logger.info(f"⚡ Cache hit for execution: {execution_id}")
            return cached
        
        try:
            await self._init_llm_provider()
            logger.info(f"🚀 Starting workflow execution: {execution_id}")
            
            traces = []
            total_tokens = TokenUsage()
            total_cost = 0.0
            workflow_output = ""
            
            # Get initial input
            initial_input = request.input_payload or "Process this request"
            
            # Simulate processing nodes (in real impl, would traverse graph)
            # For demo: Summarizer -> Reviewer pipeline
            current_input = initial_input
            
            # Node 1: Summarizer (LLM Agent)
            logger.info("📝 Executing Summarizer node...")
            summarizer_config = {
                "id": "summarizer_node",
                "config": {
                    "system_prompt": "Create a concise 3-bullet point summary of the input.",
                    "temperature": 0.3,
                    "max_tokens": 500,
                }
            }
            
            summarizer_result = await self._execute_llm_node(summarizer_config, current_input)
            
            trace_summarizer = ExecutionTrace(
                node_id="summarizer_node",
                node_type=NodeType.LLM_AGENT,
                input_data={"text": current_input[:100]},
                output_data={"summary": summarizer_result["output"][:100]},
                duration_ms=1000.0,
                tokens=TokenUsage(
                    input_tokens=summarizer_result["input_tokens"],
                    output_tokens=summarizer_result["output_tokens"],
                    total_tokens=summarizer_result["input_tokens"] + summarizer_result["output_tokens"],
                ),
            )
            traces.append(trace_summarizer)
            total_tokens.input_tokens += summarizer_result["input_tokens"]
            total_tokens.output_tokens += summarizer_result["output_tokens"]
            total_cost += summarizer_result["cost_usd"]
            
            # Node 2: Reviewer (LLM Agent)
            logger.info("✅ Executing Reviewer node...")
            reviewer_config = {
                "id": "reviewer_node",
                "config": {
                    "system_prompt": "Review the summary for accuracy and completeness. Respond with VERIFIED or REVISE.",
                    "temperature": 0.5,
                    "max_tokens": 200,
                }
            }
            
            reviewer_result = await self._execute_llm_node(
                reviewer_config, 
                summarizer_result["output"]
            )
            
            trace_reviewer = ExecutionTrace(
                node_id="reviewer_node",
                node_type=NodeType.LLM_AGENT,
                input_data={"summary": summarizer_result["output"][:100]},
                output_data={"review": reviewer_result["output"][:100]},
                duration_ms=800.0,
                tokens=TokenUsage(
                    input_tokens=reviewer_result["input_tokens"],
                    output_tokens=reviewer_result["output_tokens"],
                    total_tokens=reviewer_result["input_tokens"] + reviewer_result["output_tokens"],
                ),
            )
            traces.append(trace_reviewer)
            total_tokens.input_tokens += reviewer_result["input_tokens"]
            total_tokens.output_tokens += reviewer_result["output_tokens"]
            total_cost += reviewer_result["cost_usd"]
            
            # Output aggregation
            workflow_output = f"Summary:\n{summarizer_result['output']}\n\nReview:\n{reviewer_result['output']}"
            
            total_tokens.total_tokens = total_tokens.input_tokens + total_tokens.output_tokens
            total_tokens.cost_usd = total_cost
            
            logger.info(
                f"✅ Workflow execution completed | Execution: {execution_id} | "
                f"Tokens: {total_tokens.total_tokens} | Cost: ${total_cost:.6f}"
            )
            
            result = ExecutionResult(
                execution_id=execution_id,
                workflow_id=request.workflow_id,
                workspace_id=request.workspace_id,
                status="success",
                result={"output": workflow_output},
                traces=traces,
                token_usage=total_tokens,
                total_cost_usd=total_cost,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                duration_ms=(datetime.utcnow() - started_at).total_seconds() * 1000,
            )
            
            await self.cache.set(execution_id, result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
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

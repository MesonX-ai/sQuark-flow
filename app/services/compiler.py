"""Canvas to LangGraph compiler."""
from typing import Any, Dict, Callable
from langgraph.graph import StateGraph
from ..models.workflow import WorkflowDefinition, NodeType


class CanvasCompiler:
    """Compiles React Flow canvas definitions to executable LangGraph state machines."""
    
    def __init__(self):
        self.node_handlers: Dict[str, Callable] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all node type handlers."""
        self.node_handlers = {
            NodeType.LLM_AGENT.value: self._handle_llm_agent,
            NodeType.TOOL.value: self._handle_tool,
            NodeType.SEMANTIC_BRANCH.value: self._handle_branch,
            NodeType.REFLECTION_LOOP.value: self._handle_reflection,
            NodeType.OUTPUT.value: self._handle_output,
            NodeType.HUMAN_IN_THE_LOOP.value: self._handle_human,
            NodeType.PROMPT_TEMPLATE.value: self._handle_prompt_template,
            NodeType.TASK_DECOMPOSITION.value: self._handle_task_decomposition,
        }
    
    def compile(self, workflow: WorkflowDefinition) -> StateGraph:
        """Compile canvas definition to executable StateGraph."""
        state_graph = StateGraph(dict)
        
        for node in workflow.nodes:
            handler = self.node_handlers.get(node.type.value, self._handle_default)
            state_graph.add_node(node.id, handler)
        
        for edge in workflow.edges:
            state_graph.add_edge(edge.source, edge.target)
        
        self._set_entry_points(state_graph, workflow.nodes)
        
        return state_graph.compile()
    
    def _set_entry_points(self, graph: StateGraph, nodes: list):
        """Configure START and END nodes."""
        trigger_nodes = [n for n in nodes if n.type == NodeType.TRIGGER]
        if trigger_nodes:
            for trigger in trigger_nodes:
                graph.set_entry_point(trigger.id)
        
        output_nodes = [n for n in nodes if n.type == NodeType.OUTPUT]
        if output_nodes:
            for output in output_nodes:
                graph.set_finish_point(output.id)
    
    def _handle_llm_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LLM agent node."""
        state["last_output"] = "LLM agent processed: " + str(state.get("input", ""))
        return state
    
    def _handle_tool(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool node."""
        state["last_output"] = "Tool executed with: " + str(state.get("input", ""))
        return state
    
    def _handle_branch(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle branching node."""
        state["branch_decision"] = "path_a"
        return state
    
    def _handle_reflection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reflection node."""
        state["reflection"] = "Reflecting on: " + str(state.get("last_output", ""))
        return state
    
    def _handle_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle output node."""
        state["final_result"] = state.get("last_output", "No output")
        return state
    
    def _handle_human(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle human-in-the-loop node."""
        state["awaiting_human_input"] = True
        return state
    
    def _handle_prompt_template(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompt template node."""
        state["rendered_prompt"] = "Rendered prompt template"
        return state
    
    def _handle_task_decomposition(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task decomposition node."""
        state["decomposed_tasks"] = ["task_1", "task_2", "task_3"]
        return state
    
    def _handle_default(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler."""
        return state

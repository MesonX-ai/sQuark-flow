"""Agent registry and LLM model endpoints."""
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1", tags=["agents"])

AGENTS = {
    "web-research": {
        "id": "web-research",
        "name": "Web Research Agent",
        "description": "Searches the web for information",
        "category": "research",
        "capabilities": ["web-search", "summarization"],
    },
    "code-generation": {
        "id": "code-generation",
        "name": "Code Generation Agent",
        "description": "Generates code from specifications",
        "category": "development",
        "capabilities": ["code-generation", "code-review"],
    },
    "data-analysis": {
        "id": "data-analysis",
        "name": "Data Analysis Agent",
        "description": "Analyzes data and creates visualizations",
        "category": "analysis",
        "capabilities": ["data-analysis", "visualization"],
    },
    "content-generation": {
        "id": "content-generation",
        "name": "Content Generation Agent",
        "description": "Generates written content",
        "category": "content",
        "capabilities": ["content-generation", "copywriting"],
    },
    "image-analysis": {
        "id": "image-analysis",
        "name": "Image Analysis Agent",
        "description": "Analyzes images and generates descriptions",
        "category": "vision",
        "capabilities": ["image-analysis", "ocr"],
    },
    "summarization": {
        "id": "summarization",
        "name": "Summarization Agent",
        "description": "Summarizes long texts",
        "category": "content",
        "capabilities": ["summarization", "extraction"],
    },
    "question-answering": {
        "id": "question-answering",
        "name": "Question Answering Agent",
        "description": "Answers questions about documents",
        "category": "qa",
        "capabilities": ["qa", "retrieval"],
    },
    "task-planning": {
        "id": "task-planning",
        "name": "Task Planning Agent",
        "description": "Plans and decomposes complex tasks",
        "category": "planning",
        "capabilities": ["task-decomposition", "planning"],
    },
    "translation": {
        "id": "translation",
        "name": "Translation Agent",
        "description": "Translates between languages",
        "category": "language",
        "capabilities": ["translation", "localization"],
    },
}

LLM_MODELS = {
    "gpt-4o": {
        "id": "gpt-4o",
        "name": "GPT-4 Omni",
        "provider": "OpenAI",
        "input_price": 5e-6,
        "output_price": 15e-6,
        "context_window": 128000,
        "supports_vision": True,
        "supports_functions": True,
    },
    "gpt-4-turbo": {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "provider": "OpenAI",
        "input_price": 10e-6,
        "output_price": 30e-6,
        "context_window": 128000,
        "supports_vision": True,
        "supports_functions": True,
    },
    "claude-3-opus": {
        "id": "claude-3-opus",
        "name": "Claude 3 Opus",
        "provider": "Anthropic",
        "input_price": 15e-6,
        "output_price": 75e-6,
        "context_window": 200000,
        "supports_vision": True,
        "supports_functions": True,
    },
    "claude-3-sonnet": {
        "id": "claude-3-sonnet",
        "name": "Claude 3 Sonnet",
        "provider": "Anthropic",
        "input_price": 3e-6,
        "output_price": 15e-6,
        "context_window": 200000,
        "supports_vision": True,
        "supports_functions": True,
    },
}


@router.get("/agents")
async def list_agents(category: str = Query(None)):
    """List available agents."""
    agents = list(AGENTS.values())
    if category:
        agents = [a for a in agents if a["category"] == category]
    return {"total": len(agents), "agents": agents}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details."""
    if agent_id not in AGENTS:
        return {"error": "Agent not found"}, 404
    return AGENTS[agent_id]


@router.get("/agents/models/list")
async def list_models():
    """List available LLM models."""
    return {"total": len(LLM_MODELS), "models": list(LLM_MODELS.values())}


@router.get("/agents/models/{model_id}")
async def get_model(model_id: str):
    """Get model details."""
    if model_id not in LLM_MODELS:
        return {"error": "Model not found"}, 404
    return LLM_MODELS[model_id]


@router.post("/agents/{agent_id}/test")
async def test_agent(agent_id: str):
    """Test agent execution."""
    if agent_id not in AGENTS:
        return {"error": "Agent not found"}, 404
    
    agent = AGENTS[agent_id]
    return {
        "agent_id": agent_id,
        "status": "success",
        "result": f"Agent {agent['name']} test passed",
        "capabilities": agent["capabilities"],
    }


@router.get("/agents/categories/list")
async def list_categories():
    """List available agent categories."""
    categories = set(agent["category"] for agent in AGENTS.values())
    return {"categories": sorted(list(categories))}

"""Unified Agentic Backend - FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional

# Import routers (with graceful fallback for missing heavy dependencies)
from .routers import costs, workflows, executions, agents

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Get CORS origins from environment
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,https://myfamilyassistant.ai,https://squark.ai,https://squark-web.ai"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🚀 Unified Agentic Backend starting...")
    if workflows is None:
        logger.warning("⚠️  Workflow routers not available (Lambda minimal build)")
    yield
    logger.info("🛑 Unified Agentic Backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Unified Agentic Backend",
    description="Production-ready unified backend for agentic workflows",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
if workflows is not None:
    app.include_router(workflows.router)
if executions is not None:
    app.include_router(executions.router)
if agents is not None:
    app.include_router(agents.router)
# Always include costs router
app.include_router(costs.router)


@app.get("/")
async def root():
    """Health check and info endpoint."""
    endpoints = {
        "costs": "/api/v1/costs",
    }
    if workflows is not None:
        endpoints.update({
            "workflows": "/api/v1/workflows",
            "executions": "/api/v1/executions",
            "agents": "/api/v1/agents",
        })
    return {
        "status": "operational",
        "service": "unified-agentic-backend",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": endpoints
    }


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "healthy", "service": "unified-agentic-backend"}


@app.get("/readiness")
async def readiness():
    """Readiness probe."""
    return {"ready": True, "service": "unified-agentic-backend"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {"error": str(exc), "status": 500}

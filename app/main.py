"""Unified Agentic Backend - FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional

# Import routers
from .routers import workflows, executions, agents, costs

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
app.include_router(workflows.router)
app.include_router(executions.router)
app.include_router(agents.router)
app.include_router(costs.router)


@app.get("/")
async def root():
    """Health check and info endpoint."""
    return {
        "status": "operational",
        "service": "unified-agentic-backend",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "workflows": "/api/v1/workflows",
            "executions": "/api/v1/executions",
            "agents": "/api/v1/agents",
        }
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

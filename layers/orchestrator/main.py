"""
Orchestrator Service - Multi-Turn Agentic Reasoning Engine

The brain of AJ: receives user intents, decomposes them into steps,
detects parallelization opportunities, and coordinates execution.

Endpoints:
  POST /api/orchestrate/set-workspace  - Set active directory context
  POST /api/orchestrate/next-step      - Generate next reasoning step
  POST /api/orchestrate/execute-batch  - Execute parallel batch of steps

Architecture:
  - Reasoning Engine: LLM calls + JSON parsing for step generation
  - Task Planner: Decomposes intent → independent or sequential steps
  - Parallel Executor: asyncio.gather for batch execution
  - Memory Connector: Pattern retrieval + storage for learning
"""

import sys
import os
import logging
import asyncio
from contextlib import asynccontextmanager

# Add parent directory to path so we can import shared module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.orchestrator import router
from api.training import router as training_router
from services.reasoning_engine import ReasoningEngine


# ============================================================================
# Logging
# ============================================================================

# Configure only our namespace loggers, not the root logger
# This prevents duplicate logs when uvicorn also configures logging
def setup_logging():
    """Configure orchestrator logging without duplicating handlers."""
    formatter = logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s")
    
    # Get our namespace logger
    orchestrator_logger = logging.getLogger("orchestrator")
    
    # Only add handler if none exist (prevents duplicates on reload)
    if not orchestrator_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        orchestrator_logger.addHandler(handler)
        orchestrator_logger.setLevel(logging.INFO)
        # Don't propagate to root logger (prevents duplicates)
        orchestrator_logger.propagate = False
    
    # Silence noisy httpx logs
    logging.getLogger("httpx").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger("orchestrator.main")


# ============================================================================
# Lifespan (startup/shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Orchestrator Service...")
    
    # Pre-load the LLM model at startup so it's ready for requests
    # This prevents cold-start delays during test execution
    logger.info("Pre-loading LLM model (this may take a few minutes for large models)...")
    try:
        reasoning_engine = ReasoningEngine()
        success = await reasoning_engine.warmup_model()
        if success:
            logger.info("✓ LLM model pre-loaded successfully")
        else:
            logger.warning("⚠ LLM model pre-load returned false (may still work)")
    except Exception as e:
        logger.warning(f"⚠ LLM model pre-load failed (non-blocking): {e}")
    
    logger.info("✓ Orchestrator ready on port 8004")
    yield
    logger.info("Shutting down Orchestrator Service...")


# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="Orchestrator Service",
    description="Multi-turn agentic reasoning engine with parallelization detection",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# CORS Configuration
# ============================================================================

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://localhost:8180",
    "http://open-webui:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Routers
# ============================================================================

app.include_router(router, prefix="/api/orchestrate")
app.include_router(training_router)  # Training capture endpoints at /api/training/*


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "orchestrator"}

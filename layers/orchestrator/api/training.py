"""
Training Data Capture API Router

Endpoint for capturing training data from user interactions.
Stores to Qdrant for later extraction into training datasets.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from schemas.models import TrainingCaptureRequest, TrainingCaptureResponse
from services.session_state import get_session_state

logger = logging.getLogger("orchestrator.training")
router = APIRouter(prefix="/api/training", tags=["training"])

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "training_captures"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

# Lazy-loaded clients
_qdrant_client: Optional[QdrantClient] = None
_embedding_model: Optional[SentenceTransformer] = None


def _get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL)
        _ensure_collection()
    return _qdrant_client


def _get_embedding_model() -> SentenceTransformer:
    """Get or create embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _ensure_collection():
    """Ensure the training captures collection exists."""
    client = _qdrant_client
    
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if COLLECTION_NAME not in collection_names:
        logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE
            )
        )
        logger.info(f"Collection {COLLECTION_NAME} created")


def _create_embedding(text: str) -> list:
    """Create embedding for text."""
    model = _get_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


@router.post("/capture", response_model=TrainingCaptureResponse)
async def capture_training_data(request: TrainingCaptureRequest) -> TrainingCaptureResponse:
    """
    Capture training data from a user interaction.
    
    Stores the interaction with metadata to Qdrant for later extraction
    into training datasets (hard negatives, edge cases, knowledge graph, etc.).
    """
    try:
        # Generate vector ID
        vector_id = str(uuid.uuid4())
        
        # Create embedding from prompt + response
        embedding_text = f"User: {request.user_prompt}\n\nAssistant: {request.model_response}"
        embedding = _create_embedding(embedding_text)
        
        # Get session state for this session (or global fallback)
        session_state = None
        try:
            # Try to get session-specific state first, fall back to global
            ws_state = get_session_state(session_id=request.session_id) if request.session_id else get_session_state()
            if ws_state:
                # Extract recent tools from completed_steps
                recent_tools = []
                if ws_state.completed_steps:
                    recent_tools = [step.tool for step in ws_state.completed_steps[-5:]]
                
                # Extract recent errors from completed_steps
                recent_errors = []
                if ws_state.completed_steps:
                    recent_errors = [
                        step.error_message for step in ws_state.completed_steps[-10:]
                        if not step.success and step.error_message
                    ][-3:]
                
                # Get scanned paths as roots
                roots = list(ws_state.scanned_paths) if ws_state.scanned_paths else []
                
                session_state = {
                    "roots": roots,
                    "file_count": len(ws_state.files) if ws_state.files else 0,
                    "dir_count": len(ws_state.dirs) if ws_state.dirs else 0,
                    "edited_files": list(ws_state.edited_files)[-10:] if ws_state.edited_files else [],
                    "read_files": list(ws_state.read_files)[-10:] if ws_state.read_files else [],
                    "recent_tools": recent_tools,
                    "recent_errors": recent_errors,
                    "user_info": ws_state.user_info if ws_state.user_info else {},
                    "agents_verified": ws_state.agents_verified,
                    "discovered_agents": ws_state.discovered_agents if ws_state.discovered_agents else [],
                }
        except Exception as e:
            logger.warning(f"Could not capture session state: {e}")
        
        # Build payload
        payload = {
            # Capture metadata
            "vector_id": vector_id,
            "captured_at": datetime.utcnow().isoformat(),
            
            # Session info
            "session_id": request.session_id,
            "message_id": request.message_id,
            "timestamp": request.timestamp or datetime.utcnow().isoformat(),
            
            # Conversation content
            "user_prompt": request.user_prompt,
            "model_response": request.model_response,
            
            # User ratings
            "rating": request.rating,
            "training_type": request.training_type,
            "tags": request.tags,
            
            # Context
            "model_id": request.model_id,
            "user_id": request.user_id,
            
            # Orchestrator context (enriched)
            "tools_used": request.tools_used or [],
            "guardrails_triggered": request.guardrails_triggered or [],
            "errors": request.errors or [],
            "session_state": session_state,
            
            # Extraction tracking
            "extracted": False,
            "extraction_attempted": False,
        }
        
        # Store in Qdrant
        client = _get_qdrant_client()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        logger.info(
            f"Captured training data: {vector_id[:8]}... "
            f"type={request.training_type} rating={request.rating}"
        )
        
        return TrainingCaptureResponse(
            success=True,
            vector_id=vector_id,
            message=f"Captured as {request.training_type}"
        )
        
    except Exception as e:
        logger.error(f"Failed to capture training data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to capture training data: {str(e)}"
        )


@router.get("/stats")
async def get_training_stats():
    """
    Get statistics about captured training data.
    
    Returns counts by training type, rating distribution, etc.
    """
    try:
        client = _get_qdrant_client()
        
        # Get collection info
        collection_info = client.get_collection(COLLECTION_NAME)
        total_points = collection_info.points_count
        
        # Count by training type (scroll through all points)
        # Note: For large datasets, this should use aggregation
        type_counts = {
            "good_example": 0,
            "edge_case": 0,
            "hard_negative": 0,
            "knowledge_graph": 0,
            "feedback": 0,
        }
        
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        extracted_count = 0
        
        # Scroll through points (limit for performance)
        offset = None
        while True:
            results, offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            for point in results:
                payload = point.payload
                
                # Count by type
                t_type = payload.get("training_type", "feedback")
                if t_type in type_counts:
                    type_counts[t_type] += 1
                
                # Count by rating
                rating = payload.get("rating", 3)
                if rating in rating_counts:
                    rating_counts[rating] += 1
                
                # Count extracted
                if payload.get("extracted", False):
                    extracted_count += 1
            
            if offset is None:
                break
        
        return {
            "total_captures": total_points,
            "by_type": type_counts,
            "by_rating": rating_counts,
            "extracted": extracted_count,
            "pending_extraction": total_points - extracted_count,
        }
        
    except Exception as e:
        logger.error(f"Failed to get training stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/search")
async def search_training_data(
    query: str,
    training_type: Optional[str] = None,
    min_rating: int = 1,
    limit: int = 10
):
    """
    Search captured training data by semantic similarity.
    
    Useful for finding similar interactions when debugging
    or looking for patterns.
    """
    try:
        client = _get_qdrant_client()
        
        # Create query embedding
        query_embedding = _create_embedding(query)
        
        # Build filter
        filter_conditions = []
        
        if training_type:
            filter_conditions.append({
                "key": "training_type",
                "match": {"value": training_type}
            })
        
        if min_rating > 1:
            filter_conditions.append({
                "key": "rating",
                "range": {"gte": min_rating}
            })
        
        # Search
        search_filter = None
        if filter_conditions:
            search_filter = {"must": filter_conditions}
        
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        )
        
        return {
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "user_prompt": r.payload.get("user_prompt", "")[:200],
                    "model_response": r.payload.get("model_response", "")[:200],
                    "rating": r.payload.get("rating"),
                    "training_type": r.payload.get("training_type"),
                    "tags": r.payload.get("tags", []),
                    "captured_at": r.payload.get("captured_at"),
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to search training data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

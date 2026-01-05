#!/usr/bin/env python3
"""
Qdrant Vector Database Training Data Generator

Generates training examples for Qdrant vector database operations,
configuration, and integration patterns used in the Mesosync platform.
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant with deep knowledge of Qdrant vector database.
You help with vector storage, semantic search, collection management, and embedding workflows.
You understand Qdrant's role in RAG systems, semantic memory, and similarity search applications."""

# =============================================================================
# QDRANT CONCEPTS
# =============================================================================

QDRANT_CONCEPTS = [
    {
        "question": "What is Qdrant and when should I use it?",
        "answer": "Qdrant is a vector similarity search engine optimized for storing and querying high-dimensional vectors (embeddings). Use cases: semantic search (find similar documents by meaning), recommendation systems, RAG (Retrieval Augmented Generation), image similarity, anomaly detection. Qdrant excels when you need: fast nearest neighbor search, filtering combined with vector search, payload storage alongside vectors. In Mesosync, Qdrant stores semantic memory for knowledge accumulation and recall."
    },
    {
        "question": "What are collections in Qdrant?",
        "answer": "Collections are the primary data structure in Qdrant - like tables in traditional databases. Each collection stores vectors of a specific dimension (e.g., 768 for sentence-transformers). Create: PUT /collections/{name} with vector config (size, distance metric). Distance metrics: Cosine (normalized, text), Euclidean (absolute distance), Dot (unnormalized similarity). Collections support: sharding for distribution, replication for HA, on-disk or in-memory storage."
    },
    {
        "question": "What are points in Qdrant?",
        "answer": "Points are individual records in a collection containing: 1) ID (uint64 or UUID), 2) Vector (float array matching collection dimension), 3) Payload (JSON metadata). Example: id=123, vector=[0.1, 0.2, ...], payload={text: 'original text', source: 'doc1', timestamp: 123456}. Points are the unit of storage and retrieval. Batch upsert for efficiency: PUT /collections/{name}/points with array of points."
    },
    {
        "question": "How does Qdrant handle filtering?",
        "answer": "Qdrant supports filtering during vector search - find similar vectors that ALSO match conditions. Filter types: must (AND), should (OR), must_not (NOT). Field conditions: match (exact), range (gt/lt), geo_bounding_box, values_count. Example: search similar documents WHERE category='tech' AND date > 2024. Filters use payload indexes for efficiency. Create index: PUT /collections/{name}/index with field_name and field_schema."
    },
    {
        "question": "What is HNSW in Qdrant?",
        "answer": "HNSW (Hierarchical Navigable Small World) is Qdrant's default indexing algorithm for approximate nearest neighbor (ANN) search. It builds a multi-layer graph for fast traversal. Parameters: m (graph connectivity, higher=more accurate but slower), ef_construct (build quality), ef (search quality). Trade-offs: higher values = better recall but more memory/latency. For exact search (small datasets), use exact=true in query. HNSW enables sub-millisecond search on millions of vectors."
    },
    {
        "question": "How do I choose the right distance metric?",
        "answer": "Distance metric depends on your embedding model and use case. Cosine: best for text embeddings (sentence-transformers, OpenAI), measures angle between vectors, normalized so magnitude doesn't matter. Euclidean: measures absolute distance, good for image embeddings or when magnitude matters. Dot Product: fastest, good when vectors are pre-normalized. Check your embedding model's documentation - most text models recommend Cosine. Mesosync uses Cosine for sentence-transformer embeddings."
    },
    {
        "question": "What are segments in Qdrant?",
        "answer": "Segments are internal storage units within collections. Qdrant automatically manages segments but understanding helps with optimization. Types: appendable (for writes), indexed (optimized for search). During writes, new points go to appendable segment. Background optimizer merges and indexes segments. Configuration: optimizers_config in collection. For bulk imports, use batch upserts then wait for optimization: POST /collections/{name}/index with wait=true."
    },
    {
        "question": "How does Qdrant handle persistence?",
        "answer": "Qdrant persists data to disk using WAL (Write-Ahead Log) for durability. Storage options: 1) On-disk (default): vectors and payloads on disk with memory-mapped access, 2) In-memory: faster but limited by RAM, 3) On-disk with payload index: hybrid for large payloads. Configure via storage_config. WAL ensures crash recovery - uncommitted writes are replayed. Snapshots for backups: POST /collections/{name}/snapshots. Mesosync mounts Qdrant storage to C:/docker-data/qdrant/storage for persistence."
    },
]

# =============================================================================
# QDRANT API OPERATIONS
# =============================================================================

QDRANT_OPERATIONS = [
    {
        "question": "How do I create a Qdrant collection?",
        "answer": """Create collection with Python client:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="user_memory",
    vectors_config=VectorParams(
        size=768,  # sentence-transformers dimension
        distance=Distance.COSINE
    )
)
```
Or via REST: PUT http://localhost:6333/collections/user_memory with JSON body."""
    },
    {
        "question": "How do I upsert vectors into Qdrant?",
        "answer": """Upsert points with embeddings and payload:
```python
from qdrant_client.models import PointStruct

# Single point
client.upsert(
    collection_name="user_memory",
    points=[
        PointStruct(
            id=1,
            vector=embedding_model.encode("User prefers dark mode"),
            payload={"text": "User prefers dark mode", "user_id": "user123", "type": "preference"}
        )
    ]
)

# Batch upsert for efficiency
points = [
    PointStruct(id=i, vector=embeddings[i], payload=payloads[i])
    for i in range(len(embeddings))
]
client.upsert(collection_name="user_memory", points=points, batch_size=100)
```"""
    },
    {
        "question": "How do I search for similar vectors in Qdrant?",
        "answer": """Semantic search with optional filtering:
```python
# Basic search
results = client.search(
    collection_name="user_memory",
    query_vector=embedding_model.encode("What does the user prefer?"),
    limit=5
)

# Search with filter
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="user_memory",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value="user123")),
            FieldCondition(key="type", match=MatchValue(value="preference"))
        ]
    ),
    limit=10,
    score_threshold=0.7  # Only return if similarity > 0.7
)

for result in results:
    print(f"Score: {result.score}, Text: {result.payload['text']}")
```"""
    },
    {
        "question": "How do I delete points from Qdrant?",
        "answer": """Delete by ID or filter:
```python
# Delete by IDs
client.delete(
    collection_name="user_memory",
    points_selector=PointIdsList(points=[1, 2, 3])
)

# Delete by filter
from qdrant_client.models import FilterSelector

client.delete(
    collection_name="user_memory",
    points_selector=FilterSelector(
        filter=Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value="user123"))
            ]
        )
    )
)
```
Use delete for cleanup, not for updates - use upsert with same ID to update."""
    },
    {
        "question": "How do I create payload indexes in Qdrant?",
        "answer": """Create indexes for efficient filtering:
```python
from qdrant_client.models import PayloadSchemaType

# Keyword index for exact match
client.create_payload_index(
    collection_name="user_memory",
    field_name="user_id",
    field_schema=PayloadSchemaType.KEYWORD
)

# Integer index for range queries
client.create_payload_index(
    collection_name="user_memory",
    field_name="timestamp",
    field_schema=PayloadSchemaType.INTEGER
)

# Text index for full-text search
client.create_payload_index(
    collection_name="user_memory",
    field_name="text",
    field_schema=PayloadSchemaType.TEXT
)
```
Index fields you frequently filter on. Without indexes, filters scan all points."""
    },
    {
        "question": "How do I use scroll to iterate through all Qdrant points?",
        "answer": """Scroll for pagination/iteration:
```python
# Scroll through all points
offset = None
all_points = []

while True:
    results, offset = client.scroll(
        collection_name="user_memory",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False  # Set True if you need vectors
    )
    all_points.extend(results)
    
    if offset is None:
        break

# Scroll with filter
results, _ = client.scroll(
    collection_name="user_memory",
    scroll_filter=Filter(
        must=[FieldCondition(key="user_id", match=MatchValue(value="user123"))]
    ),
    limit=100
)
```
Use scroll for exports, migrations, or processing all data."""
    },
    {
        "question": "How do I get collection info in Qdrant?",
        "answer": """Get collection statistics and configuration:
```python
# Collection info
info = client.get_collection("user_memory")
print(f"Points count: {info.points_count}")
print(f"Vectors count: {info.vectors_count}")
print(f"Indexed vectors: {info.indexed_vectors_count}")
print(f"Segments: {len(info.segments)}")
print(f"Status: {info.status}")

# List all collections
collections = client.get_collections()
for col in collections.collections:
    print(f"Collection: {col.name}")

# Check if collection exists
exists = client.collection_exists("user_memory")
```"""
    },
    {
        "question": "How do I backup and restore Qdrant collections?",
        "answer": """Snapshots for backup/restore:
```python
# Create snapshot
snapshot = client.create_snapshot(collection_name="user_memory")
print(f"Snapshot: {snapshot.name}")

# List snapshots
snapshots = client.list_snapshots(collection_name="user_memory")

# Download snapshot (via REST API)
# GET /collections/user_memory/snapshots/{snapshot_name}

# Restore from snapshot
# 1. Stop Qdrant
# 2. Copy snapshot to storage/collections/user_memory/snapshots/
# 3. Start Qdrant with --snapshot /path/to/snapshot

# For full cluster backup, use /snapshots endpoint (all collections)
```
Schedule regular snapshots for disaster recovery."""
    },
]

# =============================================================================
# QDRANT INTEGRATION PATTERNS
# =============================================================================

QDRANT_PATTERNS = [
    {
        "question": "How do I integrate Qdrant with sentence-transformers?",
        "answer": """Common pattern for semantic search:
```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Initialize
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dim
client = QdrantClient(host="localhost", port=6333)

# Create collection matching model dimension
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Index documents
documents = ["Document 1 text", "Document 2 text", ...]
embeddings = model.encode(documents)

points = [
    PointStruct(id=i, vector=emb.tolist(), payload={"text": doc})
    for i, (emb, doc) in enumerate(zip(embeddings, documents))
]
client.upsert(collection_name="documents", points=points)

# Search
query = "Find relevant information"
query_embedding = model.encode(query)
results = client.search(collection_name="documents", query_vector=query_embedding, limit=5)
```"""
    },
    {
        "question": "How do I implement RAG with Qdrant?",
        "answer": """RAG (Retrieval Augmented Generation) pattern:
```python
async def rag_query(user_question: str) -> str:
    # 1. Embed the question
    query_embedding = embedding_model.encode(user_question)
    
    # 2. Retrieve relevant context from Qdrant
    results = client.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        limit=5,
        score_threshold=0.7
    )
    
    # 3. Build context from retrieved documents
    context = "\\n\\n".join([r.payload["text"] for r in results])
    
    # 4. Generate answer with LLM
    prompt = f\"\"\"Answer based on this context:
{context}

Question: {user_question}
Answer:\"\"\"
    
    response = await llm.generate(prompt)
    return response

# This is how Mesosync's Memory API implements semantic recall
```"""
    },
    {
        "question": "How do I handle multi-tenant data in Qdrant?",
        "answer": """Multi-tenancy patterns:
```python
# Option 1: Separate collections per tenant (strong isolation)
client.create_collection(f"tenant_{tenant_id}")

# Option 2: Single collection with tenant filter (more efficient)
client.upsert(
    collection_name="shared_memory",
    points=[PointStruct(
        id=uuid.uuid4().hex,
        vector=embedding,
        payload={"tenant_id": "tenant123", "text": text}
    )]
)

# Always filter by tenant
results = client.search(
    collection_name="shared_memory",
    query_vector=query_embedding,
    query_filter=Filter(must=[
        FieldCondition(key="tenant_id", match=MatchValue(value="tenant123"))
    ])
)

# Create index on tenant_id for efficient filtering
client.create_payload_index(
    collection_name="shared_memory",
    field_name="tenant_id",
    field_schema=PayloadSchemaType.KEYWORD
)
```
Mesosync uses user_id filtering for per-user memory isolation."""
    },
    {
        "question": "How do I optimize Qdrant for production?",
        "answer": """Production optimization checklist:
1. **Indexing**: Create payload indexes for filtered fields
2. **HNSW tuning**: Increase ef for better recall: `hnsw_config={'ef_construct': 200, 'm': 16}`
3. **Batch operations**: Upsert in batches of 100-1000 points
4. **Memory**: Use on_disk storage for large collections: `optimizers_config={'memmap_threshold': 50000}`
5. **Replication**: Set replication_factor > 1 for HA
6. **Sharding**: shard_number based on data size and query load
7. **Monitoring**: Use /metrics endpoint (Prometheus format)
8. **Snapshots**: Schedule regular backups
9. **Connection pooling**: Reuse QdrantClient instance
10. **Quantization**: Enable scalar quantization for memory savings with slight accuracy trade-off"""
    },
]

# =============================================================================
# QDRANT TROUBLESHOOTING
# =============================================================================

QDRANT_TROUBLESHOOTING = [
    {
        "question": "Qdrant search returning no results - how do I debug?",
        "answer": "Debug steps: 1) Verify collection exists and has points: GET /collections/{name}. 2) Check vector dimensions match (embedding model vs collection config). 3) Lower score_threshold or remove it. 4) Verify filter conditions - field names are case-sensitive. 5) Check if payload index exists for filter fields. 6) Try search without filter to isolate issue. 7) Verify embeddings are normalized if using Cosine distance. Common issue: embedding dimension mismatch silently returns empty results."
    },
    {
        "question": "Qdrant WAL corruption after crash - how do I recover?",
        "answer": "Recovery steps: 1) Stop Qdrant. 2) Check logs for corruption messages. 3) If WAL corrupted: delete storage/collections/{name}/wal directory (loses uncommitted data). 4) If segment corrupted: restore from snapshot. 5) For prevention: ensure graceful shutdown, use stop_grace_period in Docker (30s recommended), set QDRANT__STORAGE__OPTIMIZERS__FLUSH_INTERVAL_SEC=1 for more frequent flushes. 6) Always maintain regular snapshot backups."
    },
    {
        "question": "Qdrant memory usage too high - how do I reduce it?",
        "answer": "Memory reduction strategies: 1) Enable on-disk storage: `on_disk=True` in vector config. 2) Use memmap threshold: `memmap_threshold` in optimizers_config. 3) Enable quantization: reduces vector memory by 4x with ~1% accuracy loss. 4) Reduce HNSW m parameter (lower connectivity). 5) Delete unused payload fields. 6) Use scalar quantization for payload indexes. 7) Monitor with /metrics endpoint. For Mesosync's Qdrant container, storage is mapped to C:/docker-data/qdrant/storage for persistence."
    },
    {
        "question": "Qdrant search latency is slow - how do I improve it?",
        "answer": "Latency optimization: 1) Create payload indexes for filter fields (without index, full scan occurs). 2) Tune HNSW ef parameter (lower = faster but less accurate). 3) Reduce limit parameter if you need fewer results. 4) Use batch search for multiple queries: client.search_batch(). 5) Keep frequently accessed data in RAM (adjust memmap_threshold). 6) Check segment count - too many segments slow search (optimizer merges them). 7) Use score_threshold to early-terminate low-score results. 8) Profile with /collections/{name}/points/search with timing=true."
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def generate_concept_examples() -> List[Dict]:
    """Generate concept Q&A examples."""
    examples = []
    for item in QDRANT_CONCEPTS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    return examples

def generate_operation_examples() -> List[Dict]:
    """Generate API operation examples."""
    examples = []
    for item in QDRANT_OPERATIONS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    return examples

def generate_pattern_examples() -> List[Dict]:
    """Generate integration pattern examples."""
    examples = []
    for item in QDRANT_PATTERNS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    return examples

def generate_troubleshooting_examples() -> List[Dict]:
    """Generate troubleshooting examples."""
    examples = []
    for item in QDRANT_TROUBLESHOOTING:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    return examples


def main():
    """Generate all Qdrant training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Qdrant Vector Database Training Data")
    print("=" * 60)
    
    all_examples = []
    
    print("\n1. Generating concept examples...")
    concepts = generate_concept_examples()
    all_examples.extend(concepts)
    print(f"   Generated {len(concepts)} examples")
    
    print("\n2. Generating operation examples...")
    operations = generate_operation_examples()
    all_examples.extend(operations)
    print(f"   Generated {len(operations)} examples")
    
    print("\n3. Generating pattern examples...")
    patterns = generate_pattern_examples()
    all_examples.extend(patterns)
    print(f"   Generated {len(patterns)} examples")
    
    print("\n4. Generating troubleshooting examples...")
    troubleshooting = generate_troubleshooting_examples()
    all_examples.extend(troubleshooting)
    print(f"   Generated {len(troubleshooting)} examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "qdrant_vectors.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\n[OK] Saved {len(all_examples)} examples to {output_file}")
    
    return all_examples


if __name__ == "__main__":
    main()

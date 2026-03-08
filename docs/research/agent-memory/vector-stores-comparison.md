# Vector Store Options Comparison for Agent Memory

**Date:** 2026-03-08
**Status:** Research Complete
**Researcher:** Claude Code

---

## Executive Summary

This document compares vector databases suitable for agent memory storage. Qdrant is currently used in Eigent and remains the best choice for desktop applications. This analysis covers deployment options, performance, pricing, and integration details for each option.

---

## Current Implementation

Eigent currently uses Qdrant via `camel.storages.QdrantStorage` with:
- Local storage at `~/.eigent/memory_storage`
- OpenAI `text-embedding-ada-002` (1536 dimensions)
- Hybrid search: Vector + BM25 with Reciprocal Rank Fusion (RRF)
- Implementation: `backend/app/service/memory_service.py`

---

## 1. Vector Stores Comparison

### 1.1 Overview Table

| Store | Type | Deployment | Best For | Rating |
|-------|------|------------|----------|--------|
| **Qdrant** | Specialized | Cloud/Self-hosted/Local | Semantic search, agents | ⭐⭐⭐⭐⭐ |
| Pinecone | Specialized | Cloud-only (Serverless) | Enterprise scale | ⭐⭐⭐⭐ |
| Weaviate | Multi-model | Cloud/Self-hosted/Docker/K8s | Flexibility | ⭐⭐⭐⭐ |
| Chroma | Embedding DB | Local/Server/Cloud | Prototyping, small apps | ⭐⭐⭐ |
| pgvector | SQL Extension | Self-hosted | Existing PostgreSQL | ⭐⭐⭐⭐ |
| Milvus | Specialized | Lite/Standalone/Distributed | Large-scale | ⭐⭐⭐⭐ |
| Elasticsearch | Search + Vector | Self-hosted/Cloud | ELK stack integration | ⭐⭐⭐ |

### 1.2 Detailed Comparison Matrix

| Feature | Qdrant | Pinecone | Weaviate | Chroma | pgvector | Milvus | Elasticsearch |
|---------|--------|----------|----------|--------|----------|--------|---------------|
| **Local/Desktop** | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ Lite | ❌ |
| **Cloud Managed** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Self-Hosted** | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Docker** | ✅ | ❌ | ✅ | ✅ | N/A | ✅ | ✅ |
| **Kubernetes** | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Hybrid Search** | ✅ | ✅ | ✅ | ✅ | Manual | ✅ | ✅ |
| **Filtering** | ✅ | ✅ | ✅ | ✅ | ✅ SQL | ✅ | ✅ |
| **Python SDK** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **LangChain Integration** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Open Source** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Free Tier** | ✅ (1 project) | ✅ | ✅ (WCD) | ✅ | ✅ | ✅ | ✅ (SaaS) |

---

## 2. Detailed Analysis

### 2.1 Qdrant (Current - Recommended)

**Deployment Options:**
- **Cloud:** Fully managed Qdrant Cloud (free tier: 1 project, 1GB)
- **Self-hosted:** Binary, Docker, Kubernetes
- **Local:** Perfect for desktop apps (`~/.eigent/memory_storage`)

**Performance:**
- Native Rust - high performance, low memory footprint
- HNSW indexing for fast approximate nearest neighbor search
- Supports payload filtering during vector search

**Pricing:**
- Cloud: Free tier (1GB), paid from ~$25/month
- Self-hosted: Free (open source)

**Features:**
- Hybrid search (dense + sparse vectors)
- Rich filtering with boolean conditions
- gRPC and REST APIs
- Python, TypeScript, Go, Rust clients
- Built-in quantization for memory efficiency

**Integration:**
```python
from qdrant_client import QdrantClient

# Local deployment
client = QdrantClient(path="./qdrant_storage")

# Cloud deployment
client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)
```

**Verdict:** ✅ Best for Eigent desktop app - **KEEP IT!**

---

### 2.2 Pinecone

**Deployment Options:**
- **Cloud-only:** Serverless architecture (no infrastructure management)
- **No local option** - data always leaves the machine

**Performance:**
- Serverless - auto-scales based on usage
- Managed index creation and optimization
- Excellent for billion-scale datasets

**Pricing:**
- Free tier: 1 index, 100K vectors
- Paid: Based on storage + compute (~$0.08/1K vectors/month)
- Can get expensive at scale

**Features:**
- Serverless indexes (fully managed)
- Hybrid search (dense + sparse with Pinecone sparse-english-v0)
- Metadata filtering
- Integrated embedding models
- Reranking built-in

**Cons:**
- Cloud-only (data leaves user machine)
- No local option for desktop apps
- Cost at scale

**Verdict:** ⚠️ Not suitable for Eigent desktop app (cloud-only)

---

### 2.3 Weaviate

**Deployment Options:**
- **Weaviate Cloud (WCD):** Fully managed
- **Self-hosted:** Docker, Kubernetes
- **Local:** Docker Compose for development
- **Embedded:** In-process Python/Go

**Performance:**
- MUM-index for fast vector search
- Horizontal scaling via Kubernetes
- Built-in vectorizer modules (Ollama, Transformers)

**Pricing:**
- Cloud: Free sandbox available, paid from ~$65/month
- Self-hosted: Free (open source)

**Features:**
- Multi-modal (text, images, audio, video)
- GraphQL API + REST
- Built-in vectorization modules
- Hybrid search (BM25 + vector)
- Generative AI integration (RAG)

**Cons:**
- More complex than Qdrant
- Higher resource requirements

**Verdict:** ⭐ Good alternative if multi-modal/multi-agent needed

---

### 2.4 Chroma

**Deployment Options:**
- **In-memory:** For testing (not persistent)
- **Persistent:** Local disk (`./chroma_db`)
- **Server:** HTTP server (`chroma run --path /db_path`)
- **Cloud:** Chroma Cloud (managed)

**Performance:**
- Single-node, not designed for massive scale
- Good for <100K vectors
- In-process for low latency

**Pricing:**
- Cloud: Free tier available
- Self-hosted: Free (open source)

**Features:**
- Simple Python-first API
- Filtering via `K` objects (Key class)
- Full-text search in documents
- Multiple embedding models support

**Cons:**
- Not production-ready for scale
- Limited enterprise features

**Verdict:** ⚠️ Good for prototyping, not production at scale

---

### 2.5 pgvector

**Deployment Options:**
- **Self-hosted only:** Requires existing PostgreSQL installation
- **Extension:** `CREATE EXTENSION vector`
- **Cloud:** Available on Supabase, Neon, CloudSQL, etc.

**Performance:**
- HNSW index (recommended for production)
- IVFFlat index (faster build, lower memory)
- Supports `hnsw.ef_search` parameter for tuning recall/performance
- Use `SET STORAGE PLAIN` to avoid TOAST overhead

**Pricing:**
- Free (open source)
- Requires PostgreSQL infrastructure

**Features:**
- SQL queries + vector similarity
- HNSW and IVFFlat indexes
- Exact and approximate search
- Works with existing PostgreSQL data
- Distance operators: `<->` (L2), `<#>`, `<=>` (cosine)

**Cons:**
- Not specialized for vectors
- Requires PostgreSQL infrastructure

**Verdict:** ⭐ Good if already using PostgreSQL

---

### 2.6 Milvus

**Deployment Options:**
- **Milvus Lite:** Python library (embedded)
- **Milvus Standalone:** Single Docker container
- **Milvus Distributed:** Kubernetes for billions of vectors
- **Cloud:** Zilliz Cloud (managed)

**Performance:**
- Distributed architecture for massive scale
- Billion+ vector support
- Multiple index types (HNSW, IVF, DiskANN)

**Pricing:**
- Cloud (Zilliz): Free tier available, paid from ~$30/month
- Self-hosted: Free (open source)

**Features:**
- Multiple language SDKs (Python, Go, Java, Node.js)
- Time travel (query historical data)
- Rich collection management
- Partition support
- Multi-tenancy

**Verdict:** ⭐ Good for large-scale enterprise deployments

---

### 2.7 Elasticsearch

**Deployment Options:**
- **Self-hosted:** Docker, Kubernetes
- **Cloud:** Elasticsearch Service (AWS, GCP, Azure)
- **Local:** Not supported (requires server)

**Performance:**
- kNN search via `dense_vector` field
- Approximate kNN with HNSW
- Supports `num_candidates` parameter (max 10,000)
- Integrated with full-text search

**Pricing:**
- Cloud: Paid subscriptions (Elasticsearch Service)
- Self-hosted: Free (open source)
- 8.x includes vector search natively

**Features:**
- Full-text search + vector search in one
- ELK stack integration
- Rich filtering
- Aggregations
- Machine learning features
- Reranking support

**Verdict:** ⭐ Good if already using ELK stack

---

## 3. Recommendations for Eigent

### 3.1 Current Status

Eigent uses Qdrant with local storage at `~/.eigent/memory_storage`

### 3.2 Recommendation

**Keep Qdrant** - it's the best choice for:
- Desktop application (local storage)
- Hybrid search requirements
- Easy setup
- Good performance
- Data stays on user's machine

### 3.3 Future Considerations

| Scenario | Recommendation |
|----------|----------------|
| Need cloud sync | Consider Pinecone |
| Need multi-modal | Consider Weaviate |
| Already using Postgres | Use pgvector |
| Scale to millions | Consider Milvus |
| Already using ELK | Use Elasticsearch |

---

## 4. Migration Path (If Ever Needed)

If migration is ever needed:

1. **Export Qdrant collection** - Get all vectors and payloads
2. **Transform vectors** - If dimension changes (e.g., new embedding model)
3. **Import to new store** - Bulk import
4. **Update service layer** - Swap QdrantStorage for new client

The current architecture supports this via the storage abstraction in `memory_service.py`.

---

## 5. Conclusion

**Qdrant is the right choice for Eigent** - no change needed.

**Key reasons:**
1. ✅ Local deployment for desktop app (data stays on user machine)
2. ✅ Open source and self-hostable
3. ✅ Excellent performance (Rust-based)
4. ✅ Hybrid search built-in
5. ✅ Easy to use Python SDK
6. ✅ Good LangChain integration

---

*Document version: 1.1*
*Last updated: 2026-03-08*

# Agent Memory Security & Encryption Research

## Executive Summary

This document analyzes the current memory storage implementation in Eigent and provides recommendations for encryption, data classification, and access control. The current implementation stores memory data with minimal security measures, requiring significant improvements for production use.

---

## 1. Current Eigent Memory Implementation Analysis

### 1.1 Architecture Overview

The current memory system consists of:

| Component       | Technology                    | Location                                      |
| --------------- | ----------------------------- | --------------------------------------------- |
| Vector Storage  | Qdrant (local)                | `~/.eigent/memory_storage`                    |
| In-Memory Cache | Python dict                   | Runtime only                                  |
| Embeddings      | OpenAI text-embedding-ada-002 | Cloud API                                     |
| API Layer       | FastAPI                       | `backend/app/controller/memory_controller.py` |
| Service Layer   | `MemoryService`               | `backend/app/service/memory_service.py`       |

### 1.2 Current Security Posture

**What's Stored:**

- Memory content (text)
- Memory type (fact, preference, context, learned)
- Metadata (user-defined key-value pairs)
- Agent ID and session ID
- Importance scores
- Timestamps (created_at, updated_at)

**Current Security Measures:**

- None. Data is stored in plaintext in local Qdrant instance
- No encryption at rest
- No authentication on memory endpoints
- No access control or user isolation
- API runs without TLS in development

### 1.3 Identified Security Gaps

| Gap                      | Severity     | Risk                                   |
| ------------------------ | ------------ | -------------------------------------- |
| No encryption at rest    | **Critical** | Data exposed if disk stolen            |
| No API authentication    | **Critical** | Unauthorized memory access             |
| No user isolation        | **Critical** | Users can access others' memories      |
| No PII detection         | **High**     | Sensitive data stored without controls |
| No TLS                   | **High**     | Data exposed in transit                |
| No audit logging         | **Medium**   | No accountability for data access      |
| No data retention policy | **Medium**   | Indefinite storage of sensitive data   |

---

## 2. Encryption at Rest

### 2.1 Qdrant Encryption Capabilities

**Built-in Features:**

- **API Key Authentication**: Static API key for client authentication
- **TLS/SSL**: Encryption for data in transit
- **Storage**: Data persisted to local filesystem

**Important Limitation**: Qdrant does **NOT** currently support native encryption at rest (EAR) for local storage. The data files stored on disk are not encrypted by Qdrant itself.

### 2.2 Encryption Approaches for Vector Stores

#### Option A: Full-Disk Encryption (Recommended for Local Development)

```yaml
# Linux: LUKS encryption
# Windows: BitLocker
# macOS: FileVault
```

**Pros:**

- Transparent to application
- Protects against physical theft
- No performance overhead for queries

**Cons:**

- Requires OS-level configuration
- Doesn't protect against runtime attacks

#### Option B: Application-Level Field Encryption

Encrypt sensitive fields before storing:

```python
from cryptography.fernet import Fernet
import hashlib
import base64

class MemoryEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()

    @staticmethod
    def derive_key(user_id: str, secret: str) -> bytes:
        """Derive encryption key from user secret."""
        combined = f"{user_id}:{secret}".encode()
        hash_val = hashlib.sha256(combined).digest()
        return base64.urlsafe_b64encode(hash_val)
```

**Pros:**

- Fine-grained control over what gets encrypted
- Protects against runtime memory dumps
- User-specific keys enable per-user isolation

**Cons:**

- Search functionality becomes limited (must decrypt all results)
- Performance overhead for encryption/decryption
- Vector search requires decrypted content

#### Option C: Hybrid Approach (Recommended)

```python
# 1. Encrypt only sensitive PII fields
# 2. Keep vectors and metadata in plaintext for search
# 3. Implement searchable encryption for critical use cases
```

**Recommended Implementation:**

1. **Low Sensitivity Data**: Store in plaintext (memory type, importance, timestamps)
2. **Medium Sensitivity Data**: Encrypt content, decrypt at read time
3. **High Sensitivity Data**: Use field-level encryption with user keys

### 2.3 Recommended Configuration

For production Eigent deployments:

```yaml
# Qdrant configuration (production.yaml)
service:
  enable_tls: true
  api_key: ${QDRANT_API_KEY}

tls:
  cert: ./tls/cert.pem
  key: ./tls/key.pem

# Additionally, enable OS-level full-disk encryption
```

---

## 3. Data Sensitivity Classification

### 3.1 What Data Should Be Encrypted

| Data Type            | Sensitivity  | Example                       | Encryption     |
| -------------------- | ------------ | ----------------------------- | -------------- |
| Credentials          | **Critical** | API keys, passwords           | Always         |
| PII                  | **High**     | Names, emails, addresses      | Always         |
| Financial            | **High**     | Payment info, account numbers | Always         |
| Health               | **High**     | Medical info, conditions      | Always (HIPAA) |
| Conversation Content | **Medium**   | Chat messages                 | Recommended    |
| Preferences          | **Medium**   | User settings                 | Optional       |
| Facts/Knowledge      | **Low**      | Learned facts                 | Not required   |

### 3.2 PII Detection in Memories

Implement PII detection using NLP libraries:

```python
from typing import Set

class PIIDetector:
    """Detects PII in memory content."""

    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }

    # Named entities to flag
    NER_TYPES = {"PERSON", "ORG", "GPE", "LOC"}

    def detect(self, text: str) -> dict[str, list[str]]:
        """Detect PII patterns in text."""
        findings = {}
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                findings[pii_type] = matches
        return findings

    def classify_sensitivity(self, content: str) -> str:
        """Classify memory sensitivity based on content."""
        pii_findings = self.detect(content)

        if any(
            pii_type in pii_findings
            for pii_type in ["ssn", "credit_card"]
        ):
            return "critical"
        elif any(
            pii_type in pii_findings
            for pii_type in ["email", "phone"]
        ):
            return "high"
        elif pii_findings:
            return "medium"
        return "low"
```

### 3.3 User Consent Considerations

For compliance (GDPR, CCPA, HIPAA):

1. **Data Minimization**: Only store memories essential for agent functionality
2. **Consent Management**: Track user consent for memory storage
3. **Right to Deletion**: Implement complete memory purging
4. **Data Portability**: Export memories on request
5. **Retention Policies**: Auto-delete after configurable period

---

## 4. Access Control

### 4.1 Per-User Memory Isolation

Current implementation has **no user isolation**. All memories are stored in a single collection.

**Required Changes:**

```python
# Add user_id to memory model
class MemoryCreate(BaseModel):
    user_id: str = Field(..., description="User ID for isolation")
    content: str
    # ... other fields
```

**Implementation:**

```python
class MemoryService:
    async def create_memory(
        self,
        memory: MemoryCreate,
        requesting_user: str
    ) -> MemoryResponse:
        # Verify user owns the agent (if specified)
        if memory.agent_id:
            await self._verify_agent_ownership(
                memory.agent_id,
                requesting_user
            )

        # Set user_id for isolation
        memory_data = memory.model_dump()
        memory_data["user_id"] = requesting_user

        # Store with user scope
        return await self._store_with_user_scope(memory_data)
```

### 4.2 Project-Based Access

```python
class ProjectMemoryScope:
    """Scope memories to projects."""

    async def get_memories(
        self,
        user_id: str,
        project_id: str | None = None,
        agent_id: str | None = None,
    ) -> list[MemoryResponse]:
        # Build query filter
        filters = {"user_id": user_id}

        if project_id:
            filters["project_id"] = project_id
        if agent_id:
            filters["agent_id"] = agent_id

        return await self._query_with_filters(filters)
```

### 4.3 Encryption Key Management

**Key Hierarchy:**

```
Master Key (KEK)
    │
    ├── User Key 1 (DEK) ──► User 1's memories
    ├── User Key 2 (DEK) ──► User 2's memories
    └── Project Key (DEK) ──► Shared project memories
```

**Implementation Options:**

| Approach                 | Pros              | Cons                    |
| ------------------------ | ----------------- | ----------------------- |
| User-provided password   | No server trust   | User burden             |
| Server-side key storage  | Easy to implement | Single point of failure |
| Hardware Security Module | Maximum security  | Cost, complexity        |
| Key Management Service   | Managed, scalable | Cloud dependency        |

**Recommended: Server-side with env var for MVP**

```python
import os
from cryptography.fernet import Fernet

class KeyManager:
    def __init__(self):
        key = os.environ.get("MEMORY_ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key()
            # Store securely or prompt user
        self.cipher = Fernet(key)

    def encrypt_for_user(self, user_id: str, data: str) -> str:
        # Derive user-specific key
        user_key = self._derive_user_key(user_id)
        return user_key.encrypt(data.encode()).decode()

    def decrypt_for_user(self, user_id: str, data: str) -> str:
        user_key = self._derive_user_key(user_id)
        return user_key.decrypt(data.encode()).decode()
```

---

## 5. Implementation Options

### 5.1 Field-Level Encryption

**Best for**: Selective encryption of sensitive fields

```python
from pydantic import BaseModel, field_validator
from cryptography.fernet import Fernet
import json

class EncryptedMemory:
    """Memory with field-level encryption."""

    ENCRYPTED_FIELDS = ["content", "metadata"]

    def __init__(self, cipher: Fernet):
        self.cipher = cipher

    def encrypt_fields(self, memory_data: dict) -> dict:
        """Encrypt sensitive fields before storage."""
        encrypted = memory_data.copy()

        for field in self.ENCRYPTED_FIELDS:
            if field in encrypted and encrypted[field]:
                if isinstance(encrypted[field], dict):
                    # Encrypt JSON-serialized dict
                    plaintext = json.dumps(encrypted[field])
                    encrypted[field] = self.cipher.encrypt(plaintext.encode())
                else:
                    encrypted[field] = self.cipher.encrypt(
                        str(encrypted[field]).encode()
                    )

        return encrypted

    def decrypt_fields(self, memory_data: dict) -> dict:
        """Decrypt fields after retrieval."""
        decrypted = memory_data.copy()

        for field in self.ENCRYPTED_FIELDS:
            if field in decrypted and decrypted[field]:
                decrypted[field] = self.cipher.decrypt(
                    decrypted[field]
                ).decode()
                if field == "metadata":
                    decrypted[field] = json.loads(decrypted[field])

        return decrypted
```

### 5.2 Full Database Encryption

**Best for**: Maximum security with minimal code changes

- Enable BitLocker/FileVault on storage drives
- Use encrypted container (LUKS on Linux)
- Qdrant data files automatically protected

### 5.3 Application-Level Encryption

**Best for**: Multi-tenant SaaS deployments

```python
class EncryptedVectorStore:
    """Vector store with application-level encryption."""

    def __init__(self, user_id: str, master_key: bytes):
        self.user_id = user_id
        self.cipher = self._derive_cipher(master_key, user_id)
        self.raw_store = QdrantStorage(...)

    def write(self, vectors, payloads):
        # Encrypt content before storing
        encrypted_payloads = []
        for payload in payloads:
            encrypted = payload.copy()
            if "content" in encrypted:
                encrypted["content"] = self.cipher.encrypt(
                    encrypted["content"]
                )
            encrypted_payloads.append(encrypted)

        self.raw_store.write(vectors, encrypted_payloads)

    def query(self, query_vector, **kwargs):
        results = self.raw_store.query(query_vector, **kwargs)

        # Decrypt results
        for result in results:
            if "content" in result.get("payload", {}):
                result["payload"]["content"] = self.cipher.decrypt(
                    result["payload"]["content"]
                )

        return results
```

### 5.4 Trade-offs Matrix

| Approach             | Search  | Performance | Security  | Implementation |
| -------------------- | ------- | ----------- | --------- | -------------- |
| Full-disk            | Full    | 100%        | Medium    | Easy           |
| Field encryption     | Full\*  | 90%         | High      | Medium         |
| App-level encryption | Full\*  | 85%         | Very High | Hard           |
| Encrypted vectors    | Limited | 70%         | Very High | Hard           |

\*Requires decryption of all results post-query

---

## 6. Recommendations

### Priority 1: Immediate (MVP)

1. **Enable TLS** in production Qdrant configuration
2. **Add API key authentication** to memory endpoints
3. **Implement user_id isolation** in memory storage
4. **Add basic PII detection** for sensitive data warnings

### Priority 2: Short-Term

1. **Field-level encryption** for high-sensitivity memories
2. **Audit logging** for memory access
3. **Data retention policies** with auto-expiration
4. **User consent tracking** for compliance

### Priority 3: Long-Term

1. **HSM integration** for key management
2. **Searchable encryption** for privacy-preserving search
3. **Multi-region replication** with encryption
4. **HIPAA/GDPR compliance** certifications

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Eigent Backend                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Auth      │  │   PII       │  │  Encryption │    │
│  │   Service   │  │   Detector  │  │   Service   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│                    Memory Service                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  User Isolation Layer (user_id scoping)         │   │
│  │  + Field Encryption (Fernet)                    │   │
│  │  + Audit Logging                                │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                    Qdrant Storage                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  TLS Enabled + API Key Auth                     │   │
│  │  + OS-level Full-Disk Encryption                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 7. References

- [Qdrant Security Documentation](https://qdrant.tech/documentation/guides/security)
- [Qdrant API Key Authentication](https://qdrant.tech/documentation/guides/security_q=jwt)
- [Python Cryptography Library](https://cryptography.io/)
- [Fernet Symmetric Encryption](https://cryptography.io/en/latest/hazmat/primitives/symmetric/#cryptography.fernet)

---

_Document Version: 1.0_
_Last Updated: 2026-03-08_
_Author: Security Research_

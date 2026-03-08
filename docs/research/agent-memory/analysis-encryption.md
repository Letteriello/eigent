# Encryption Analysis - Memory Service

**Analysis Date:** 2026-03-08
**Author:** Backend Developer Agent

---

## 1. Current Security Analysis

### 1.1 What is Currently Stored (Plaintext)

The `memory_service.py` stores the following data without any encryption:

| Field         | Type        | Sensitivity                      | Stored In     |
| ------------- | ----------- | -------------------------------- | ------------- |
| `content`     | str         | **HIGH** - actual memory content | Qdrant + dict |
| `memory_type` | enum        | LOW - classification only        | Qdrant + dict |
| `metadata`    | dict        | **MEDIUM-HIGH** - user-defined   | Qdrant + dict |
| `agent_id`    | str \| None | LOW - reference                  | Qdrant + dict |
| `session_id`  | str \| None | LOW - reference                  | Qdrant + dict |
| `importance`  | float       | LOW - score                      | Qdrant + dict |
| `created_at`  | datetime    | LOW - timestamp                  | Qdrant + dict |
| `updated_at`  | datetime    | LOW - timestamp                  | Qdrant + dict |

### 1.2 Storage Locations

1. **In-Memory Dict** (`self._memories`):
   - Stores plaintext in Python process memory
   - Lost on restart
   - Vulnerable to memory dumps

2. **Qdrant Vector Store** (`~/.eigent/memory_storage`):
   - Persisted to filesystem
   - **No encryption at rest** - files readable if disk stolen
   - No API key authentication configured

### 1.3 Current Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│                    Attack Surface                            │
├─────────────────────────────────────────────────────────────┤
│  Local Access:     Read ~/.eigent/memory_storage/*         │
│  Memory Dump:       Read Python process memory              │
│  Network:           Qdrant port (6333) unauthenticated      │
│  Application:       Any user can read/write any memory      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Gaps Identified

### 2.1 Critical Gaps

| Gap                 | Severity     | Impact                                            | Research Reference    |
| ------------------- | ------------ | ------------------------------------------------- | --------------------- |
| No field encryption | **CRITICAL** | `content` and `metadata` exposed in plaintext     | Section 2.2, Option B |
| No user isolation   | **CRITICAL** | No `user_id` field - anyone can access any memory | Section 4.1           |
| No key management   | **CRITICAL** | No encryption keys exist                          | Section 4.3           |

### 2.2 High Priority Gaps

| Gap                           | Severity | Impact                                       |
| ----------------------------- | -------- | -------------------------------------------- |
| No PII detection              | HIGH     | Sensitive data stored without classification |
| No API authentication         | HIGH     | Memory endpoints unprotected                 |
| No sensitivity classification | HIGH     | Can't differentiate encryption needs         |

### 2.3 Medium Priority Gaps

| Gap               | Severity | Impact             |
| ----------------- | -------- | ------------------ |
| No audit logging  | MEDIUM   | No accountability  |
| No data retention | MEDIUM   | Indefinite storage |

---

## 3. Implementation Approach

### 3.1 Recommended: Field-Level Encryption (Hybrid)

Based on the research document (Section 2.2, Option C), I recommend **field-level encryption with sensitivity classification**:

```
┌─────────────────────────────────────────────────────────────┐
│                  Encryption Strategy                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Sensitivity: LOW     →  plaintext (memory_type, etc.)    │
│  Sensitivity: MEDIUM →  encrypted content                   │
│  Sensitivity: HIGH   →  encrypted content + metadata       │
│  Sensitivity: CRITICAL→ encrypted + audit logged            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Why This Approach?

| Factor         | Decision                              | Rationale                                        |
| -------------- | ------------------------------------- | ------------------------------------------------ |
| **Search**     | Keep vectors in plaintext             | Full semantic search capability preserved        |
| **Encryption** | Encrypt `content` and `metadata` only | Protects sensitive data, minimal performance hit |
| **Keys**       | Master key + user derivation          | Per-user isolation without managing N keys       |
| **PII**        | Optional detection layer              | Classifies before encryption                     |

### 3.3 Encryption Method: Fernet (AES-128-CBC + HMAC)

From the research document - Fernet is:

- Built into Python's `cryptography` library
- Authenticated encryption (AEAD)
- Key derivation from master key
- No native Qdrant encryption needed

---

## 4. Code Changes Needed

### 4.1 New Files to Create

| File                                        | Purpose                                    |
| ------------------------------------------- | ------------------------------------------ |
| `backend/app/service/encryption_service.py` | Key management + encrypt/decrypt           |
| `backend/app/service/pii_detector.py`       | PII detection + sensitivity classification |

### 4.2 Modifications to `memory_service.py`

#### 4.2.1 Add Encryption Service Dependency

```python
# Add to imports
from cryptography.fernet import Fernet
import hashlib
import base64

# Add to __init__
self._encryption_key: bytes | None = None

def _get_encryption_key(self) -> bytes:
    """Get or generate encryption key."""
    if self._encryption_key is None:
        key = os.environ.get("MEMORY_ENCRYPTION_KEY")
        if key:
            self._encryption_key = key.encode() if isinstance(key, str) else key
        else:
            self._encryption_key = Fernet.generate_key()
            logger.warning("No MEMORY_ENCRYPTION_KEY set, generated temporary key")
    return self._encryption_key

def _encrypt(self, data: str) -> str:
    """Encrypt sensitive field."""
    key = self._get_encryption_key()
    return Fernet(key).encrypt(data.encode()).decode()

def _decrypt(self, data: str) -> str:
    """Decrypt sensitive field."""
    key = self._get_encryption_key()
    return Fernet(key).decrypt(data.encode()).decode()
```

#### 4.2.2 Modify `create_memory`

```python
async def create_memory(self, memory: MemoryCreate) -> MemoryResponse:
    # ... existing ID generation ...

    # NEW: Encrypt sensitive fields before storage
    encrypted_content = self._encrypt(memory.content)
    encrypted_metadata = self._encrypt(json.dumps(memory.metadata)) if memory.metadata else None

    memory_data = {
        "id": memory_id,
        "content": encrypted_content,  # Store encrypted
        "content_plaintext": memory.content,  # Keep for search indexing
        "metadata": encrypted_metadata,  # Store encrypted
        # ... rest unchanged ...
    }
```

#### 4.2.3 Modify `get_memory`

```python
async def get_memory(self, memory_id: str) -> MemoryResponse | None:
    # ... existing retrieval logic ...

    # NEW: Decrypt sensitive fields before returning
    if memory_data:
        memory_data["content"] = self._decrypt(memory_data["content"])
        if memory_data.get("metadata"):
            memory_data["metadata"] = json.loads(self._decrypt(memory_data["metadata"]))
```

#### 4.2.4 Modify `search_memories`

```python
async def search_memories(self, search_query: MemorySearchQuery) -> MemorySearchResult:
    # Search uses plaintext content (kept separately for indexing)
    # Results are decrypted after retrieval

    for memory_id in combined:
        memory_data = self._memories.get(memory_id)
        if memory_data:
            # Decrypt for return
            memory_data["content"] = self._decrypt(memory_data["content"])
            if memory_data.get("metadata"):
                memory_data["metadata"] = json.loads(self._decrypt(memory_data["metadata"]))
```

### 4.3 Model Changes (Optional - Keep Backward Compatible)

The encryption should be transparent to the API - store encrypted in DB, decrypt in service layer. No model changes required.

### 4.4 Environment Variables

```bash
# Required for production
MEMORY_ENCRYPTION_KEY=<base64-encoded-32-byte-key>

# Generate with:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 5. Implementation Phases

### Phase 1: Core Encryption (Priority)

1. Create `encryption_service.py` with Fernet encryption/decryption
2. Modify `memory_service.py` to encrypt `content` before storage
3. Modify `memory_service.py` to decrypt on retrieval
4. Keep plaintext for search indexing

### Phase 2: User Isolation (Priority)

1. Add `user_id` to memory storage schema
2. Filter queries by `user_id`
3. Derive user-specific keys from master key

### Phase 3: PII Detection (Optional)

1. Create `pii_detector.py` with regex patterns
2. Auto-classify sensitivity on memory creation
3. Encrypt critical/high sensitivity by default

### Phase 4: Key Management (Future)

1. Support for user-provided encryption keys
2. Key rotation
3. Hardware Security Module integration

---

## 6. Summary

| Aspect              | Current State  | Target State                       |
| ------------------- | -------------- | ---------------------------------- |
| Content encryption  | None           | Fernet field-level                 |
| Metadata encryption | None           | Fernet field-level                 |
| User isolation      | None           | user_id scoping                    |
| Key management      | None           | ENV-based master key               |
| PII detection       | None           | Optional layer                     |
| Search              | Full plaintext | Plaintext index, encrypted storage |

**Estimated Effort:** 2-4 hours for Phase 1 (core encryption)

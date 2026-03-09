# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

from enum import Enum


class Status(str, Enum):
    confirming = "confirming"
    confirmed = "confirmed"
    processing = "processing"
    done = "done"


class MemoryType(str, Enum):
    """Types of memories that agents can store.

    - fact: Factual information (e.g., "user prefers dark mode")
    - preference: User preferences and settings
    - context: Current working context and project info
    - learned: Knowledge learned from interactions
    - session_summary: Summary of a single session's memories
    - consolidated: Consolidated summary from multiple sessions
    - key_facts: Extracted key facts and entities
    """

    fact = "fact"
    preference = "preference"
    context = "context"
    learned = "learned"
    session_summary = "session_summary"
    consolidated = "consolidated"
    key_facts = "key_facts"


class SummaryLevel(str, Enum):
    """Level of summarization for memory summaries.

    - session: Summary of a single session
    - consolidated: Consolidated summary from multiple sessions
    - key_facts: Extracted key facts and entities
    """

    session = "session"
    consolidated = "consolidated"
    key_facts = "key_facts"


class MemoryStatus(str, Enum):
    """Lifecycle status of memories.

    - pending: Memory created but not yet processed
    - new: Newly created, recently added
    - active: Currently active and accessible
    - stale: Not accessed recently, may be archived
    - archived: Archived for long-term storage
    - deleted: Soft-deleted, can be recovered
    """

    pending = "pending"
    new = "new"
    active = "active"
    stale = "stale"
    archived = "archived"
    deleted = "deleted"


class AccessLevel(str, Enum):
    """Access level for multi-agent memory sharing.

    - private: Only the owning agent can access
    - team: All agents in the same project can access
    - global: Any agent can access (cross-project)
    """

    private = "private"
    team = "team"
    global_ = "global"


DEFAULT_SUMMARY_PROMPT = (
    "After completing the task, please generate"
    " a summary of the entire task completion. "
    "The summary must be enclosed in"
    " <summary></summary> tags and include:\n"
    "1. A confirmation of task completion,"
    " referencing the original goal.\n"
    "2. A high-level overview of the work"
    " performed and the final outcome.\n"
    "3. A bulleted list of key results"
    " or accomplishments.\n"
    "Adopt a confident and professional tone."
)

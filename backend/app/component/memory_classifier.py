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

"""Hybrid memory classifier using keywords and LLM fallback."""

import logging
import re
from typing import Any

from app.model.enums import MemoryScope, MemoryType

logger = logging.getLogger("memory_classifier")

GLOBAL_KEYWORDS = {
    "preference": [
        "i prefer",
        "my preference",
        "i like",
        "i don't like",
        "i always",
        "i never",
        "i hate",
        "love",
        "hate",
        "favorite",
        "best",
        "worst",
        "better than",
    ],
    "personal": [
        "my name is",
        "i am",
        "i'm",
        "call me",
        "birthday",
        "born on",
        "age",
        "years old",
        "my birthday",
        "my age",
    ],
    "design": [
        "color scheme",
        "theme",
        "dark mode",
        "light mode",
        "font",
        "typography",
        "spacing",
        "layout",
        "design",
        "aesthetic",
        "style",
        "ui",
        "ux",
    ],
    "workflow": [
        "workflow",
        "process",
        "how i work",
        "my process",
        "when i",
        "before i",
        "after i",
        "first i",
    ],
}

PROJECT_KEYWORDS = {
    "context": [
        "project",
        "repository",
        "repo",
        "codebase",
        "this project",
        "our project",
        "the project",
        "working on",
        "building",
        "developing",
    ],
    "technical": [
        "api",
        "database",
        "frontend",
        "backend",
        "server",
        "client",
        "config",
        "setup",
        "environment",
        "dependencies",
        "packages",
    ],
}

AGENT_KEYWORDS = {
    "agent_specific": [
        "agent",
        "assistant",
        "helper",
        "you should",
        "remember to",
        "don't forget",
        "keep in mind",
        "for this task",
        "when working on this",
    ],
}

LLM_FALLBACK_PROMPT = """Analyze the following text and determine the memory scope.

Text: {content}

Determine if this memory is:
- GLOBAL: User preferences, personal info, design choices that apply across all projects
- PROJECT: Project-specific information, technical details about a particular project
- AGENT: Task-specific information that applies only to the current agent interaction

Respond with only one word: GLOBAL, PROJECT, or AGENT

Also determine the memory type:
- fact: Factual information
- preference: User preferences
- context: Working context
- learned: Learned knowledge

Respond with format: SCOPE|TYPE

Example responses:
- GLOBAL|preference
- PROJECT|context
- AGENT|learned"""


class MemoryClassifier:
    """Hybrid classifier for determining memory scope and type."""

    def __init__(self, llm_provider: Any | None = None):
        """Initialize the classifier.

        Args:
            llm_provider: Optional LLM provider for fallback classification
        """
        self._llm_provider = llm_provider

    def classify(self, content: str) -> tuple[MemoryScope, MemoryType]:
        """Classify memory content to determine scope and type.

        Args:
            content: The text content to classify

        Returns:
            Tuple of (MemoryScope, MemoryType)
        """
        content_lower = content.lower()

        scope = self._detect_scope(content_lower)
        mem_type = self._detect_type(content_lower)

        logger.debug(f"Classified as scope={scope}, type={mem_type}")
        return scope, mem_type

    def _detect_scope(self, content: str) -> MemoryScope:
        """Detect memory scope using keyword matching.

        Args:
            content: Lowercased content

        Returns:
            Detected MemoryScope
        """
        global_score = self._match_keywords(GLOBAL_KEYWORDS, content)
        project_score = self._match_keywords(PROJECT_KEYWORDS, content)
        agent_score = self._match_keywords(AGENT_KEYWORDS, content)

        if global_score > project_score and global_score > agent_score:
            return MemoryScope.global_
        elif project_score > agent_score:
            return MemoryScope.project
        else:
            return MemoryScope.agent

    def _detect_type(self, content: str) -> MemoryType:
        """Detect memory type using keyword matching.

        Args:
            content: Lowercased content

        Returns:
            Detected MemoryType
        """
        preference_patterns = [
            r"prefer",
            r"like",
            r"love",
            r"hate",
            r"favorite",
            r"better",
            r"worse",
            r"always",
            r"never",
        ]
        if any(re.search(p, content) for p in preference_patterns):
            return MemoryType.preference

        context_patterns = [
            r"project",
            r"working on",
            r"building",
            r"codebase",
            r"repository",
            r"setup",
            r"config",
        ]
        if any(re.search(p, content) for p in context_patterns):
            return MemoryType.context

        learned_patterns = [
            r"learned",
            r"found out",
            r"discovered",
            r"figured out",
            r"remember",
            r"keep in mind",
            r"note that",
        ]
        if any(re.search(p, content) for p in learned_patterns):
            return MemoryType.learned

        return MemoryType.fact

    def _match_keywords(
        self, keyword_dict: dict[str, list[str]], content: str
    ) -> float:
        """Calculate match score for keyword categories.

        Args:
            keyword_dict: Dictionary of category -> keywords
            content: Content to match against

        Returns:
            Score (0.0 to 1.0)
        """
        total_matches = 0
        total_keywords = 0

        for keywords in keyword_dict.values():
            total_keywords += len(keywords)
            for keyword in keywords:
                if keyword in content:
                    total_matches += 1

        return total_matches / max(total_keywords, 1)

    async def classify_with_llm(
        self, content: str
    ) -> tuple[MemoryScope, MemoryType]:
        """Classify using LLM as fallback when keyword matching is uncertain.

        Args:
            content: The text content to classify

        Returns:
            Tuple of (MemoryScope, MemoryType)
        """
        if self._llm_provider is None:
            logger.warning("No LLM provider available, using keyword fallback")
            return self.classify(content)

        try:
            prompt = LLM_FALLBACK_PROMPT.format(content=content)
            response = await self._llm_provider.complete(prompt)

            if "|" in response:
                scope_str, type_str = response.strip().split("|")
                scope = MemoryScope(scope_str.lower())
                mem_type = MemoryType(type_str.lower())
                return scope, mem_type
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")

        return self.classify(content)

    def should_save_memory(self, content: str) -> bool:
        """Determine if content should be saved as a memory.

        Args:
            content: The text content to evaluate

        Returns:
            True if should be saved
        """
        content_lower = content.lower()

        save_indicators = [
            "remember",
            "don't forget",
            "keep in mind",
            "my preference",
            "i prefer",
            "i always",
            "important",
            "note that",
            "note:",
            "reminder",
            "for future reference",
        ]

        return any(indicator in content_lower for indicator in save_indicators)


_classifier: MemoryClassifier | None = None


def get_memory_classifier() -> MemoryClassifier:
    """Get the global memory classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = MemoryClassifier()
    return _classifier

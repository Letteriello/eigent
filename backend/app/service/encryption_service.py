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

"""Encryption service for field-level encryption of sensitive memory data."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from app.component.environment import env

logger = logging.getLogger("encryption_service")

# Default encryption key path
DEFAULT_KEY_PATH = "~/.eigent/memory_encryption.key"

# Default sensitive memory types (will be encrypted by default)
DEFAULT_SENSITIVE_TYPES = {"preference", "learned"}


class EncryptionService:
    """Service for encrypting and decrypting sensitive memory fields.

    Uses Fernet (AES-128-CBC + HMAC) for authenticated encryption.
    Stores the encryption key in the user's config directory.
    """

    def __init__(
        self,
        key_path: str | Path | None = None,
        encryption_enabled: bool | None = None,
        sensitive_content_types: set[str] | None = None,
    ):
        """Initialize the encryption service.

        Args:
            key_path: Path to store/load the encryption key.
                     Defaults to ~/.eigent/memory_encryption.key
            encryption_enabled: Whether encryption is enabled.
                              Defaults to MEMORY_ENCRYPTION_ENABLED env var
            sensitive_content_types: Set of memory types that should be encrypted.
                                    Defaults to {"preference", "learned"}
        """
        self._key_path = (
            Path(key_path) if key_path else Path(os.path.expanduser(DEFAULT_KEY_PATH))
        )
        self._fernet: Fernet | None = None

        # Determine if encryption is enabled
        if encryption_enabled is None:
            encryption_enabled = env("MEMORY_ENCRYPTION_ENABLED", "false").lower() == "true"
        self._encryption_enabled = encryption_enabled

        # Set sensitive content types
        self._sensitive_content_types = sensitive_content_types or DEFAULT_SENSITIVE_TYPES

        # Load or generate the encryption key
        if self._encryption_enabled:
            self._load_or_generate_key()

        logger.info(
            f"EncryptionService initialized: enabled={self._encryption_enabled}, "
            f"sensitive_types={self._sensitive_content_types}"
        )

    def _load_or_generate_key(self) -> None:
        """Load existing key or generate a new one."""
        if self._key_path.exists():
            try:
                key = self._key_path.read_bytes()
                self._fernet = Fernet(key)
                logger.info(f"Loaded encryption key from {self._key_path}")
            except Exception as e:
                logger.error(f"Failed to load encryption key: {e}")
                # Generate new key if existing one is corrupted
                self._generate_key()
        else:
            self._generate_key()

    def _generate_key(self) -> None:
        """Generate a new encryption key and save it."""
        self._fernet = Fernet.generate_key()

        # Ensure parent directory exists
        self._key_path.parent.mkdir(parents=True, exist_ok=True)

        # Save key with restricted permissions
        self._key_path.write_bytes(self._fernet)
        self._key_path.chmod(0o600)  # Owner read/write only

        logger.warning(
            f"Generated new encryption key at {self._key_path}. "
            "Keep this key secure - it cannot be recovered if lost!"
        )

    @property
    def is_enabled(self) -> bool:
        """Check if encryption is enabled."""
        return self._encryption_enabled

    @property
    def sensitive_content_types(self) -> set[str]:
        """Get the set of sensitive content types."""
        return self._sensitive_content_types

    def is_sensitive(self, memory_type: str) -> bool:
        """Check if a memory type should be encrypted.

        Args:
            memory_type: The memory type to check

        Returns:
            True if this memory type should be encrypted
        """
        return memory_type in self._sensitive_content_types

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            ValueError: If encryption is not enabled or key is not available
        """
        if not self._encryption_enabled:
            raise ValueError("Encryption is not enabled")

        if self._fernet is None:
            raise ValueError("Encryption key not available")

        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If encryption is not enabled or decryption fails
        """
        if not self._encryption_enabled:
            raise ValueError("Encryption is not enabled")

        if self._fernet is None:
            raise ValueError("Encryption key not available")

        return self._fernet.decrypt(ciphertext.encode()).decode()

    def encrypt_dict(self, data: dict[str, Any]) -> str:
        """Encrypt a dictionary (JSON-serialized).

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        return self.encrypt(json.dumps(data))

    def decrypt_dict(self, ciphertext: str) -> dict[str, Any]:
        """Decrypt a dictionary (JSON-deserialized).

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted dictionary
        """
        return json.loads(self.decrypt(ciphertext))

    def encrypt_if_sensitive(self, content: str, memory_type: str) -> tuple[str, bool]:
        """Encrypt content if the memory type is sensitive.

        Args:
            content: The content to potentially encrypt
            memory_type: The memory type

        Returns:
            Tuple of (processed_content, was_encrypted)
        """
        if self._encryption_enabled and self.is_sensitive(memory_type):
            return self.encrypt(content), True
        return content, False

    def decrypt_if_encrypted(
        self, content: str, is_encrypted: bool
    ) -> str:
        """Decrypt content if it was encrypted.

        Args:
            content: The content to potentially decrypt
            is_encrypted: Whether the content is encrypted

        Returns:
            Decrypted content if is_encrypted, otherwise original content
        """
        if self._encryption_enabled and is_encrypted:
            return self.decrypt(content)
        return content


# Global encryption service instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def init_encryption_service(
    key_path: str | Path | None = None,
    encryption_enabled: bool | None = None,
    sensitive_content_types: set[str] | None = None,
) -> EncryptionService:
    """Initialize the global encryption service.

    Args:
        key_path: Path to store/load the encryption key
        encryption_enabled: Whether encryption is enabled
        sensitive_content_types: Set of memory types to encrypt

    Returns:
        Initialized encryption service
    """
    global _encryption_service
    _encryption_service = EncryptionService(
        key_path=key_path,
        encryption_enabled=encryption_enabled,
        sensitive_content_types=sensitive_content_types,
    )
    return _encryption_service

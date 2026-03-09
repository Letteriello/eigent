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

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from app.component.environment import env

logger = logging.getLogger("encryption_service")

# Default encryption key path
DEFAULT_KEY_PATH = "~/.eigent/memory_encryption.key"

# Default sensitive memory types (will be encrypted by default)
DEFAULT_SENSITIVE_TYPES = {"preference", "learned"}


class EncryptionService:
    """Service for encrypting and decrypting sensitive memory fields.

    Uses AES-256-GCM for authenticated encryption with PBKDF2 key derivation.
    Stores the encryption key in the user's config directory.
    """

    # PBKDF2 parameters - OWASP recommended
    PBKDF2_ITERATIONS = 600000
    SALT_LENGTH = 16
    KEY_LENGTH = 32  # 256 bits for AES-256
    NONCE_LENGTH = 12  # 96 bits for GCM

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
        self._aesgcm: AESGCM | None = None
        self._key_salt: bytes | None = None

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
            f"algorithm=AES-256-GCM, sensitive_types={self._sensitive_content_types}"
        )

    def _load_or_generate_key(self) -> None:
        """Load existing key or generate a new one."""
        if self._key_path.exists():
            try:
                data = self._key_path.read_bytes()
                # Format: salt (16 bytes) + key (32 bytes)
                if len(data) == self.SALT_LENGTH + self.KEY_LENGTH:
                    self._key_salt = data[:self.SALT_LENGTH]
                    key = data[self.SALT_LENGTH:]
                    self._aesgcm = AESGCM(key)
                    logger.info(f"Loaded encryption key from {self._key_path}")
                else:
                    logger.error(f"Invalid key file format, regenerating")
                    self._generate_key()
            except Exception as e:
                logger.error(f"Failed to load encryption key: {e}")
                # Generate new key if existing one is corrupted
                self._generate_key()
        else:
            self._generate_key()

    def _generate_key(self) -> None:
        """Generate a new encryption key and save it."""
        # Generate random salt
        self._key_salt = os.urandom(self.SALT_LENGTH)

        # Generate random password for key derivation
        password = os.urandom(32)

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=self._key_salt,
            iterations=self.PBKDF2_ITERATIONS,
        )
        key = kdf.derive(password)

        # Create AES-GCM cipher
        self._aesgcm = AESGCM(key)

        # Ensure parent directory exists
        self._key_path.parent.mkdir(parents=True, exist_ok=True)

        # Save salt + key with restricted permissions
        key_data = self._key_salt + key
        self._key_path.write_bytes(key_data)
        self._key_path.chmod(0o600)  # Owner read/write only

        # Clear password from memory (best effort)
        del password
        del key

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
            Base64-encoded encrypted string (nonce + ciphertext)

        Raises:
            ValueError: If encryption is not enabled or key is not available
        """
        if not self._encryption_enabled:
            raise ValueError("Encryption is not enabled")

        if self._aesgcm is None:
            raise ValueError("Encryption key not available")

        # Generate random nonce for each encryption
        nonce = os.urandom(self.NONCE_LENGTH)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode(), None)

        # Store nonce + ciphertext together
        result = base64.b64encode(nonce + ciphertext).decode()
        return result

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string (nonce + ciphertext)

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If encryption is not enabled or decryption fails
        """
        if not self._encryption_enabled:
            raise ValueError("Encryption is not enabled")

        if self._aesgcm is None:
            raise ValueError("Encryption key not available")

        try:
            data = base64.b64decode(ciphertext.encode())
            nonce = data[:self.NONCE_LENGTH]
            encrypted = data[self.NONCE_LENGTH:]
            plaintext = self._aesgcm.decrypt(nonce, encrypted, None)
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed") from e

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

"""
Main Security Manager coordinating security functions
"""

import logging
from typing import Dict, Any, Optional
from .encryption import EncryptionManager
from .audit_logger import AuditLogger, audit_logger

logger = logging.getLogger(__name__)


class SecurityManager:
    """Main security manager coordinating encryption, auditing, and other security functions"""

    def __init__(self, encryption_key: Optional[bytes] = None,
                 audit_log_file: str = "security_audit.log"):
        """
        Initialize the security manager

        Args:
            encryption_key: Key for encryption (if None, a new one will be generated)
            audit_log_file: File path for audit logs
        """
        self.encryption_manager = EncryptionManager(encryption_key)
        # Note: We're using the global audit_logger, but we could create a new one
        # if we wanted different configuration
        self.audit_logger = audit_logger
        self.logger = logging.getLogger(__name__)

        # In-memory cache for session tokens, API keys, etc.
        self._secure_storage: Dict[str, Any] = {}

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data

        Args:
            data: String data to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        encrypted = self.encryption_manager.encrypt_string(data)
        self.audit_logger.log_event(
            event_type="encryption",
            action="encrypt_data",
            outcome="success",
            details={"data_length": len(data)}
        )
        return encrypted

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Encrypted string (base64 encoded)

        Returns:
            Decrypted string
        """
        try:
            decrypted = self.encryption_manager.decrypt_string(encrypted_data)
            self.audit_logger.log_event(
                event_type="decryption",
                action="decrypt_data",
                outcome="success",
                details={"data_length": len(decrypted)}
            )
            return decrypted
        except Exception as e:
            self.audit_logger.log_event(
                event_type="decryption",
                action="decrypt_data",
                outcome="failure",
                details={"error": str(e)},
                severity="error"
            )
            raise

    def hash_data(self, data: str) -> str:
        """
        Hash data for secure storage (e.g., passwords)

        Args:
            data: Data to hash

        Returns:
            Hexadecimal hash string
        """
        hash_value = self.encryption_manager.hash_data(data)
        self.audit_logger.log_event(
            event_type="hashing",
            action="hash_data",
            outcome="success",
            details={"data_length": len(data)}
        )
        return hash_value

    def verify_hash(self, data: str, hash_value: str) -> bool:
        """
        Verify that data matches a hash

        Args:
            data: Data to check
            hash_value: Hash to compare against

        Returns:
            True if data matches the hash, False otherwise
        """
        result = self.encryption_manager.verify_hash(data, hash_value)
        self.audit_logger.log_event(
            event_type="hash_verification",
            action="verify_hash",
            outcome="success" if result else "failure",
            details={"data_length": len(data)}
        )
        return result

    def store_secret(self, key: str, value: str):
        """
        Store a secret in secure memory (encrypted)

        Args:
            key: Identifier for the secret
            value: Secret value to store
        """
        encrypted_value = self.encrypt_data(value)
        self._secure_storage[key] = encrypted_value
        self.audit_logger.log_event(
            event_type="secret_storage",
            action="store_secret",
            outcome="success",
            details={"key": key}
        )

    def retrieve_secret(self, key: str) -> Optional[str]:
        """
        Retrieve a secret from secure memory

        Args:
            key: Identifier for the secret

        Returns:
            Decrypted secret value, or None if not found
        """
        encrypted_value = self._secure_storage.get(key)
        if encrypted_value is None:
            self.audit_logger.log_event(
                event_type="secret_retrieval",
                action="retrieve_secret",
                outcome="failure",
                details={"key": key, "reason": "not_found"},
                severity="warning"
            )
            return None

        try:
            decrypted_value = self.decrypt_data(encrypted_value)
            self.audit_logger.log_event(
                event_type="secret_retrieval",
                action="retrieve_secret",
                outcome="success",
                details={"key": key}
            )
            return decrypted_value
        except Exception as e:
            self.audit_logger.log_event(
                event_type="secret_retrieval",
                action="retrieve_secret",
                outcome="failure",
                details={"key": key, "error": str(e)},
                severity="error"
            )
            return None

    def delete_secret(self, key: str) -> bool:
        """
        Remove a secret from secure memory

        Args:
            key: Identifier for the secret

        Returns:
            True if secret was found and deleted, False otherwise
        """
        if key in self._secure_storage:
            del self._secure_storage[key]
            self.audit_logger.log_event(
                event_type="secret_storage",
                action="delete_secret",
                outcome="success",
                details={"key": key}
            )
            return True
        else:
            self.audit_logger.log_event(
                event_type="secret_storage",
                action="delete_secret",
                outcome="failure",
                details={"key": key, "reason": "not_found"},
                severity="warning"
            )
            return False

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token

        Args:
            length: Length of the token in bytes

        Returns:
            URL-safe base64-encoded token
        """
        import secrets
        token = secrets.token_urlsafe(length)
        self.audit_logger.log_event(
            event_type="token_generation",
            action="generate_secure_token",
            outcome="success",
            details={"token_length": length}
            # Note: We don't log the actual token for security reasons
        )
        return token

    def validate_input(self, input_data: str, max_length: int = 1000,
                      allowed_chars: Optional[str] = None) -> bool:
        """
        Validate input to prevent injection attacks

        Args:
            input_data: Input string to validate
            max_length: Maximum allowed length
            allowed_chars: Regex pattern of allowed characters (None for alphanumeric + basic punctuation)

        Returns:
            True if input is valid, False otherwise
        """
        import re

        # Check length
        if len(input_data) > max_length:
            self.audit_logger.log_event(
                event_type="input_validation",
                action="validate_input",
                outcome="failure",
                details={
                    "reason": "length_exceeded",
                    "length": len(input_data),
                    "max_length": max_length
                },
                severity="warning"
            )
            return False

        # Check allowed characters
        if allowed_chars is None:
            # Default to alphanumeric, spaces, and basic punctuation
            pattern = r'^[a-zA-Z0-9\s\-_.@]+$'
        else:
            pattern = f'^[{allowed_chars}]+$'

        if not re.match(pattern, input_data):
            self.audit_logger.log_event(
                event_type="input_validation",
                action="validate_input",
                outcome="failure",
                details={
                    "reason": "invalid_characters",
                    "input_preview": input_data[:50]  # Only log first 50 chars to avoid leaking sensitive data
                },
                severity="warning"
            )
            return False

        self.audit_logger.log_event(
            event_type="input_validation",
            action="validate_input",
            outcome="success",
            details={"length": len(input_data)}
        )
        return True

    def get_security_status(self) -> Dict[str, Any]:
        """
        Get current security status and metrics

        Returns:
            Dictionary with security status information
        """
        # In a real implementation, this would include more detailed metrics
        return {
            "encryption_enabled": True,
            "audit_logging_enabled": True,
            "secrets_stored": len(self._secure_storage),
            "status": "secure"
        }


# Global security manager instance
security_manager = SecurityManager()
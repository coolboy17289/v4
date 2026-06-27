"""
Encryption Utilities for Data Protection
"""

import os
import base64
import hashlib
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize the encryption manager

        Args:
            key: Encryption key (if None, a new key will be generated)
        """
        if key is None:
            key = self.generate_key()
        self.key = key
        self.cipher = Fernet(key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key"""
        return Fernet.generate_key()

    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive an encryption key from a password

        Args:
            password: Password to derive key from
            salt: Salt to use (if None, a random salt will be generated)

        Returns:
            Derived key as bytes
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data

        Args:
            data: Data to encrypt (string or bytes)

        Returns:
            Encrypted data as bytes
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        encrypted_data = self.cipher.encrypt(data)
        return encrypted_data

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt data

        Args:
            encrypted_data: Encrypted data as bytes

        Returns:
            Decrypted data as string
        """
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise

    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string and return as base64-encoded string

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        encrypted_bytes = self.encrypt(plaintext)
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_string(self, encrypted_string: str) -> str:
        """
        Decrypt a base64-encoded encrypted string

        Args:
            encrypted_string: Base64-encoded encrypted string

        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encoded_string.encode('utf-8'))
            return self.decrypt(encrypted_bytes)
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise

    def hash_data(self, data: Union[str, bytes]) -> str:
        """
        Create a SHA-256 hash of data

        Args:
            data: Data to hash

        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        hash_object = hashlib.sha256(data)
        return hash_object.hexdigest()

    def verify_hash(self, data: Union[str, bytes], hash_value: str) -> bool:
        """
        Verify that data matches a hash

        Args:
            data: Data to check
            hash_value: Hash to compare against

        Returns:
            True if data matches the hash, False otherwise
        """
        computed_hash = self.hash_data(data)
        return secrets.compare_digest(computed_hash, hash_value)
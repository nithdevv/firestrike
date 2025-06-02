import hashlib
import os
from typing import Tuple
from nacl.public import PrivateKey, PublicKey, Box
from nacl.utils import random
from base64 import b64encode, b64decode

class CryptoHandler:
    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        # Generate key pair for asymmetric encryption
        private_key = PrivateKey.generate()
        public_key = private_key.public_key
        return bytes(private_key), bytes(public_key)

    @staticmethod
    def anonymous_hash(data: bytes, salt: bytes = None) -> Tuple[bytes, bytes]:
        # Create anonymous data hash using salt and SHA-3
        if salt is None:
            salt = os.urandom(32)
        
        # Use SHA3-256 for hashing
        hasher = hashlib.sha3_256()
        hasher.update(salt)
        hasher.update(data)
        return hasher.digest(), salt

    @staticmethod
    def verify_hash(data: bytes, salt: bytes, expected_hash: bytes) -> bool:
        # Verify data hash
        hasher = hashlib.sha3_256()
        hasher.update(salt)
        hasher.update(data)
        return hasher.digest() == expected_hash

    @staticmethod
    def encrypt_message(message: bytes, 
                       sender_private_key: bytes,
                       recipient_public_key: bytes) -> bytes:
        # Encrypt message for recipient
        sender_box = Box(PrivateKey(sender_private_key),
                        PublicKey(recipient_public_key))
        nonce = random(Box.NONCE_SIZE)
        encrypted = sender_box.encrypt(message, nonce)
        return encrypted

    @staticmethod
    def decrypt_message(encrypted: bytes,
                       recipient_private_key: bytes,
                       sender_public_key: bytes) -> bytes:
        # Decrypt message from sender
        recipient_box = Box(PrivateKey(recipient_private_key),
                          PublicKey(sender_public_key))
        return recipient_box.decrypt(encrypted)

    @staticmethod
    def encode_key(key: bytes) -> str:
        # Encode key to base64 string
        return b64encode(key).decode('utf-8')

    @staticmethod
    def decode_key(key_str: str) -> bytes:
        # Decode key from base64 string
        return b64decode(key_str.encode('utf-8')) 
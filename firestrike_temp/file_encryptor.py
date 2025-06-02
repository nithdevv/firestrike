import os
import hashlib
import base64
import logging
from typing import Tuple, Optional
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey

class EncryptionError(Exception):
    # Base class for encryption errors
    pass

class DecryptionError(Exception):
    # Base class for decryption errors
    pass

class FileEncryptor:
    CHUNK_SIZE = 8192  # 8KB for file reading
    IV_SIZE = 16       # AES IV size
    KEY_SIZE = 32      # 256 bits for AES-256
    
    def __init__(self, log_level: int = logging.INFO):
        # Initialize with logging setup
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
    @staticmethod
    def generate_key() -> bytes:
        # Generate random 256-bit key
        try:
            return os.urandom(FileEncryptor.KEY_SIZE)
        except Exception as e:
            raise EncryptionError(f"Key generation error: {str(e)}")
            
    def calculate_file_hash(self, file_path: str, chunk_size: int = None) -> str:
        # Calculate SHA3-256 hash of file with large file support
        if chunk_size is None:
            chunk_size = self.CHUNK_SIZE
            
        try:
            hasher = hashlib.sha3_256()
            file_size = os.path.getsize(file_path)
            processed = 0
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
                    processed += len(chunk)
                    # Log progress for large files
                    if file_size > 100 * 1024 * 1024:  # 100MB
                        progress = (processed / file_size) * 100
                        self.logger.debug(f"Hashing progress: {progress:.1f}%")
                        
            return hasher.hexdigest()
            
        except (IOError, OSError) as e:
            raise EncryptionError(f"File read error during hashing: {str(e)}")
        except Exception as e:
            raise EncryptionError(f"Hash calculation error: {str(e)}")
            
    def encrypt_file(self, file_path: str, key: bytes, output_path: Optional[str] = None) -> Tuple[bytes, str]:
        # Encrypt file using AES-256-CBC and return IV and encrypted file path
        if len(key) != self.KEY_SIZE:
            raise EncryptionError(f"Invalid key length: {len(key)} bytes (expected {self.KEY_SIZE})")
            
        try:
            # Generate IV
            iv = os.urandom(self.IV_SIZE)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(128).padder()
            
            # If path not specified, create temporary
            if output_path is None:
                file_hash = self.calculate_file_hash(file_path)
                output_path = f"{file_hash}.fire"
                
            # Encrypt file
            file_size = os.path.getsize(file_path)
            processed = 0
            
            with open(file_path, 'rb') as fin, open(output_path, 'wb') as fout:
                # Write IV at start of file
                fout.write(iv)
                
                while chunk := fin.read(self.CHUNK_SIZE):
                    # Add padding and encrypt
                    padded_chunk = padder.update(chunk)
                    encrypted_chunk = encryptor.update(padded_chunk)
                    fout.write(encrypted_chunk)
                    
                    # Track progress
                    processed += len(chunk)
                    if file_size > 100 * 1024 * 1024:  # 100MB
                        progress = (processed / file_size) * 100
                        self.logger.debug(f"Encryption progress: {progress:.1f}%")
                
                # Finalize encryption
                final_padded = padder.finalize()
                final_encrypted = encryptor.update(final_padded) + encryptor.finalize()
                fout.write(final_encrypted)
                
            return iv, output_path
            
        except (IOError, OSError) as e:
            raise EncryptionError(f"File operation error during encryption: {str(e)}")
        except Exception as e:
            raise EncryptionError(f"Encryption error: {str(e)}")
            
    def decrypt_file(self, encrypted_file: str, key: bytes, output_path: Optional[str] = None) -> str:
        # Decrypt file and return path to decrypted file
        if len(key) != self.KEY_SIZE:
            raise DecryptionError(f"Invalid key length: {len(key)} bytes (expected {self.KEY_SIZE})")
            
        try:
            # If path not specified, create temporary
            if output_path is None:
                output_path = encrypted_file.replace('.fire', '_decrypted')
                
            with open(encrypted_file, 'rb') as f:
                # Read IV from start of file
                iv = f.read(self.IV_SIZE)
                if len(iv) != self.IV_SIZE:
                    raise DecryptionError("Invalid encrypted file format")
                    
                # Create decryptor
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                unpadder = padding.PKCS7(128).unpadder()
                
                # Decrypt file
                file_size = os.path.getsize(encrypted_file) - self.IV_SIZE
                processed = 0
                
                with open(output_path, 'wb') as fout:
                    while chunk := f.read(self.CHUNK_SIZE):
                        decrypted_chunk = decryptor.update(chunk)
                        try:
                            unpadded_chunk = unpadder.update(decrypted_chunk)
                            fout.write(unpadded_chunk)
                        except ValueError:
                            # If this is last block, handle it separately
                            if not f.peek(1):
                                final_chunk = unpadder.update(decrypted_chunk) + unpadder.finalize()
                                fout.write(final_chunk)
                            else:
                                raise
                                
                        processed += len(chunk)
                        if file_size > 100 * 1024 * 1024:  # 100MB
                            progress = (processed / file_size) * 100
                            self.logger.debug(f"Decryption progress: {progress:.1f}%")
                            
            return output_path
            
        except (IOError, OSError) as e:
            raise DecryptionError(f"File operation error during decryption: {str(e)}")
        except InvalidKey:
            raise DecryptionError("Invalid decryption key")
        except Exception as e:
            raise DecryptionError(f"Decryption error: {str(e)}")
            
    @staticmethod
    def generate_magnet_link(file_hash: str, key: bytes) -> str:
        # Generate magnet link in firestrike format
        try:
            key_b64 = base64.b64encode(key).decode('utf-8')
            return f"firestrike://{file_hash}#{key_b64}"
        except Exception as e:
            raise EncryptionError(f"Magnet link generation error: {str(e)}")
            
    @staticmethod
    def parse_magnet_link(magnet_link: str) -> Tuple[str, bytes]:
        # Parse magnet link into hash and key
        try:
            if not magnet_link.startswith("firestrike://"):
                raise ValueError("Invalid magnet link format")
                
            parts = magnet_link.split("://")[1].split("#")
            if len(parts) != 2:
                raise ValueError("Invalid magnet link format")
                
            file_hash, key_b64 = parts
            key = base64.b64decode(key_b64)
            
            if len(file_hash) != 64:  # SHA3-256 in hex
                raise ValueError("Invalid hash length")
            if len(key) != FileEncryptor.KEY_SIZE:
                raise ValueError("Invalid key length")
                
            return file_hash, key
            
        except Exception as e:
            raise ValueError(f"Magnet link parsing error: {str(e)}")
            
def encrypt_and_generate_link(file_path: str) -> str:
    # Convenience function to encrypt file and generate magnet link
    encryptor = FileEncryptor()
    
    # Generate key and calculate hash
    key = encryptor.generate_key()
    file_hash = encryptor.calculate_file_hash(file_path)
    
    # Encrypt file
    _, encrypted_path = encryptor.encrypt_file(file_path, key)
    
    # Generate magnet link
    return encryptor.generate_magnet_link(file_hash, key)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python file_encryptor.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: file {file_path} not found")
        sys.exit(1)
        
    try:
        magnet_link = encrypt_and_generate_link(file_path)
        print(f"\nFile successfully encrypted!")
        print(f"Magnet link: {magnet_link}")
        print(f"Encrypted file saved as: {os.path.basename(file_path)}.fire")
    except Exception as e:
        print(f"Error encrypting file: {e}")
        sys.exit(1) 
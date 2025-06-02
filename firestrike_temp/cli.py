import argparse
import asyncio
import os
import base64
import logging
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path
from .file_encryptor import FileEncryptor, encrypt_and_generate_link
from .hidden_service import FireStrikeNode, NetworkError
from .crypto import CryptoHandler
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# Version of the package
__version__ = "0.1.0"

class CLIError(Exception):
    # Base class for CLI errors
    pass

class FireStrikeCLI:
    def __init__(self, log_level: int = logging.INFO):
        # Initialize CLI
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Formatter for console output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console_handler)
        
        # Initialize components
        self.encryptor = FileEncryptor(log_level=log_level)
        self.node: Optional[FireStrikeNode] = None
        
    async def init_node(self, port: int = 8789) -> None:
        # Initialize and start node
        if self.node is not None:
            raise CLIError("Node is already running")
            
        try:
            self.node = FireStrikeNode(port=port)
            await self.node.start()
        except Exception as e:
            raise CLIError(f"Failed to start node: {str(e)}")
            
    async def upload_file(self, file_path: str, temp: bool = False) -> str:
        # Upload file to network
        try:
            # Check file existence
            if not os.path.exists(file_path):
                raise CLIError(f"File not found: {file_path}")
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise CLIError("File is empty")
                
            self.logger.info(f"Uploading file {file_path} ({file_size} bytes)")
            
            # Encrypt file and get magnet link
            magnet = encrypt_and_generate_link(file_path)
            file_hash, key = self.encryptor.parse_magnet_link(magnet)
            
            # If node not running, start it
            if self.node is None:
                await self.init_node()
                
            # Read encrypted file
            encrypted_path = f"{file_hash}.fire"
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
                
            # Send file to network
            message = {
                'type': 'store',
                'hash': file_hash,
                'data': encrypted_data.hex(),
                'sender': self.node.onion_address
            }
            
            # Send file to multiple peers for reliability
            peers = await self.get_peers()
            success_count = 0
            
            for peer in peers[:3]:  # Send to first three peers
                response = await self.node.connect_to_peer(peer['address'], message)
                if response and response.get('status') == 'ok':
                    success_count += 1
                    
            if success_count == 0:
                self.logger.warning("Failed to send file to any peers")
            else:
                self.logger.info(f"File successfully sent to {success_count} peers")
                
            # Delete temporary files
            if temp:
                try:
                    os.unlink(file_path)
                    os.unlink(encrypted_path)
                except OSError as e:
                    self.logger.error(f"Failed to delete temporary files: {str(e)}")
                    
            return magnet
            
        except Exception as e:
            raise CLIError(f"Error uploading file: {str(e)}")
            
    async def download_file(self, magnet: str, output_path: Optional[str] = None,
                          temp: bool = False) -> str:
        # Download file from network
        try:
            # Parse magnet link
            file_hash, key = self.encryptor.parse_magnet_link(magnet)
            
            # If node not running, start it
            if self.node is None:
                await self.init_node()
                
            # Search file in network
            message = {
                'type': 'find',
                'hash': file_hash,
                'sender': self.node.onion_address
            }
            
            # Get peer list
            peers = await self.get_peers()
            if not peers:
                raise CLIError("No active peers found")
                
            # Try to download file
            encrypted_data = None
            
            for peer in peers:
                response = await self.node.connect_to_peer(peer['address'], message)
                if response and response.get('status') == 'found':
                    encrypted_data = bytes.fromhex(response['data'])
                    break
                    
            if not encrypted_data:
                raise CLIError("File not found in network")
                
            # Save encrypted file
            encrypted_path = f"{file_hash}.fire"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Decrypt file
            if output_path is None:
                output_path = f"downloaded_{os.path.basename(file_hash)}"
                
            decrypted_path = self.encryptor.decrypt_file(encrypted_path, key, output_path)
            
            # Delete temporary files
            if temp:
                try:
                    os.unlink(encrypted_path)
                except OSError as e:
                    self.logger.error(f"Failed to delete temporary file: {str(e)}")
                    
            self.logger.info(f"File successfully downloaded: {decrypted_path}")
            return decrypted_path
            
        except Exception as e:
            raise CLIError(f"Error downloading file: {str(e)}")
            
    async def get_peers(self) -> List[Dict[str, Any]]:
        # Get list of active peers
        if self.node is None:
            raise CLIError("Node is not running")
            
        message = {
            'type': 'get_peers',
            'sender': self.node.onion_address
        }
        
        # Get peer list from current node
        response = await self.node.process_message(message)
        if response.get('status') != 'ok':
            return []
            
        return response.get('peers', [])
        
    async def cleanup(self) -> None:
        # Clean up resources
        if self.node:
            await self.node.stop()
            
def create_parser() -> argparse.ArgumentParser:
    # Create command line argument parser
    parser = argparse.ArgumentParser(
        description="FireStrike - Decentralized anonymous file sharing network"
    )
    
    # Add version argument
    parser.add_argument('--version', action='version',
                       version=f'FireStrike {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload file')
    upload_parser.add_argument('file', help='Path to file')
    upload_parser.add_argument('--temp', action='store_true',
                             help='Delete file after upload')
    upload_parser.add_argument('--port', type=int, default=8789,
                             help='Port to start node on')
                             
    # Download command
    download_parser = subparsers.add_parser('download', help='Download file')
    download_parser.add_argument('magnet', help='Magnet link')
    download_parser.add_argument('--output', help='Path to save file')
    download_parser.add_argument('--temp', action='store_true',
                               help='Delete file after completion')
    download_parser.add_argument('--port', type=int, default=8789,
                               help='Port to start node on')
                               
    # Peers command
    peers_parser = subparsers.add_parser('peers', help='Show peer list')
    peers_parser.add_argument('--port', type=int, default=8789,
                            help='Port to start node on')
                            
    return parser

def main_cli() -> None:
    """Entry point for the CLI"""
    asyncio.run(main())

if __name__ == "__main__":
    main_cli() 
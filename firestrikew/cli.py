import argparse
import asyncio
import os
import base64
import logging
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path
from .file_encryptor import FileEncryptor, encrypt_and_generate_link
from .dht_node import DHTNode
from .crypto import CryptoHandler

# Version of the package
__version__ = "0.1.0"

class CLIError(Exception):
    """Base class for CLI errors"""
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
        self.node: Optional[DHTNode] = None
        
    async def init_node(self, port: int = 8789) -> None:
        """Initialize and start node"""
        if self.node is not None:
            raise CLIError("Node is already running")
            
        try:
            self.node = DHTNode(port=port)
            await self.node.start()
        except Exception as e:
            raise CLIError(f"Failed to start node: {str(e)}")
            
    async def upload_file(self, file_path: str, temp: bool = False) -> str:
        """Upload file to network"""
        try:
            # Check file existence
            if not os.path.exists(file_path):
                raise CLIError(f"File not found: {file_path}")
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise CLIError("File is empty")
                
            self.logger.info(f"Uploading file {file_path} ({file_size} bytes)")
            
            # If node not running, start it
            if self.node is None:
                await self.init_node()
                
            # Read and hash file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            file_hash = await self.node.store_data(file_data)
            
            # Delete temporary files if requested
            if temp:
                try:
                    os.unlink(file_path)
                except OSError as e:
                    self.logger.error(f"Failed to delete temporary file: {str(e)}")
                    
            return file_hash
            
        except Exception as e:
            raise CLIError(f"Error uploading file: {str(e)}")
            
    async def download_file(self, file_hash: str, output_path: Optional[str] = None,
                          temp: bool = False) -> str:
        """Download file from network"""
        try:
            # If node not running, start it
            if self.node is None:
                await self.init_node()
                
            # Get file data
            file_data = await self.node.get_data(file_hash)
            if not file_data:
                raise CLIError("File not found in network")
                
            # Save file
            if output_path is None:
                output_path = f"downloaded_{os.path.basename(file_hash)}"
                
            with open(output_path, 'wb') as f:
                f.write(file_data)
                
            self.logger.info(f"File successfully downloaded: {output_path}")
            return output_path
            
        except Exception as e:
            raise CLIError(f"Error downloading file: {str(e)}")
            
    async def get_peers(self) -> List[Dict[str, Any]]:
        """Get list of active peers"""
        if self.node is None:
            raise CLIError("Node is not running")
            
        peers = list(self.node.peers)
        return [{"address": peer} for peer in peers]
        
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.node:
            await self.node.stop()
            
def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="FireStrike - Decentralized P2P file sharing network"
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
    download_parser.add_argument('hash', help='File hash')
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

async def main() -> None:
    """Main entry point for the CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle version and help without initializing CLI
    if not args.command:
        parser.print_help()
        return
        
    cli = FireStrikeCLI()
    
    try:
        if args.command == 'upload':
            file_hash = await cli.upload_file(args.file, args.temp)
            print(f"File hash: {file_hash}")
            
        elif args.command == 'download':
            output_path = await cli.download_file(args.hash, args.output, args.temp)
            print(f"File downloaded: {output_path}")
            
        elif args.command == 'peers':
            await cli.init_node(args.port)
            peers = await cli.get_peers()
            if peers:
                print("\nActive peers list:")
                for peer in peers:
                    print(f"- {peer['address']}")
            else:
                print("No active peers found")
                
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        await cli.cleanup()

def main_cli() -> None:
    """Entry point for the CLI"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main_cli() 
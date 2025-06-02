import asyncio
import logging
import json
from typing import Dict, List, Optional, Set, Tuple
from .network_connection import NetworkConnection
from .crypto import CryptoHandler
from .storage import Storage
import socket

class DHTNode:
    def __init__(self, port: int = 8788, storage_dir: str = None):
        self.port = port
        self.network = NetworkConnection(port)
        self.crypto = CryptoHandler()
        self.storage = Storage(storage_dir)
        
        # Node keys
        self.private_key: Optional[bytes] = None
        self.public_key: Optional[bytes] = None
        
        # Node address
        self.address: Optional[str] = None
        
        # Routing table: {node_id: (address, public_key)}
        self.routing_table: Dict[str, Tuple[str, bytes]] = {}
        
        # Known peers
        self.peers: Set[str] = set()
        
    async def start(self) -> None:
        """Start DHT node"""
        # Generate keys
        self.private_key, self.public_key = self.crypto.generate_keypair()
        
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            self.address = s.getsockname()[0]
        finally:
            s.close()
        
        # Start server
        await self.network.start_server()
        
        logging.info(f"DHT node started on {self.address}:{self.port}")
        
    async def stop(self) -> None:
        """Stop DHT node"""
        await self.network.stop()
        logging.info("DHT node stopped")
        
    async def connect_to_peer(self, host: str, port: int) -> None:
        """Connect to a peer"""
        try:
            reader, writer = await self.network.connect_to_peer(host, port)
            self.peers.add(f"{host}:{port}")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logging.error(f"Failed to connect to peer {host}:{port}: {str(e)}")
            
    async def store_data(self, data: bytes) -> str:
        """Store data and return its hash"""
        data_hash, salt = self.crypto.hash_data(data)
        self.storage.store_data(data_hash, data, salt)
        return data_hash
        
    async def get_data(self, data_hash: str) -> Optional[bytes]:
        """Retrieve data by hash"""
        result = self.storage.get_data(data_hash)
        if result:
            data, _ = result
            return data
        return None 
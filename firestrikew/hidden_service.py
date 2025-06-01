import asyncio
import logging
import json
import base64
import socket
import time
from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass, asdict
import stem.process
from stem.control import Controller
import socks
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

@dataclass
class PeerInfo:
    # Peer information in the network
    onion_address: str
    public_key: bytes
    last_seen: float
    shared_files: Set[str]
    
class NetworkError(Exception):
    # Base class for network errors
    pass

class TorError(NetworkError):
    # TOR-related errors
    pass

class PeerError(NetworkError):
    # Peer interaction errors
    pass

class FireStrikeNode:
    # Node configuration constants
    PEER_TIMEOUT = 300  # 5 minutes peer timeout
    MAX_PEERS = 50      # Maximum number of peers
    PING_INTERVAL = 60  # Peer check interval
    CHUNK_SIZE = 8192   # File transfer chunk size
    
    def __init__(self, port: int = 8789, 
                 tor_port: int = 9050, 
                 control_port: int = 9051,
                 max_peers: int = None,
                 log_level: int = logging.ERROR):
        # Initialize FireStrike node
        self.port = port
        self.tor_port = tor_port
        self.control_port = control_port
        self.max_peers = max_peers or self.MAX_PEERS
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Node state
        self.onion_address: Optional[str] = None
        self.tor_process = None
        self.controller = None
        self.server = None
        self.is_running = False
        
        # Peer information
        self.peers: Dict[str, PeerInfo] = {}
        self.data_store: Dict[str, bytes] = {}
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        
    async def start_tor(self) -> None:
        # Start TOR process and create hidden service
        try:
            # Check if TOR is already running
            if self.tor_process:
                raise TorError("TOR is already running")
                
            # TOR configuration
            tor_config = {
                'SocksPort': str(self.tor_port),
                'ControlPort': str(self.control_port),
                'Log': 'err stderr',
                'DataDirectory': f'tor_data_{self.port}',
                'CircuitBuildTimeout': '10',
                'NumEntryGuards': '4'
            }
            
            # Start TOR
            self.tor_process = stem.process.launch_tor_with_config(
                config = tor_config,
                init_msg_handler = lambda msg: self.logger.debug(f"Tor: {msg}")
            )
            
            # Setup controller
            self.controller = Controller.from_port(port=self.control_port)
            self.controller.authenticate()
            
            # Create hidden service
            result = self.controller.create_hidden_service(
                port = self.port,
                target_port = self.port,
                await_publication = True
            )
            self.onion_address = result.hostname
            
            # Setup SOCKS5 proxy
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            socket.socket = socks.socksocket
            
            self.logger.info(f"Hidden service started at {self.onion_address}")
            
        except Exception as e:
            self.logger.error(f"Error starting TOR: {str(e)}")
            await self.cleanup()
            raise TorError(f"Failed to start TOR: {str(e)}")
            
    async def handle_connection(self, reader: asyncio.StreamReader, 
                              writer: asyncio.StreamWriter) -> None:
        # Handle incoming connections
        try:
            # Read data
            data = await reader.read(self.CHUNK_SIZE)
            if not data:
                return
                
            # Parse message
            message = json.loads(data.decode())
            
            # Process message
            response = await self.process_message(message)
            
            # Send response
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except json.JSONDecodeError:
            self.logger.error("Received invalid data")
        except Exception as e:
            self.logger.error(f"Error handling connection: {str(e)}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Process incoming messages
        try:
            message_type = message.get('type')
            
            if message_type == 'ping':
                return await self.handle_ping(message)
            elif message_type == 'store':
                return await self.handle_store(message)
            elif message_type == 'find':
                return await self.handle_find(message)
            elif message_type == 'get_peers':
                return await self.handle_get_peers(message)
            else:
                return {
                    'type': 'error',
                    'status': 'unknown_message_type'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                'type': 'error',
                'status': 'internal_error',
                'message': str(e)
            }
            
    async def handle_ping(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Handle ping messages
        sender = message.get('sender')
        if not sender:
            raise PeerError("Missing sender address")
            
        # Update peer information
        if sender in self.peers:
            self.peers[sender].last_seen = time.time()
        elif len(self.peers) < self.max_peers:
            self.peers[sender] = PeerInfo(
                onion_address=sender,
                public_key=message.get('public_key', b''),
                last_seen=time.time(),
                shared_files=set()
            )
            
        return {
            'type': 'pong',
            'status': 'ok',
            'address': self.onion_address
        }
        
    async def handle_store(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Handle data storage requests
        file_hash = message.get('hash')
        data_b64 = message.get('data')
        
        if not file_hash or not data_b64:
            raise ValueError("Missing file hash or data")
            
        # Decode and store data
        data = base64.b64decode(data_b64)
        self.data_store[file_hash] = data
        
        # Update available files information
        sender = message.get('sender')
        if sender in self.peers:
            self.peers[sender].shared_files.add(file_hash)
            
        return {
            'type': 'store_response',
            'status': 'ok',
            'hash': file_hash
        }
        
    async def handle_find(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Handle data search requests
        file_hash = message.get('hash')
        if not file_hash:
            raise ValueError("Missing file hash")
            
        # Search data locally
        data = self.data_store.get(file_hash)
        if data:
            return {
                'type': 'find_response',
                'status': 'found',
                'hash': file_hash,
                'data': base64.b64encode(data).decode()
            }
            
        # If data not found, return list of peers that have the file
        peers_with_file = [
            peer.onion_address for peer in self.peers.values()
            if file_hash in peer.shared_files
        ]
        
        return {
            'type': 'find_response',
            'status': 'not_found',
            'hash': file_hash,
            'peers': peers_with_file
        }
        
    async def handle_get_peers(self, message: Dict[str, Any]) -> Dict[str, Any]:
        # Return list of known peers
        # Remove stale entries
        await self.cleanup_peers()
        
        # Form list of active peers
        active_peers = [
            {
                'address': peer.onion_address,
                'public_key': base64.b64encode(peer.public_key).decode(),
                'shared_files': list(peer.shared_files)
            }
            for peer in self.peers.values()
        ]
        
        return {
            'type': 'peers_response',
            'status': 'ok',
            'peers': active_peers
        }
        
    async def connect_to_peer(self, peer_onion: str, 
                            message: Dict[str, Any],
                            timeout: float = 30) -> Optional[Dict[str, Any]]:
        # Connect to another node via TOR
        try:
            # Establish connection with timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    peer_onion,
                    self.port,
                    ssl=False
                ),
                timeout=timeout
            )
            
            try:
                # Send message
                writer.write(json.dumps(message).encode())
                await writer.drain()
                
                # Wait for response
                response = await asyncio.wait_for(
                    reader.read(self.CHUNK_SIZE),
                    timeout=timeout
                )
                
                return json.loads(response.decode())
                
            finally:
                writer.close()
                await writer.wait_closed()
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout connecting to {peer_onion}")
            return None
        except Exception as e:
            self.logger.error(f"Error connecting to {peer_onion}: {str(e)}")
            return None
            
    async def cleanup_peers(self) -> None:
        # Remove inactive peers
        current_time = time.time()
        inactive = [
            addr for addr, peer in self.peers.items()
            if current_time - peer.last_seen > self.PEER_TIMEOUT
        ]
        for addr in inactive:
            del self.peers[addr]
            
    async def ping_peers(self) -> None:
        # Periodically check peer availability
        while self.is_running:
            try:
                # Form ping message
                message = {
                    'type': 'ping',
                    'sender': self.onion_address
                }
                
                # Send ping to all known peers
                for peer_address in list(self.peers.keys()):
                    response = await self.connect_to_peer(peer_address, message)
                    if not response or response.get('status') != 'ok':
                        # If peer is unavailable, remove it
                        self.peers.pop(peer_address, None)
                        
                # Remove inactive peers
                await self.cleanup_peers()
                
            except Exception as e:
                self.logger.error(f"Error checking peers: {str(e)}")
                
            await asyncio.sleep(self.PING_INTERVAL)
            
    async def start(self) -> None:
        # Start the node
        try:
            # Start TOR
            await self.start_tor()
            
            # Start server
            self.server = await asyncio.start_server(
                self.handle_connection,
                '127.0.0.1',
                self.port
            )
            
            self.is_running = True
            
            # Start background tasks
            ping_task = asyncio.create_task(self.ping_peers())
            self.background_tasks.append(ping_task)
            
            # Run server
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            self.logger.error(f"Error starting node: {str(e)}")
            await self.cleanup()
            raise
            
    async def cleanup(self) -> None:
        # Clean up resources
        self.is_running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        # Stop TOR
        if self.controller:
            self.controller.close()
        if self.tor_process:
            self.tor_process.kill()
            
        self.logger.info("Node stopped")
        
    async def stop(self) -> None:
        # Stop the node
        await self.cleanup()

# Usage example
async def example_usage():
    # Start first node
    node1 = FireStrikeNode(port=8789)
    await node1.start_tor()
    print(f"Node 1 started at: {node1.onion_address}")
    
    # Start second node
    node2 = FireStrikeNode(port=8790)
    await node2.start_tor()
    print(f"Node 2 started at: {node2.onion_address}")
    
    # Send ping from node1 to node2
    message = {
        'type': 'ping',
        'sender': node1.onion_address
    }
    
    response = await node1.connect_to_peer(node2.onion_address, message)
    print(f"Response from node 2: {response}")
    
    # Stop nodes
    await node1.stop()
    await node2.stop()

if __name__ == "__main__":
    try:
        asyncio.run(example_usage())
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1) 
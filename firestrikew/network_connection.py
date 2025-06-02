import asyncio
import logging
import socket
from typing import Optional, Tuple

class NetworkConnection:
    def __init__(self, port: int = 8789):
        self.port = port
        self.server = None
        self.logger = logging.getLogger(__name__)
        
    async def start_server(self) -> None:
        """Start TCP server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_connection,
                '0.0.0.0',  # Listen on all interfaces
                self.port
            )
            
            addr = self.server.sockets[0].getsockname()
            self.logger.info(f"Server started on {addr[0]}:{addr[1]}")
            
        except Exception as e:
            self.logger.error(f"Error starting server: {str(e)}")
            raise
            
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming TCP connection"""
        addr = writer.get_extra_info('peername')
        self.logger.debug(f"New connection from {addr}")
        
        try:
            while True:
                data = await reader.read(8192)  # 8KB chunks
                if not data:
                    break
                    
                # Echo back for now - override this in subclasses
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            self.logger.error(f"Error handling connection from {addr}: {str(e)}")
            
        finally:
            writer.close()
            await writer.wait_closed()
            self.logger.debug(f"Connection closed from {addr}")
            
    async def connect_to_peer(self, host: str, port: int, 
                            timeout: float = 30) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to a peer"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            return reader, writer
            
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout connecting to {host}:{port}")
            raise
        except Exception as e:
            self.logger.error(f"Error connecting to {host}:{port}: {str(e)}")
            raise
            
    async def stop(self) -> None:
        """Stop the server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("Server stopped") 
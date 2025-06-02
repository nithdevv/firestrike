import stem.process
import stem.control
import socks
import socket
import asyncio
import logging
from typing import Optional, Tuple

class TorConnection:
    def __init__(self, tor_port: int = 9050, control_port: int = 9051):
        self.tor_port = tor_port
        self.control_port = control_port
        self.tor_process: Optional[stem.process.Process] = None
        self.controller: Optional[stem.control.Controller] = None
        
    async def start_tor(self) -> None:
        # Start TOR process and configure SOCKS proxy
        try:
            self.tor_process = stem.process.launch_tor_with_config(
                config = {
                    'SocksPort': str(self.tor_port),
                    'ControlPort': str(self.control_port),
                },
                init_msg_handler = lambda msg: logging.debug(f"Tor initialization: {msg}")
            )
            
            # Setup controller
            self.controller = stem.control.Controller.from_port(port=self.control_port)
            self.controller.authenticate()
            
            # Configure SOCKS proxy for all connections
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            socket.socket = socks.socksocket
            
            logging.info("Tor successfully started and configured")
        except Exception as e:
            logging.error(f"Error starting Tor: {e}")
            raise
            
    async def get_new_identity(self) -> None:
        # Request new Tor identity
        if self.controller:
            await asyncio.to_thread(self.controller.signal, stem.Signal.NEWNYM)
            logging.info("New Tor identity acquired")
            
    async def get_hidden_service(self, port: int) -> Tuple[str, str]:
        # Create hidden service and return its onion address
        if not self.controller:
            raise RuntimeError("Tor controller not initialized")
            
        response = await asyncio.to_thread(
            self.controller.create_hidden_service,
            port = port,
            target_port = port
        )
        
        return response.hostname, response.private_key
        
    async def stop(self) -> None:
        # Stop Tor process and release resources
        if self.controller:
            await asyncio.to_thread(self.controller.close)
        if self.tor_process:
            self.tor_process.kill()
        logging.info("Tor stopped") 
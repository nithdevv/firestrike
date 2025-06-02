import asyncio
import logging
import json
from typing import Dict, List, Optional, Set, Tuple
from .tor_connection import TorConnection
from .crypto import CryptoHandler

class DHTNode:
    def __init__(self, port: int = 8788):
        self.port = port
        self.tor = TorConnection()
        self.crypto = CryptoHandler()
        
        # Ключи узла
        self.private_key: Optional[bytes] = None
        self.public_key: Optional[bytes] = None
        
        # Onion-адрес узла
        self.onion_address: Optional[str] = None
        
        # Таблица маршрутизации: {node_id: (onion_address, public_key)}
        self.routing_table: Dict[str, Tuple[str, bytes]] = {}
        
        # Хранилище данных: {hash: (data, salt)}
        self.data_store: Dict[str, Tuple[bytes, bytes]] = {}
        
        # Известные пиры
        self.peers: Set[str] = set()
        
    async def start(self) -> None:
        """Запускает DHT узел"""
        # Инициализируем Tor
        await self.tor.start_tor()
        
        # Генерируем ключи
        self.private_key, self.public_key = self.crypto.generate_keypair()
        
        # Создаем скрытый сервис
        self.onion_address, _ = await self.tor.get_hidden_service(self.port)
        
        # Запускаем сервер
        server = await asyncio.start_server(
            self.handle_connection, '127.0.0.1', self.port
        )
        
        logging.info(f"DHT узел запущен на {self.onion_address}")
        await server.serve_forever()
        
    async def handle_connection(self, reader: asyncio.StreamReader, 
                              writer: asyncio.StreamWriter) -> None:
        """Обрабатывает входящие соединения"""
        try:
            data = await reader.read(4096)
            message = json.loads(data.decode())
            
            if message['type'] == 'store':
                # Сохраняем данные
                file_data = message['data'].encode()
                file_hash, salt = self.crypto.anonymous_hash(file_data)
                self.data_store[file_hash.hex()] = (file_data, salt)
                response = {'status': 'ok', 'hash': file_hash.hex()}
                
            elif message['type'] == 'find':
                # Ищем данные
                file_hash = message['hash']
                if file_hash in self.data_store:
                    data, salt = self.data_store[file_hash]
                    response = {
                        'status': 'found',
                        'data': data.decode(),
                        'salt': salt.hex()
                    }
                else:
                    response = {'status': 'not_found'}
                    
            elif message['type'] == 'ping':
                # Обновляем информацию о пире
                peer_address = message['address']
                peer_pubkey = message['public_key']
                self.peers.add(peer_address)
                self.routing_table[peer_address] = (
                    peer_address,
                    self.crypto.decode_key(peer_pubkey)
                )
                response = {
                    'status': 'ok',
                    'address': self.onion_address,
                    'public_key': self.crypto.encode_key(self.public_key)
                }
            
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except Exception as e:
            logging.error(f"Ошибка при обработке соединения: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def store_file(self, data: bytes) -> str:
        """Сохраняет файл в DHT"""
        file_hash, salt = self.crypto.anonymous_hash(data)
        self.data_store[file_hash.hex()] = (data, salt)
        
        # Распространяем данные на известные узлы
        for peer in self.peers:
            try:
                reader, writer = await asyncio.open_connection(
                    '127.0.0.1', self.port
                )
                
                message = {
                    'type': 'store',
                    'data': data.decode()
                }
                
                writer.write(json.dumps(message).encode())
                await writer.drain()
                
                writer.close()
                await writer.wait_closed()
                
            except Exception as e:
                logging.error(f"Ошибка при распространении данных: {e}")
                
        return file_hash.hex()
        
    async def find_file(self, file_hash: str) -> Optional[Tuple[bytes, bytes]]:
        """Ищет файл в DHT по хешу"""
        # Сначала ищем локально
        if file_hash in self.data_store:
            return self.data_store[file_hash]
            
        # Затем спрашиваем у известных пиров
        for peer in self.peers:
            try:
                reader, writer = await asyncio.open_connection(
                    '127.0.0.1', self.port
                )
                
                message = {
                    'type': 'find',
                    'hash': file_hash
                }
                
                writer.write(json.dumps(message).encode())
                await writer.drain()
                
                response = await reader.read(4096)
                result = json.loads(response.decode())
                
                writer.close()
                await writer.wait_closed()
                
                if result['status'] == 'found':
                    return (
                        result['data'].encode(),
                        bytes.fromhex(result['salt'])
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка при поиске данных: {e}")
                
        return None
        
    async def join_network(self, bootstrap_node: str) -> None:
        """Присоединяется к сети через известный узел"""
        try:
            reader, writer = await asyncio.open_connection(
                '127.0.0.1', self.port
            )
            
            message = {
                'type': 'ping',
                'address': self.onion_address,
                'public_key': self.crypto.encode_key(self.public_key)
            }
            
            writer.write(json.dumps(message).encode())
            await writer.drain()
            
            response = await reader.read(4096)
            result = json.loads(response.decode())
            
            if result['status'] == 'ok':
                self.peers.add(result['address'])
                self.routing_table[result['address']] = (
                    result['address'],
                    self.crypto.decode_key(result['public_key'])
                )
                
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logging.error(f"Ошибка при присоединении к сети: {e}")
            
    async def stop(self) -> None:
        """Останавливает DHT узел"""
        await self.tor.stop() 
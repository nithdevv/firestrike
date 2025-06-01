import pytest
import os
import asyncio
import tempfile
import random
import psutil
import gc
from pathlib import Path
from typing import Generator, Tuple
import pytest_asyncio
from ..file_encryptor import FileEncryptor
from ..hidden_service import FireStrikeNode
from ..cli import FireStrikeCLI

@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def sample_file(temp_dir) -> Generator[Tuple[str, bytes], None, None]:
    """Создает тестовый файл с случайными данными"""
    file_path = os.path.join(temp_dir, "test_file.bin")
    # Создаем файл размером 1MB
    data = os.urandom(1024 * 1024)
    with open(file_path, "wb") as f:
        f.write(data)
    yield file_path, data

@pytest.fixture
def large_file(temp_dir) -> Generator[Tuple[str, bytes], None, None]:
    """Создает большой тестовый файл (100MB)"""
    file_path = os.path.join(temp_dir, "large_file.bin")
    # Создаем файл размером 100MB
    chunk_size = 1024 * 1024  # 1MB
    total_size = 100 * chunk_size  # 100MB
    
    with open(file_path, "wb") as f:
        remaining = total_size
        while remaining > 0:
            chunk = os.urandom(min(chunk_size, remaining))
            f.write(chunk)
            remaining -= len(chunk)
    
    # Читаем файл для проверки
    with open(file_path, "rb") as f:
        data = f.read()
    yield file_path, data

@pytest_asyncio.fixture
async def dht_network():
    """Создает изолированную DHT сеть из трех нод"""
    nodes = []
    try:
        # Создаем три ноды на разных портах
        for port in range(8788, 8791):
            node = FireStrikeNode(port=port)
            await node.start_tor()
            nodes.append(node)
        
        # Соединяем ноды между собой
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                message = {
                    'type': 'ping',
                    'sender': nodes[i].onion_address
                }
                await nodes[i].connect_to_peer(nodes[j].onion_address, message)
        
        yield nodes
    finally:
        # Останавливаем все ноды
        for node in nodes:
            await node.stop()

class TestFileEncryption:
    """Тесты шифрования и дешифрования файлов"""
    
    def test_file_encryption(self, sample_file):
        """Проверяет корректность шифрования файла"""
        file_path, original_data = sample_file
        encryptor = FileEncryptor()
        
        # Генерируем ключ и шифруем файл
        key = encryptor.generate_key()
        encrypted_data = encryptor.encrypt_file(file_path, key)
        
        # Проверяем, что зашифрованные данные отличаются от оригинальных
        assert encrypted_data != original_data
        assert len(encrypted_data) >= len(original_data)  # Учитываем IV и паддинг
        
    def test_hash_calculation(self, sample_file):
        """Проверяет стабильность хеширования"""
        file_path, _ = sample_file
        encryptor = FileEncryptor()
        
        # Вычисляем хеш дважды
        hash1 = encryptor.calculate_file_hash(file_path)
        hash2 = encryptor.calculate_file_hash(file_path)
        
        # Хеши должны совпадать
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA3-256 дает 64 символа в hex
        
    def test_magnet_link_format(self, sample_file):
        """Проверяет формат магнет-ссылок"""
        file_path, _ = sample_file
        encryptor = FileEncryptor()
        
        magnet = encrypt_and_generate_link(file_path)
        
        # Проверяем формат
        assert magnet.startswith("firestrike://")
        assert "#" in magnet
        parts = magnet.split("://")[1].split("#")
        assert len(parts) == 2
        assert len(parts[0]) == 64  # SHA3-256 хеш
        assert len(parts[1]) > 0  # Base64 ключ

@pytest.mark.asyncio
class TestDHTNetwork:
    """Тесты работы DHT сети"""
    
    async def test_node_discovery(self, dht_network):
        """Проверяет обнаружение нод в сети"""
        # Проверяем, что все ноды знают друг о друге
        for node in dht_network:
            assert len(node.peers) == len(dht_network) - 1
            
    async def test_file_distribution(self, dht_network, sample_file):
        """Проверяет распространение файла по сети"""
        file_path, original_data = sample_file
        cli = FireStrikeCLI()
        
        # Загружаем файл через первую ноду
        magnet = await cli.upload_file(file_path)
        
        # Пытаемся скачать через последнюю ноду
        result = await cli.download_file(magnet, temp=True)
        
        # Проверяем, что данные совпадают
        assert result == original_data
        
    async def test_node_failure(self, dht_network, sample_file):
        """Проверяет работу сети при отказе ноды"""
        file_path, original_data = sample_file
        cli = FireStrikeCLI()
        
        # Загружаем файл
        magnet = await cli.upload_file(file_path)
        
        # Отключаем одну ноду
        await dht_network[1].stop()
        
        # Проверяем, что файл все еще доступен
        result = await cli.download_file(magnet, temp=True)
        assert result == original_data

@pytest.mark.asyncio
class TestMemoryLeaks:
    """Тесты на утечки памяти"""
    
    def get_process_memory(self):
        """Возвращает текущее потребление памяти процессом"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    
    async def test_large_file_upload(self, large_file):
        """Проверяет утечки памяти при загрузке большого файла"""
        file_path, _ = large_file
        cli = FireStrikeCLI()
        
        # Замеряем память до операции
        gc.collect()
        memory_before = self.get_process_memory()
        
        # Загружаем большой файл
        magnet = await cli.upload_file(file_path)
        
        # Принудительно вызываем сборщик мусора
        gc.collect()
        memory_after = self.get_process_memory()
        
        # Проверяем, что разница в памяти не превышает 10MB
        memory_diff = memory_after - memory_before
        assert memory_diff < 10 * 1024 * 1024  # 10MB
        
    async def test_large_file_download(self, dht_network, large_file):
        """Проверяет утечки памяти при скачивании большого файла"""
        file_path, original_data = large_file
        cli = FireStrikeCLI()
        
        # Загружаем файл
        magnet = await cli.upload_file(file_path)
        
        # Замеряем память до скачивания
        gc.collect()
        memory_before = self.get_process_memory()
        
        # Скачиваем файл
        result = await cli.download_file(magnet, temp=True)
        
        # Проверяем память после скачивания
        gc.collect()
        memory_after = self.get_process_memory()
        
        # Проверяем результат и утечки памяти
        assert result == original_data
        memory_diff = memory_after - memory_before
        assert memory_diff < 10 * 1024 * 1024  # 10MB 
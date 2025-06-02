import pytest
import logging
import os
from pathlib import Path

def pytest_configure(config):
    """Конфигурация для запуска тестов"""
    # Отключаем вывод логов при тестировании
    logging.getLogger().setLevel(logging.ERROR)
    
    # Создаем временную директорию для тестов если её нет
    test_dir = Path("test_data")
    if not test_dir.exists():
        test_dir.mkdir()

def pytest_unconfigure(config):
    """Очистка после завершения тестов"""
    # Удаляем временные файлы
    test_dir = Path("test_data")
    if test_dir.exists():
        for file in test_dir.glob("*"):
            try:
                file.unlink()
            except:
                pass
        test_dir.rmdir()

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Автоматически очищает временные файлы после каждого теста"""
    yield
    # Удаляем все .fire файлы
    for file in Path().glob("*.fire"):
        try:
            file.unlink()
        except:
            pass 
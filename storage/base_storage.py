"""
Базовый класс для хранилищ данных.
Абстрактный интерфейс для различных бэкендов.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    """Базовый класс для всех хранилищ"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._connected = False
        self._logger = logging.getLogger(f"storage.{self.__class__.__name__}")
    
    @abstractmethod
    def connect(self) -> bool:
        """Подключение к хранилищу"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Отключение от хранилища"""
        pass
    
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> bool:
        """Сохранение данных"""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Загрузка данных"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Удаление данных"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        pass
    
    @abstractmethod
    def list_keys(self, pattern: str = "*") -> List[str]:
        """Список ключей по паттерну"""
        pass
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    def save_many(self, items: Dict[str, Dict[str, Any]]) -> int:
        """Сохранение нескольких записей"""
        count = 0
        for key, data in items.items():
            if self.save(key, data):
                count += 1
        return count
    
    def load_many(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Загрузка нескольких записей"""
        result = {}
        for key in keys:
            result[key] = self.load(key)
        return result
    
    def clear(self) -> bool:
        """Очистка хранилища"""
        keys = self.list_keys()
        for key in keys:
            self.delete(key)
        return True
"""
JSON файловое хранилище.
Простое хранение данных в JSON файлах.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from storage.base_storage import BaseStorage
import logging
import fnmatch

logger = logging.getLogger(__name__)


class JSONStorage(BaseStorage):
    """Хранилище на основе JSON файлов"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.base_path = Path(config.get("path", "./data/json"))
        self.extension = config.get("extension", ".json")
        self._ensure_dir()
    
    def _ensure_dir(self) -> None:
        """Создание директории"""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Получение пути к файлу"""
        # Замена недопустимых символов
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_path / f"{safe_key}{self.extension}"
    
    def connect(self) -> bool:
        """Подключение"""
        try:
            self._ensure_dir()
            self._connected = True
            self._logger.info(f"JSON Storage подключён: {self.base_path}")
            return True
        except Exception as e:
            self._logger.error(f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self) -> None:
        """Отключение"""
        self._connected = False
        self._logger.info("JSON Storage отключён")
    
    def save(self, key: str, data: Dict[str, Any]) -> bool:
        """Сохранение данных"""
        if not self._connected:
            return False
        
        try:
            file_path = self._get_file_path(key)
            data["_metadata"] = {
                "saved_at": __import__("datetime").datetime.now().isoformat(),
                "key": key
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._logger.debug(f"Данные сохранены: {key}")
            return True
            
        except Exception as e:
            self._logger.error(f"Ошибка сохранения {key}: {e}")
            return False
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Загрузка данных"""
        if not self._connected:
            return None
        
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._logger.debug(f"Данные загружены: {key}")
            return data
            
        except Exception as e:
            self._logger.error(f"Ошибка загрузки {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Удаление данных"""
        if not self._connected:
            return False
        
        try:
            file_path = self._get_file_path(key)
            
            if file_path.exists():
                file_path.unlink()
                self._logger.debug(f"Данные удалены: {key}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Ошибка удаления {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Проверка существования"""
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    def list_keys(self, pattern: str = "*") -> List[str]:
        """Список ключей"""
        keys = []
        
        for file_path in self.base_path.glob(f"*{self.extension}"):
            key = file_path.stem
            if fnmatch.fnmatch(key, pattern):
                keys.append(key)
        
        return keys
    
    def get_file_size(self, key: str) -> int:
        """Размер файла в байтах"""
        file_path = self._get_file_path(key)
        if file_path.exists():
            return file_path.stat().st_size
        return 0
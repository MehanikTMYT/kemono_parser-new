"""
Модуль валидации данных.
"""

import re
from typing import Optional, List, Dict, Any
from pathlib import Path


class Validators:
    """Класс с методами валидации"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Проверка URL"""
        pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        return bool(pattern.match(url))
    
    @staticmethod
    def is_valid_hash(hash_string: str, algorithm: str = "sha256") -> bool:
        """Проверка хэша"""
        lengths = {
            "md5": 32,
            "sha1": 40,
            "sha256": 64,
            "sha512": 128
        }
        
        expected_length = lengths.get(algorithm.lower(), 64)
        pattern = re.compile(r'^[a-fA-F0-9]{' + str(expected_length) + r'}$')
        return bool(pattern.match(hash_string))
    
    @staticmethod
    def is_valid_path(path: str, must_exist: bool = False) -> bool:
        """Проверка пути"""
        try:
            path_obj = Path(path)
            if must_exist:
                return path_obj.exists()
            return True
        except:
            return False
    
    @staticmethod
    def is_valid_service(service: str) -> bool:
        """Проверка сервиса Kemono"""
        valid_services = ["patreon", "fanbox", "onlyfans", "gumroad", "subscribestar"]
        return service.lower() in valid_services
    
    @staticmethod
    def is_valid_creator_id(creator_id: str) -> bool:
        """Проверка ID создателя"""
        if not creator_id:
            return False
        # ID не должен содержать специальных символов
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', creator_id))
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """
        Валидация конфигурации.
        
        Returns:
            Список ошибок
        """
        errors = []
        
        # Проверка обязательных полей
        if "api" in config:
            api = config["api"]
            if "rate_limit" in api:
                if not isinstance(api["rate_limit"], (int, float)) or api["rate_limit"] <= 0:
                    errors.append("api.rate_limit должен быть положительным числом")
            
            if "timeout" in api:
                if not isinstance(api["timeout"], int) or api["timeout"] <= 0:
                    errors.append("api.timeout должен быть положительным целым")
        
        if "downloads" in config:
            dl = config["downloads"]
            if "base_dir" in dl:
                if not Validators.is_valid_path(dl["base_dir"]):
                    errors.append(f"Невалидный путь: {dl['base_dir']}")
        
        return errors
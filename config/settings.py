"""
Модуль управления настройками приложения.
Загрузка из YAML, ENV и дефолтных значений.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Загрузка .env файла
load_dotenv()


class Settings:
    """Класс для управления настройками приложения"""
    
    _instance: Optional["Settings"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[Path] = None
        self._load_config()
        self._initialized = True
    
    def _load_config(self) -> None:
        """Загрузка конфигурации из файлов"""
        # Дефолтные значения
        self._config = self._get_defaults()
        
        # Загрузка из YAML
        config_paths = [
            Path("config/config.yaml"),
            Path("config/config.local.yaml"),
            Path("config.yaml"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                self._config_path = config_path
                with open(config_path, "r", encoding="utf-8") as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self._merge_config(yaml_config)
                logger.info(f"Конфигурация загружена: {config_path}")
                break
        
        # Переопределение из ENV
        self._load_from_env()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Дефолтные настройки"""
        return {
            "app": {
                "name": "Kemono Parser",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "api": {
                "service": "kemono",
                "base_url": "https://kemono.cr/api/v1",
                "rate_limit": 30,
                "timeout": 30,
                "retry_count": 3
            },
            "modules": {
                "api_client": {"enabled": True},
                "ip_checker": {"enabled": True},
                "proxy_manager": {"enabled": True, "proxy_url": None},
                "artist_search": {"enabled": True, "cache_enabled": True},
                "post_parser": {"enabled": True, "save_metadata": True},
                "file_downloader": {
                    "enabled": True,
                    "download_dir": "./downloads",
                    "chunk_size": 8192,
                    "timeout": 60
                }
            },
            "storage": {
                "type": "sqlite",
                "path": "./data/parser.db"
            },
            "downloads": {
                "base_dir": "./downloads",
                "organize_by": "creator",
                "max_concurrent": 3
            }
        }
    
    def _merge_config(self, new_config: Dict) -> None:
        """Слияние конфигураций"""
        for key, value in new_config.items():
            if key in self._config and isinstance(value, dict) and isinstance(self._config[key], dict):
                self._config[key].update(value)
            else:
                self._config[key] = value
    
    def _load_from_env(self) -> None:
        """Загрузка настроек из переменных окружения"""
        env_mapping = {
        "KP_API_KEY": ("api", "api_key"),
        "KP_SESSION_COOKIE": ("modules", "api_client", "session_cookie"),
        "KP_PROXY_URL": ("modules", "proxy_manager", "proxy_url"),
        "KP_DOWNLOAD_DIR": ("downloads", "base_dir"),
        "KP_LOG_LEVEL": ("app", "log_level"),
        "KP_DEBUG": ("app", "debug"),
    }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                # Преобразование типов
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                
                # Установка в конфигурацию
                config = self._config
                for key in config_path[:-1]:
                    config = config.setdefault(key, {})
                config[config_path[-1]] = value
                logger.debug(f"ENV {env_var} -> {config_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения по ключу (точечная нотация)"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Установка значения по ключу"""
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        
        config[keys[-1]] = value
        logger.debug(f"Настройка обновлена: {key} = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """Получение всей конфигурации"""
        return self._config.copy()
    
    def save(self, path: Optional[str] = None) -> bool:
        """Сохранение конфигурации в файл"""
        save_path = Path(path) if path else self._config_path
        if not save_path:
            logger.error("Путь для сохранения не указан")
            return False
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"Конфигурация сохранена: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    @property
    def debug(self) -> bool:
        return self.get("app.debug", False)
    
    @property
    def log_level(self) -> str:
        return self.get("app.log_level", "INFO")
    
    @property
    def api_key(self) -> Optional[str]:
        return self.get("api.api_key")
    
    @property
    def proxy_url(self) -> Optional[str]:
        return self.get("modules.proxy_manager.proxy_url")
    
    @property
    def download_dir(self) -> str:
        return self.get("downloads.base_dir", "./downloads")


# Глобальный экземпляр
settings = Settings()
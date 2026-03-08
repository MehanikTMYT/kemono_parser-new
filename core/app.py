"""
Главный класс приложения.
"""

from typing import Dict, Optional
import logging
import yaml
from pathlib import Path

from core.registry import ModuleRegistry
from utils.logger import setup_logger


class KemonoParserApp:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.registry = ModuleRegistry()
        self._logger = setup_logger("app", self.config.get("app", {}).get("log_level", "INFO"))
        self._logger.info("Kemono Parser App запускается...")
    
    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def register_default_modules(self) -> None:
        from modules.api_client.api_client_module import APIClientModule
        from modules.artist_search.artist_search_module import ArtistSearchModule
        from modules.post_parser.post_parser_module import PostParserModule
        from modules.file_downloader.downloader_module import FileDownloaderModule
        from modules.ip_checker.ip_checker_module import IPCheckerModule
        from modules.proxy_manager.proxy_manager_module import ProxyManagerModule
        
        self.registry.register_class(APIClientModule)
        self.registry.register_class(ArtistSearchModule)
        self.registry.register_class(PostParserModule)
        self.registry.register_class(FileDownloaderModule)
        self.registry.register_class(IPCheckerModule)
        self.registry.register_class(ProxyManagerModule)
    
    def initialize(self) -> bool:
        try:
            self.register_default_modules()
            
            modules_order = [
                "api_client",
                "ip_checker",
                "proxy_manager",
                "artist_search",
                "post_parser",
                "file_downloader"
            ]
            
            for module_name in modules_order:
                config = self.config.get("modules", {}).get(module_name, {})
                self.registry.initialize_module(module_name, config)
            
            self._logger.info("Все модули инициализированы")
            return True
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            return False
    
    def run_artist_download(self, artist_name: str, service: str = "patreon") -> Dict:
        result = {
            "success": False,
            "artist": None,
            "posts_count": 0,
            "files_downloaded": 0,
            "errors": []
        }
        
        try:
            search_module = self.registry.get_module("artist_search")
            artists = search_module.execute(artist_name, service)
            
            if not artists:
                result["errors"].append(f"Артист {artist_name} не найден")
                return result
            
            result["artist"] = artists[0]
            creator_id = artists[0]["creator_id"]
            
            parser_module = self.registry.get_module("post_parser")
            posts = parser_module.execute(service, creator_id)
            result["posts_count"] = len(posts)
            
            downloader_module = self.registry.get_module("file_downloader")
            downloaded = 0
            
            for post in posts[:5]:  # Ограничение для теста
                files = post.get("attachments", [])
                for file_info in files:
                    download_result = downloader_module.execute(
                        url=file_info.get("path"),
                        filename=f"{post['id']}_{file_info.get('name', 'file')}"
                    )
                    if download_result.get("success"):
                        downloaded += 1
            
            result["files_downloaded"] = downloaded
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Ошибка выполнения: {e}")
        
        return result
    
    def shutdown(self) -> None:
        self._logger.info("Завершение работы...")
        self.registry.shutdown_all()
        self._logger.info("Приложение остановлено")
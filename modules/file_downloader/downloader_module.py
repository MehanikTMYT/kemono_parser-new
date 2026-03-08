"""
Модуль скачивания файлов с проверкой IP и прокси.
"""

from typing import Dict, Optional, Callable
from pathlib import Path
import requests
import hashlib
from modules.base_module import BaseModule, ModuleState


class FileDownloaderModule(BaseModule):
    """Модуль скачивания файлов"""
    
    name = "file_downloader"
    version = "1.0.0"
    description = "Скачивание файлов с поддержкой прокси и проверкой IP"
    dependencies = ["ip_checker", "proxy_manager"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.download_dir = Path(config.get("download_dir", "./downloads"))
        self.chunk_size = config.get("chunk_size", 8192)
        self.timeout = config.get("timeout", 60)
        self.ip_checker = None
        self.proxy_manager = None
    
    def initialize(self) -> bool:
        """Инициализация"""
        try:
            from core.registry import ModuleRegistry
            registry = ModuleRegistry()
            
            self.ip_checker = registry.get_module("ip_checker")
            self.proxy_manager = registry.get_module("proxy_manager")
            
            self.download_dir.mkdir(parents=True, exist_ok=True)
            self._set_state(ModuleState.READY)
            
            return True
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            return False
    
    def execute(
        self,
        url: str,
        filename: str,
        use_proxy: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Скачивание файла.
        
        Returns:
            Dict со статусом и путём к файлу
        """
        result = {
            "success": False,
            "path": None,
            "size": 0,
            "hash": None,
            "error": None
        }
        
        if self.state != ModuleState.READY:
            result["error"] = "Модуль не готов"
            return result
        
        # Проверка IP для Dropbox
        if "dropbox.com" in url:
            if self.ip_checker:
                ip_info = self.ip_checker.execute()
                if ip_info.get("is_ru") and not use_proxy:
                    result["error"] = "RF detected, proxy required for Dropbox"
                    return result
        
        # Получение сессии с прокси
        session = self._get_session(use_proxy)
        filepath = self.download_dir / filename
        
        try:
            self._set_state(ModuleState.RUNNING)
            
            with session.get(url, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                
                total = int(response.headers.get("content-length", 0))
                downloaded = 0
                file_hash = hashlib.sha256()
                
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        f.write(chunk)
                        file_hash.update(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total:
                            progress_callback(downloaded, total)
                
                result.update({
                    "success": True,
                    "path": str(filepath),
                    "size": downloaded,
                    "hash": file_hash.hexdigest()
                })
                
                self._logger.info(f"Скачано: {filename} ({downloaded} bytes)")
                
        except Exception as e:
            result["error"] = str(e)
            self._logger.error(f"Ошибка скачивания: {e}")
        
        finally:
            self._set_state(ModuleState.READY)
        
        return result
    
    def _get_session(self, use_proxy: bool) -> requests.Session:
        """Получение сессии с прокси"""
        session = requests.Session()
        
        if use_proxy and self.proxy_manager:
            proxy = self.proxy_manager.execute()
            if proxy:
                session.proxies = {"http": proxy, "https": proxy}
        
        return session
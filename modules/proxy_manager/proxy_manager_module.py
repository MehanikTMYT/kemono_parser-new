"""
Модуль управления прокси.
Поддержка ротации и проверки прокси.
"""

from typing import Dict, List, Optional
import requests
from modules.base_module import BaseModule, ModuleState
import logging
import random

logger = logging.getLogger(__name__)


class ProxyManagerModule(BaseModule):
    """Модуль управления прокси"""
    
    name = "proxy_manager"
    version = "1.0.0"
    description = "Управление прокси с поддержкой ротации"
    dependencies = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._proxies: List[Dict] = []
        self._current_proxy: Optional[Dict] = None
        self._proxy_index = 0
        self._auto_rotate = config.get("auto_rotate", False)
        self._check_url = config.get("check_url", "https://httpbin.org/ip")
        self._timeout = config.get("timeout", 10)
        
        # Добавление прокси из конфига
        proxy_url = config.get("proxy_url")
        if proxy_url:
            self.add_proxy(proxy_url)
    
    def initialize(self) -> bool:
        """Инициализация модуля"""
        try:
            if self._proxies:
                self._current_proxy = self._proxies[0]
                self._set_state(ModuleState.READY)
                self._logger.info(f"Proxy Manager инициализирован ({len(self._proxies)} прокси)")
            else:
                self._set_state(ModuleState.READY)
                self._logger.info("Proxy Manager инициализирован (нет прокси)")
            return True
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            self._set_state(ModuleState.ERROR)
            return False
    
    def execute(self) -> Optional[str]:
        """
        Получение текущего прокси.
        
        Returns:
            URL прокси или None
        """
        if self.state != ModuleState.READY:
            return None
        
        if self._auto_rotate and len(self._proxies) > 1:
            self.rotate()
        
        if self._current_proxy:
            return self._current_proxy.get("url")
        return None
    
    def add_proxy(
        self,
        url: str,
        protocol: str = "http",
        country: Optional[str] = None,
        priority: int = 0
    ) -> bool:
        """
        Добавление прокси.
        
        Args:
            url: URL прокси (user:pass@host:port)
            protocol: Протокол (http, https, socks4, socks5)
            country: Страна прокси
            priority: Приоритет
        """
        # Нормализация URL
        if not url.startswith(("http://", "https://", "socks4://", "socks5://")):
            url = f"{protocol}://{url}"
        
        proxy = {
            "url": url,
            "protocol": protocol,
            "country": country,
            "priority": priority,
            "added_at": __import__("datetime").datetime.now().isoformat(),
            "working": None,
            "last_check": None
        }
        
        self._proxies.append(proxy)
        self._proxies.sort(key=lambda p: p["priority"], reverse=True)
        
        if not self._current_proxy:
            self._current_proxy = proxy
        
        self._logger.info(f"Прокси добавлен: {url[:30]}...")
        return True
    
    def add_proxies(self, proxy_list: List[str]) -> int:
        """Добавление нескольких прокси"""
        count = 0
        for proxy_url in proxy_list:
            if self.add_proxy(proxy_url):
                count += 1
        return count
    
    def rotate(self) -> Optional[str]:
        """Переключение на следующий прокси"""
        if len(self._proxies) <= 1:
            return self._current_proxy.get("url") if self._current_proxy else None
        
        self._proxy_index = (self._proxy_index + 1) % len(self._proxies)
        self._current_proxy = self._proxies[self._proxy_index]
        
        self._logger.debug(f"Прокси ротирован: {self._current_proxy.get('url', '')[:30]}...")
        return self._current_proxy.get("url")
    
    def remove_proxy(self, url: str) -> bool:
        """Удаление прокси"""
        for i, proxy in enumerate(self._proxies):
            if proxy["url"] == url:
                self._proxies.pop(i)
                if self._current_proxy == proxy:
                    self._current_proxy = self._proxies[0] if self._proxies else None
                self._logger.info(f"Прокси удалён: {url[:30]}...")
                return True
        return False
    
    def check_proxy(self, proxy_url: Optional[str] = None) -> bool:
        """
        Проверка работоспособности прокси.
        
        Returns:
            True если прокси работает
        """
        url = proxy_url or self.execute()
        if not url:
            return False
        
        try:
            proxies = {"http": url, "https": url}
            response = requests.get(self._check_url, proxies=proxies, timeout=self._timeout)
            response.raise_for_status()
            
            # Обновление статуса
            for proxy in self._proxies:
                if proxy["url"] == url:
                    proxy["working"] = True
                    proxy["last_check"] = __import__("datetime").datetime.now().isoformat()
                    break
            
            self._logger.debug(f"Прокси работает: {url[:30]}...")
            return True
            
        except Exception as e:
            self._logger.debug(f"Прокси не работает: {url[:30]}... - {e}")
            
            for proxy in self._proxies:
                if proxy["url"] == url:
                    proxy["working"] = False
                    proxy["last_check"] = __import__("datetime").datetime.now().isoformat()
                    break
            
            return False
    
    def check_all_proxies(self) -> Dict[str, bool]:
        """Проверка всех прокси"""
        results = {}
        for proxy in self._proxies:
            results[proxy["url"]] = self.check_proxy(proxy["url"])
        return results
    
    def get_working_proxies(self) -> List[str]:
        """Получение списка рабочих прокси"""
        return [p["url"] for p in self._proxies if p.get("working", True)]
    
    def get_proxy_dict(self, proxy_url: Optional[str] = None) -> Dict[str, str]:
        """
        Получение прокси в формате для requests.
        
        Returns:
            Dict {"http": url, "https": url}
        """
        url = proxy_url or self.execute()
        if url:
            return {"http": url, "https": url}
        return {}
    
    def get_stats(self) -> Dict:
        """Статистика по прокси"""
        total = len(self._proxies)
        working = sum(1 for p in self._proxies if p.get("working", True))
        
        return {
            "total": total,
            "working": working,
            "not_working": total - working,
            "current": self._current_proxy.get("url") if self._current_proxy else None,
            "auto_rotate": self._auto_rotate
        }
    
    def clear(self) -> None:
        """Очистка всех прокси"""
        self._proxies.clear()
        self._current_proxy = None
        self._proxy_index = 0
        self._logger.info("Все прокси очищены")
"""
Модуль проверки IP адреса и геолокации.
Используется для определения необходимости прокси.
"""

from typing import Dict, Optional, List
import requests
from modules.base_module import BaseModule, ModuleState
import logging

logger = logging.getLogger(__name__)


class IPCheckerModule(BaseModule):
    """Модуль проверки IP и геолокации"""
    
    name = "ip_checker"
    version = "1.0.0"
    description = "Проверка IP адреса и определение местоположения"
    dependencies = []
    
    # Сервисы для проверки IP
    IP_SERVICES = [
        "https://ipapi.co/json/",
        "https://ipinfo.io/json/",
        "https://api.ipify.org?format=json",
        "https://ipapi.com/ip_api.php"
    ]
    
    # Страны с ограничениями
    RESTRICTED_COUNTRIES = ["RU", "BY", "CN"]
    
    # Хостинги требующие прокси
    PROXY_REQUIRED_HOSTS = [
        "dropbox.com",
        "google.com",
        "mega.nz",
        "mediafire.com"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._cache: Optional[Dict] = None
        self._cache_ttl = config.get("cache_ttl", 300)  # 5 минут
        self._check_url = config.get("check_url", self.IP_SERVICES[0])
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
    
    def initialize(self) -> bool:
        """Инициализация модуля"""
        try:
            self._set_state(ModuleState.READY)
            self._logger.info("Модуль IP Checker инициализирован")
            return True
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            self._set_state(ModuleState.ERROR)
            return False
    
    def execute(self, force_refresh: bool = False) -> Dict:
        """
        Проверка текущего IP.
        
        Args:
            force_refresh: Игнорировать кэш
        
        Returns:
            Dict с информацией об IP
        """
        # Проверка кэша
        if not force_refresh and self._cache:
            import time
            if time.time() - self._cache.get("_timestamp", 0) < self._cache_ttl:
                self._logger.debug("IP информация из кэша")
                return self._cache
        
        self._set_state(ModuleState.RUNNING)
        
        try:
            ip_info = self._check_ip()
            
            if ip_info:
                ip_info["_timestamp"] = __import__("time").time()
                self._cache = ip_info
                self._set_state(ModuleState.READY)
                self._logger.info(f"IP проверен: {ip_info.get('ip')} ({ip_info.get('country_name', 'Unknown')})")
                return ip_info
            else:
                self._set_state(ModuleState.ERROR)
                return {"error": "Не удалось проверить IP"}
                
        except Exception as e:
            self._logger.error(f"Ошибка проверки IP: {e}")
            self._set_state(ModuleState.ERROR)
            return {"error": str(e)}
    
    def _check_ip(self) -> Optional[Dict]:
        """Проверка IP через различные сервисы"""
        for service_url in self.IP_SERVICES:
            try:
                response = self._session.get(service_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Нормализация ответа
                return self._normalize_ip_data(data)
                
            except Exception as e:
                self._logger.debug(f"Сервис {service_url} недоступен: {e}")
                continue
        
        return None
    
    def _normalize_ip_data(self, data: Dict) -> Dict:
        """Нормализация данных от разных сервисов"""
        normalized = {
            "ip": data.get("ip") or data.get("query"),
            "country_code": data.get("country_code") or data.get("country"),
            "country_name": data.get("country_name") or data.get("country"),
            "region": data.get("region") or data.get("regionName"),
            "city": data.get("city"),
            "isp": data.get("org") or data.get("isp"),
            "timezone": data.get("timezone"),
            "is_ru": (data.get("country_code") or data.get("country")) == "RU",
            "is_restricted": (data.get("country_code") or data.get("country")) in self.RESTRICTED_COUNTRIES
        }
        return normalized
    
    def check_host_requires_proxy(self, url: str) -> bool:
        """
        Проверка требует ли хост прокси.
        
        Args:
            url: URL для проверки
        
        Returns:
            True если прокси рекомендуется
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        
        for proxy_host in self.PROXY_REQUIRED_HOSTS:
            if proxy_host in host:
                # Проверяем текущее местоположение
                ip_info = self.execute()
                if ip_info.get("is_restricted"):
                    self._logger.info(f"Хост {host} требует прокси для {ip_info.get('country_name')}")
                    return True
        
        return False
    
    def is_in_restricted_country(self) -> bool:
        """Проверка нахождения в стране с ограничениями"""
        ip_info = self.execute()
        return ip_info.get("is_restricted", False)
    
    def get_country(self) -> Optional[str]:
        """Получение текущей страны"""
        ip_info = self.execute()
        return ip_info.get("country_name")
    
    def clear_cache(self) -> None:
        """Очистка кэша IP"""
        self._cache = None
        self._logger.debug("Кэш IP очищен")
    
    def shutdown(self) -> None:
        """Завершение работы модуля"""
        self._session.close()
        super().shutdown()
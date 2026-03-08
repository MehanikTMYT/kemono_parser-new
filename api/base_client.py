"""
Базовый класс для API клиентов с обходом защиты Kemono.
"""

import requests
from typing import Optional, Dict, Any
from abc import ABC
import logging
import random

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Базовый класс для всех API клиентов"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        proxy: Optional[str] = None,
        headers: Optional[Dict] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.proxy = proxy
        self.session = requests.Session()
        
        selected_ua = random.choice(self.USER_AGENTS)
        
        self.session.headers.update({
            "User-Agent": selected_ua,
            "Accept": "text/css, application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://kemono.cr/",
            "Origin": "https://kemono.cr",
        })
        
        if headers:
            self.session.headers.update(headers)
        
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        
        self._logger = logging.getLogger(f"api.client.{self.__class__.__name__}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
        return self._request("GET", endpoint, params=params, headers=headers, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
        return self._request("POST", endpoint, json=data, **kwargs)
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> Optional[Dict]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault("timeout", self.timeout)
        
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        if "/api/" in url:
            request_headers["Accept"] = "text/css, */*"
        
        try:
            response = self.session.request(method, url, params=params, headers=request_headers, **kwargs)
            
            if response.status_code == 403:
                self._logger.error(f"403 Forbidden: {url}")
                self._logger.debug(f"Response: {response.text[:300]}")
                return None
            
            response.raise_for_status()
            
            if not response.text.strip():
                return {}
            
            try:
                return response.json()
            except ValueError:
                return {"_text": response.text}
            
        except requests.exceptions.HTTPError as e:
            self._logger.error(f"HTTP Error: {e}")
            return None
        except Exception as e:
            self._logger.error(f"Error: {e}")
            return None
    
    def close(self) -> None:
        self.session.close()

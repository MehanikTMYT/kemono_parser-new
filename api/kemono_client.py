"""
Kemono API клиент - поиск через posts endpoint.
"""

import requests
from typing import Dict, List, Optional, Any
import time
import logging

from api.base_client import BaseAPIClient
from api.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class KemonoClient(BaseAPIClient):
    BASE_URLS = {
        "kemono": "https://kemono.cr",
        "coomer": "https://coomer.su"
    }
    
    def __init__(
        self,
        service: str = "kemono",
        rate_limit: int = 30,
        timeout: int = 30,
        proxy: Optional[str] = None,
        session_cookie: Optional[str] = None
    ):
        base_url = self.BASE_URLS.get(service, self.BASE_URLS["kemono"])
        super().__init__(base_url=base_url, timeout=timeout, proxy=proxy)
        self.service = service
        self.rate_limiter = RateLimiter(calls_per_second=1/max(rate_limit, 1))
        self._logger = logging.getLogger(f"api.{service}")
        
        if session_cookie:
            self.set_session_cookie(session_cookie)
    
    def set_session_cookie(self, session_value: str) -> None:
        self.session.cookies.set("session", session_value)
        self.session.cookies.set("session", session_value, domain="kemono.cr")
        self._logger.info("Session cookie установлен")
    
    def is_authenticated(self) -> bool:
        return bool(self.session.cookies.get("session"))
    
    def test_connection(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/v1/app_version", timeout=10)
            if response.status_code == 200:
                self._logger.info(f"API: {response.text[:50]}")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Ошибка: {e}")
            return False
    
    def _request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[Dict]:
        self.rate_limiter.wait()
        
        if not endpoint.startswith("/api"):
            url = f"{self.base_url}/api/v1{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
        
        headers = kwargs.pop("headers", {})
        headers["Accept"] = "text/css, */*"
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            
            if response.status_code in [401, 403]:
                self._logger.warning(f"Auth required: {endpoint} ({response.status_code})")
                return None
            
            if response.status_code == 429:
                time.sleep(5)
                return self._request(endpoint, method, **kwargs)
            
            response.raise_for_status()
            
            if not response.text.strip():
                return {}
            
            try:
                return response.json()
            except ValueError:
                return {"_text": response.text}
            
        except Exception as e:
            self._logger.error(f"Request error: {e}")
            return None
    
    def search_creator(self, name: str, service: str = "patreon") -> List[Dict]:
        """
        Поиск создателя через posts endpoint (creators.txt заблокирован).
        """
        try:
            # Ищем посты по имени артиста
            self._logger.info(f"Поиск '{name}' через posts endpoint...")
            
            posts = self._request("/posts", params={"q": name})
            if not posts or not isinstance(posts, list):
                return []
            
            # Извлекаем уникальных создателей из постов
            creators_map = {}
            for post in posts:
                if not isinstance(post, dict):
                    continue
                
                user = post.get("user", {})
                creator_id = user.get("id") or post.get("user_id")
                creator_name = user.get("name", "")
                post_service = post.get("service", service)
                
                if creator_id and creator_id not in creators_map:
                    # Проверяем совпадение имени
                    if name.lower() in creator_name.lower():
                        creators_map[creator_id] = {
                            "creator_id": str(creator_id),
                            "service": post_service,
                            "name": creator_name,
                            "profile": user
                        }
            
            results = list(creators_map.values())
            self._logger.info(f"Найдено создателей: {len(results)}")
            return results
            
        except Exception as e:
            self._logger.error(f"Search error: {e}")
            return []
    
    def get_creator_profile(self, service: str, creator_id: str) -> Optional[Dict]:
        """Профиль создателя"""
        return self._request(f"/{service}/user/{creator_id}/profile")
    
    def get_creator_posts(self, service: str, creator_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Посты создателя"""
        return self._request(f"/{service}/user/{creator_id}/posts", params={"o": offset, "limit": limit})
    
    def get_all_creator_posts(self, service: str, creator_id: str) -> List[Dict]:
        """Все посты создателя"""
        all_posts = []
        offset = 0
        limit = 50
        
        while True:
            posts = self.get_creator_posts(service, creator_id, limit, offset)
            if not posts:
                break
            all_posts.extend(posts)
            self._logger.info(f"Получено {len(all_posts)} постов...")
            if len(posts) < limit:
                break
            offset += limit
        
        return all_posts
    
    def get_post(self, service: str, creator_id: str, post_id: str) -> Optional[Dict]:
        """Конкретный пост"""
        return self._request(f"/{service}/user/{creator_id}/post/{post_id}")
    
    def get_popular_posts(self) -> List[Dict]:
        """Популярные посты"""
        return self._request("/posts/popular")
    
    def get_random_post(self) -> Optional[Dict]:
        """Случайный пост"""
        return self._request("/posts/random")
    
    def search_posts(self, query: str, service: Optional[str] = None) -> List[Dict]:
        """Поиск постов по запросу"""
        params = {"q": query}
        if service:
            params["f"] = service
        return self._request("/posts", params=params)

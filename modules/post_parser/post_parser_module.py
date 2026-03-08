"""
Модуль парсинга постов и извлечения файлов.
"""

from typing import Dict, List, Optional, Any
import re
from urllib.parse import urlparse, urljoin
from modules.base_module import BaseModule, ModuleState
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PostParserModule(BaseModule):
    """Модуль парсинга постов"""
    
    name = "post_parser"
    version = "1.0.0"
    description = "Парсинг постов и извлечение файлов/ссылок"
    dependencies = ["api_client"]
    
    # Паттерны для поиска ссылок
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        re.IGNORECASE
    )
    
    # Хостинги файлов
    FILE_HOSTS = [
        "dropbox.com",
        "google.com",
        "drive.google.com",
        "mega.nz",
        "mediafire.com",
        "mega.co.nz",
        "uploadhaven.com",
        "katfile.com"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.api_client = None
        self.save_metadata = config.get("save_metadata", True)
        self.metadata_dir = config.get("metadata_dir", "./metadata")
        self._cache = {}
    
    def initialize(self) -> bool:
        """Инициализация модуля"""
        try:
            from core.registry import ModuleRegistry
            registry = ModuleRegistry()
            
            self.api_client = registry.get_module("api_client")
            if not self.api_client:
                self._logger.error("api_client модуль не найден")
                return False
            
            if self.save_metadata:
                from pathlib import Path
                Path(self.metadata_dir).mkdir(parents=True, exist_ok=True)
            
            self._set_state(ModuleState.READY)
            self._logger.info("Модуль Post Parser инициализирован")
            return True
            
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            self._set_state(ModuleState.ERROR)
            return False
    
    def execute(
        self,
        service: str,
        creator_id: str,
        post_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Парсинг постов.
        
        Args:
            service: Сервис (patreon, fanbox, etc.)
            creator_id: ID создателя
            post_id: ID конкретного поста (None для всех)
            limit: Лимит постов
        
        Returns:
            Список распарсенных постов
        """
        if self.state != ModuleState.READY:
            self._logger.error("Модуль не готов")
            return []
        
        self._set_state(ModuleState.RUNNING)
        
        try:
            if post_id:
                # Один пост
                post_data = self.api_client.execute(
                    method="get_post",
                    service=service,
                    creator_id=creator_id,
                    post_id=post_id
                )
                posts = [post_data] if post_data else []
            else:
                # Все посты
                posts = self.api_client.execute(
                    method="get_all_creator_posts",
                    service=service,
                    creator_id=creator_id
                )
                posts = posts or []
            
            # Парсинг каждого поста
            parsed_posts = []
            for post in posts:
                parsed = self._parse_post(post, service, creator_id)
                parsed_posts.append(parsed)
                
                # Сохранение метаданных
                if self.save_metadata:
                    self._save_metadata(parsed, service, creator_id)
            
            self._set_state(ModuleState.READY)
            self._logger.info(f"Распарсено {len(parsed_posts)} постов")
            return parsed_posts
            
        except Exception as e:
            self._logger.error(f"Ошибка парсинга: {e}")
            self._set_state(ModuleState.ERROR)
            return []
    
    def _parse_post(self, post: Dict, service: str, creator_id: str) -> Dict:
        """Парсинг одного поста"""
        parsed = {
            "id": post.get("id"),
            "title": post.get("title", "Untitled"),
            "content": post.get("content", ""),
            "published": post.get("published"),
            "edited": post.get("edited"),
            "service": service,
            "creator_id": creator_id,
            "creator_name": post.get("user", {}).get("name", "Unknown"),
            "attachments": [],
            "external_links": [],
            "files": [],
            "comments_count": post.get("comments_count", 0),
            "like_count": post.get("like_count", 0),
            "parsed_at": datetime.now().isoformat()
        }
        
        # Парсинг вложений
        attachments = post.get("attachments", [])
        for att in attachments:
            file_info = {
                "name": att.get("name", "unknown"),
                "path": att.get("path", ""),
                "type": "attachment",
                "hash": att.get("file_hash", ""),
                "size": att.get("size", 0)
            }
            parsed["attachments"].append(file_info)
            parsed["files"].append(file_info)
        
        # Парсинг ссылок из контента
        if post.get("content"):
            links = self._extract_links(post["content"])
            for link in links:
                link_info = {
                    "url": link,
                    "type": "external_link",
                    "is_file_host": self._is_file_host(link)
                }
                parsed["external_links"].append(link_info)
                
                if link_info["is_file_host"]:
                    parsed["files"].append(link_info)
        
        return parsed
    
    def _extract_links(self, content: str) -> List[str]:
        """Извлечение ссылок из текста"""
        return self.URL_PATTERN.findall(content)
    
    def _is_file_host(self, url: str) -> bool:
        """Проверка является ли ссылка файлообменником"""
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        
        for file_host in self.FILE_HOSTS:
            if file_host in host:
                return True
        return False
    
    def _save_metadata(self, post: Dict, service: str, creator_id: str) -> None:
        """Сохранение метаданных поста"""
        try:
            import json
            from pathlib import Path
            
            metadata_path = Path(self.metadata_dir) / service / creator_id
            metadata_path.mkdir(parents=True, exist_ok=True)
            
            file_path = metadata_path / f"post_{post['id']}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(post, f, ensure_ascii=False, indent=2)
            
            self._logger.debug(f"Метаданные сохранены: {file_path}")
            
        except Exception as e:
            self._logger.error(f"Ошибка сохранения метаданных: {e}")
    
    def extract_files_from_posts(self, posts: List[Dict]) -> List[Dict]:
        """Извлечение всех файлов из списка постов"""
        all_files = []
        for post in posts:
            files = post.get("files", [])
            all_files.extend(files)
        return all_files
    
    def get_posts_by_date_range(
        self,
        posts: List[Dict],
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """Фильтрация постов по диапазону дат"""
        from datetime import datetime
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        filtered = []
        for post in posts:
            published = post.get("published")
            if published:
                try:
                    post_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if start <= post_date <= end:
                        filtered.append(post)
                except:
                    continue
        
        return filtered
    
    def clear_cache(self) -> None:
        """Очистка кэша"""
        self._cache.clear()
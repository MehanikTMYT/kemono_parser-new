"""
Модуль поиска артистов через posts endpoint.
"""

from typing import List, Dict, Optional
from modules.base_module import BaseModule, ModuleState


class ArtistSearchModule(BaseModule):
    name = "artist_search"
    version = "2.0.0"
    description = "Поиск артистов через Kemono posts endpoint"
    dependencies = ["api_client"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.api_client = None
        self._cache = {}
    
    def initialize(self) -> bool:
        try:
            from core.registry import ModuleRegistry
            registry = ModuleRegistry()
            
            self.api_client = registry.get_module("api_client")
            if not self.api_client:
                self._logger.error("api_client модуль не найден")
                return False
            
            self._set_state(ModuleState.READY)
            self._logger.info("Модуль инициализирован")
            return True
            
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            self._set_state(ModuleState.ERROR)
            return False
    
    def execute(self, artist_name: str, service: str = "patreon") -> List[Dict]:
        """Поиск артиста через posts endpoint"""
        if self.state != ModuleState.READY:
            self._logger.error("Модуль не готов")
            return []
        
        cache_key = f"{artist_name.lower()}:{service}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        self._set_state(ModuleState.RUNNING)
        
        try:
            results = self.api_client.execute(
                method="search_creator",
                name=artist_name,
                service=service
            )
            
            self._cache[cache_key] = results or []
            self._set_state(ModuleState.READY)
            
            self._logger.info(f"Найдено {len(results or [])} артистов")
            return results or []
            
        except Exception as e:
            self._logger.error(f"Ошибка поиска: {e}")
            self._set_state(ModuleState.ERROR)
            return []
    
    def clear_cache(self) -> None:
        self._cache.clear()

"""
Модуль API клиента для Kemono/Coomer.
"""

from typing import Dict, Optional, Any
from modules.base_module import BaseModule, ModuleState
import logging

logger = logging.getLogger(__name__)


class APIClientModule(BaseModule):
    name = "api_client"
    version = "1.1.0"
    description = "API клиент для работы с Kemono/Coomer"
    dependencies = []
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.client = None
        self.service = config.get("service", "kemono")
        self.rate_limit = config.get("rate_limit", 30)
        self.timeout = config.get("timeout", 30)
        self.proxy = config.get("proxy")
        self.session_cookie = config.get("session_cookie")
    
    def initialize(self) -> bool:
        try:
            from api.kemono_client import KemonoClient
            
            self.client = KemonoClient(
                service=self.service,
                rate_limit=self.rate_limit,
                timeout=self.timeout,
                proxy=self.proxy,
                session_cookie=self.session_cookie
            )
            
            self._set_state(ModuleState.READY)
            
            auth_status = "✅ Authenticated" if self.client.is_authenticated() else "⚠️ No auth"
            self._logger.info(f"API Client инициализирован ({self.service}) - {auth_status}")
            return True
            
        except Exception as e:
            self._logger.error(f"Ошибка инициализации: {e}")
            self._set_state(ModuleState.ERROR)
            return False
    
    def execute(self, method: str, **kwargs) -> Any:
        if self.state != ModuleState.READY:
            return None
        if not self.client:
            return None
        try:
            self._set_state(ModuleState.RUNNING)
            if not hasattr(self.client, method):
                self._set_state(ModuleState.READY)
                return None
            result = getattr(self.client, method)(**kwargs)
            self._set_state(ModuleState.READY)
            return result
        except Exception as e:
            self._logger.error(f"Ошибка {method}: {e}")
            self._set_state(ModuleState.ERROR)
            return None
    
    def get_client(self):
        return self.client
    
    def shutdown(self) -> None:
        if self.client:
            self.client.close()
        super().shutdown()
"""
Базовый класс для всех модулей системы.
Все модули должны наследоваться от этого класса.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModuleState:
    """Состояния модуля"""
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


class BaseModule(ABC):
    """
    Базовый класс модуля.
    
    Атрибуты:
        name: Уникальное имя модуля
        version: Версия модуля
        description: Описание функционала
        dependencies: Список зависимых модулей
        config: Конфигурация модуля
    """
    
    name: str = "base_module"
    version: str = "1.0.0"
    description: str = "Базовый модуль"
    dependencies: list = []
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.state = ModuleState.UNINITIALIZED
        self.created_at = datetime.now()
        self._logger = logging.getLogger(f"module.{self.name}")
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Инициализация модуля.
        Возвращает True если успешно.
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Основная логика модуля.
        """
        pass
    
    def shutdown(self) -> None:
        """Очистка ресурсов при завершении"""
        self.state = ModuleState.UNINITIALIZED
        self._logger.info(f"Модуль {self.name} остановлен")
    
    def validate_config(self) -> bool:
        """Валидация конфигурации"""
        return True
    
    def get_info(self) -> Dict:
        """Информация о модуле"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "state": self.state,
            "dependencies": self.dependencies,
            "config": self.config
        }
    
    def _set_state(self, state: str) -> None:
        """Установка состояния с логированием"""
        old_state = self.state
        self.state = state
        self._logger.debug(f"Состояние: {old_state} -> {state}")
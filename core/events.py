"""
Система событий для асинхронной коммуникации между модулями.
Паттерн Observer / Pub-Sub.
"""

import asyncio
import threading
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Класс события"""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"Event(name={self.name}, source={self.source})"


@dataclass
class EventHandler:
    """Обработчик события"""
    callback: Callable
    async_mode: bool = False
    priority: int = 0
    once: bool = False


class EventBus:
    """
    Шина событий для коммуникации между модулями.
    Поддерживает синхронные и асинхронные обработчики.
    """
    
    _instance: Optional["EventBus"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._lock = threading.Lock()
        self._event_history: List[Event] = []
        self._max_history = 100
        self._logger = logging.getLogger("events.bus")
        self._initialized = True
    
    def subscribe(
        self,
        event_name: str,
        callback: Callable,
        async_mode: bool = False,
        priority: int = 0,
        once: bool = False
    ) -> None:
        """
        Подписка на событие.
        
        Args:
            event_name: Имя события
            callback: Функция-обработчик
            async_mode: Запускать ли в отдельном потоке
            priority: Приоритет (чем выше, тем раньше)
            once: Удалить после первого вызова
        """
        handler = EventHandler(
            callback=callback,
            async_mode=async_mode,
            priority=priority,
            once=once
        )
        
        with self._lock:
            self._handlers[event_name].append(handler)
            self._handlers[event_name].sort(key=lambda h: h.priority, reverse=True)
        
        self._logger.debug(f"Подписка на {event_name}: {callback.__name__}")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        """Отписка от события"""
        with self._lock:
            handlers = self._handlers.get(event_name, [])
            for i, handler in enumerate(handlers):
                if handler.callback == callback:
                    handlers.pop(i)
                    self._logger.debug(f"Отписка от {event_name}: {callback.__name__}")
                    return True
        return False
    
    def publish(self, event: Event) -> None:
        """
        Публикация события.
        
        Args:
            event: Объект события
        """
        with self._lock:
            handlers = self._handlers.get(event.name, []).copy()
            
            # Сохранение в историю
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        self._logger.debug(f"Событие опубликовано: {event.name}")
        
        # Вызов обработчиков
        for handler in handlers:
            self._invoke_handler(handler, event)
            
            # Удаление once-обработчиков
            if handler.once:
                self.unsubscribe(event.name, handler.callback)
    
    def _invoke_handler(self, handler: EventHandler, event: Event) -> None:
        """Вызов обработчика"""
        try:
            if handler.async_mode:
                # Асинхронный вызов в отдельном потоке
                thread = threading.Thread(
                    target=handler.callback,
                    args=(event,),
                    daemon=True
                )
                thread.start()
            else:
                # Синхронный вызов
                handler.callback(event)
                
        except Exception as e:
            self._logger.error(f"Ошибка обработчика {handler.callback.__name__}: {e}")
    
    def publish_sync(self, event_name: str, data: Dict[str, Any] = None, source: str = None) -> Event:
        """Удобный метод для публикации события"""
        event = Event(name=event_name, data=data or {}, source=source)
        self.publish(event)
        return event
    
    async def publish_async(self, event_name: str, data: Dict[str, Any] = None, source: str = None) -> Event:
        """Асинхронная публикация события"""
        event = Event(name=event_name, data=data or {}, source=source)
        
        with self._lock:
            handlers = self._handlers.get(event.name, []).copy()
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler.callback):
                    await handler.callback(event)
                else:
                    handler.callback(event)
            except Exception as e:
                self._logger.error(f"Ошибка async обработчика: {e}")
        
        return event
    
    def get_history(self, event_name: Optional[str] = None, limit: int = 10) -> List[Event]:
        """Получение истории событий"""
        with self._lock:
            if event_name:
                events = [e for e in self._event_history if e.name == event_name]
            else:
                events = self._event_history.copy()
            return events[-limit:]
    
    def clear_history(self) -> None:
        """Очистка истории"""
        with self._lock:
            self._event_history.clear()
        self._logger.info("История событий очищена")
    
    def get_subscribers_count(self, event_name: str) -> int:
        """Количество подписчиков на событие"""
        return len(self._handlers.get(event_name, []))


# Глобальный экземпляр
event_bus = EventBus()


# === Предопределённые события ===

class AppEvents:
    """Предопределённые имена событий приложения"""
    
    # Жизненный цикл
    APP_START = "app.start"
    APP_STOP = "app.stop"
    MODULE_INIT = "module.init"
    MODULE_SHUTDOWN = "module.shutdown"
    
    # API
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    RATE_LIMIT = "api.rate_limit"
    
    # Загрузка
    DOWNLOAD_START = "download.start"
    DOWNLOAD_PROGRESS = "download.progress"
    DOWNLOAD_COMPLETE = "download.complete"
    DOWNLOAD_ERROR = "download.error"
    
    # Артисты и посты
    ARTIST_FOUND = "artist.found"
    POST_PARSED = "post.parsed"
    FILE_EXTRACTED = "file.extracted"
    
    # Ошибки
    ERROR = "error"
    WARNING = "warning"
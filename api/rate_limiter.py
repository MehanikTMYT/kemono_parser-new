"""
Ограничитель скорости запросов (Rate Limiter).
Предотвращает превышение лимитов API.
"""

import time
import threading
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate Limiter с поддержкой различных стратегий.
    
    Атрибуты:
        calls_per_second: Максимум запросов в секунду
        calls_per_minute: Максимум запросов в минуту
        burst_limit: Максимум запросов подряд
    """
    
    def __init__(
        self,
        calls_per_second: Optional[float] = None,
        calls_per_minute: Optional[int] = None,
        burst_limit: Optional[int] = None
    ):
        self.calls_per_second = calls_per_second
        self.calls_per_minute = calls_per_minute
        self.burst_limit = burst_limit
        
        self._lock = threading.Lock()
        self._second_timestamps = []
        self._minute_timestamps = []
        self._burst_count = 0
        self._last_burst_reset = time.time()
        
        self._logger = logging.getLogger(f"ratelimiter.{id(self)}")
    
    def wait(self) -> None:
        """Ожидание перед следующим запросом"""
        with self._lock:
            now = time.time()
            
            # Очистка старых записей
            self._cleanup(now)
            
            # Проверка лимита в секунду
            if self.calls_per_second:
                while len(self._second_timestamps) >= self.calls_per_second:
                    sleep_time = 1.0 - (now - self._second_timestamps[0])
                    if sleep_time > 0:
                        self._logger.debug(f"Rate limit: сон {sleep_time:.2f}с")
                        time.sleep(sleep_time)
                    now = time.time()
                    self._cleanup(now)
            
            # Проверка лимита в минуту
            if self.calls_per_minute:
                while len(self._minute_timestamps) >= self.calls_per_minute:
                    oldest = self._minute_timestamps[0]
                    sleep_time = 60.0 - (now - oldest)
                    if sleep_time > 0:
                        self._logger.debug(f"Rate limit (мин): сон {sleep_time:.2f}с")
                        time.sleep(sleep_time)
                    now = time.time()
                    self._cleanup(now)
            
            # Проверка burst лимита
            if self.burst_limit:
                if self._burst_count >= self.burst_limit:
                    sleep_time = 1.0 - (now - self._last_burst_reset)
                    if sleep_time > 0:
                        self._logger.debug(f"Burst limit: сон {sleep_time:.2f}с")
                        time.sleep(sleep_time)
                    self._burst_count = 0
                    self._last_burst_reset = time.time()
            
            # Запись текущего запроса
            self._second_timestamps.append(now)
            self._minute_timestamps.append(now)
            self._burst_count += 1
    
    def _cleanup(self, now: float) -> None:
        """Удаление старых записей"""
        # Очистка секундных записей (старше 1 секунды)
        self._second_timestamps = [
            ts for ts in self._second_timestamps
            if now - ts < 1.0
        ]
        
        # Очистка минутных записей (старше 60 секунд)
        self._minute_timestamps = [
            ts for ts in self._minute_timestamps
            if now - ts < 60.0
        ]
    
    def get_stats(self) -> dict:
        """Получение статистики"""
        with self._lock:
            now = time.time()
            self._cleanup(now)
            
            return {
                "requests_last_second": len(self._second_timestamps),
                "requests_last_minute": len(self._minute_timestamps),
                "burst_count": self._burst_count,
                "limits": {
                    "per_second": self.calls_per_second,
                    "per_minute": self.calls_per_minute,
                    "burst": self.burst_limit
                }
            }
    
    def reset(self) -> None:
        """Сброс счётчиков"""
        with self._lock:
            self._second_timestamps.clear()
            self._minute_timestamps.clear()
            self._burst_count = 0
            self._last_burst_reset = time.time()
            self._logger.info("Rate limiter сброшен")


class TokenBucketLimiter:
    """
    Rate Limiter на основе алгоритма Token Bucket.
    Более гибкая стратегия для burst-трафика.
    """
    
    def __init__(self, rate: float = 1.0, capacity: int = 10):
        """
        Args:
            rate: Скорость пополнения токенов в секунду
            capacity: Максимальное количество токенов
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()
        self._logger = logging.getLogger(f"tokenbucket.{id(self)}")
    
    def wait(self) -> None:
        """Ожидание доступности токена"""
        with self._lock:
            now = time.time()
            
            # Пополнение токенов
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Если нет токенов - ждём
            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                self._logger.debug(f"Token bucket: сон {sleep_time:.2f}с")
                time.sleep(sleep_time)
                self.tokens = 0
                self.last_update = time.time()
            else:
                self.tokens -= 1
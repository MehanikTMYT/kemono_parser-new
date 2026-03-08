"""
Вспомогательные функции.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def calculate_file_hash(filepath: str, algorithm: str = "sha256") -> Optional[str]:
    """
    Вычисление хэша файла.
    
    Args:
        filepath: Путь к файлу
        algorithm: Алгоритм хэширования
    
    Returns:
        Хэш строка или None при ошибке
    """
    try:
        hash_func = hashlib.new(algorithm)
        
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    except Exception as e:
        logger.error(f"Ошибка вычисления хэша {filepath}: {e}")
        return None


def format_size(size_bytes: int) -> str:
    """
    Форматирование размера файла.
    
    Args:
        size_bytes: Размер в байтах
    
    Returns:
        Человекочитаемый размер
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Очистка имени файла от недопустимых символов.
    
    Args:
        filename: Исходное имя
    
    Returns:
        Безопасное имя файла
    """
    # Замена недопустимых символов
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Удаление ведущих/конечных пробелов и точек
    sanitized = sanitized.strip(" .")
    # Ограничение длины
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized or "unnamed"


def parse_datetime(date_string: str) -> Optional[datetime]:
    """
    Парсинг строки даты.
    
    Args:
        date_string: Строка даты
    
    Returns:
        datetime объект или None
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Не удалось распарсить дату: {date_string}")
    return None


def ensure_directory(path: str) -> Path:
    """
    Создание директории если не существует.
    
    Args:
        path: Путь к директории
    
    Returns:
        Path объект
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезка строки до максимальной длины.
    
    Args:
        text: Исходная строка
        max_length: Максимальная длина
        suffix: Суффикс для обрезанной строки
    
    Returns:
        Обрезанная строка
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_urls(text: str) -> List[str]:
    """
    Извлечение URL из текста.
    
    Args:
        text: Текст для поиска
    
    Returns:
        Список URL
    """
    url_pattern = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        re.IGNORECASE
    )
    return url_pattern.findall(text)


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """
    Глубокое слияние словарей.
    
    Args:
        base: Базовый словарь
        override: Словарь для переопределения
    
    Returns:
        Слитый словарь
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def retry_decorator(max_attempts: int = 3, delay: float = 1.0):
    """
    Декоратор для повторных попыток.
    
    Args:
        max_attempts: Максимум попыток
        delay: Задержка между попытками
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Попытка {attempt + 1}/{max_attempts} не удалась: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator
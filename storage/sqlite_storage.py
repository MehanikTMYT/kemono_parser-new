"""
SQLite хранилище данных.
Реляционное хранение с поддержкой SQL запросов.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from storage.base_storage import BaseStorage
import json
import logging

logger = logging.getLogger(__name__)


class SQLiteStorage(BaseStorage):
    """Хранилище на основе SQLite"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.db_path = Path(config.get("path", "./data/parser.db"))
        self.table_name = config.get("table", "data")
        self._conn: Optional[sqlite3.Connection] = None
        self._cursor: Optional[sqlite3.Cursor] = None
    
    def connect(self) -> bool:
        """Подключение к базе"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()
            
            # Создание таблицы
            self._create_table()
            
            self._connected = True
            self._logger.info(f"SQLite Storage подключён: {self.db_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Ошибка подключения: {e}")
            return False
    
    def _create_table(self) -> None:
        """Создание таблицы"""
        self._cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()
    
    def disconnect(self) -> None:
        """Отключение"""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._cursor = None
        self._connected = False
        self._logger.info("SQLite Storage отключён")
    
    def save(self, key: str, data: Dict[str, Any]) -> bool:
        """Сохранение данных"""
        if not self._connected or not self._cursor:
            return False
        
        try:
            data_json = json.dumps(data, ensure_ascii=False)
            
            self._cursor.execute(f"""
                INSERT OR REPLACE INTO {self.table_name} (key, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, data_json))
            
            self._conn.commit()
            self._logger.debug(f"Данные сохранены: {key}")
            return True
            
        except Exception as e:
            self._logger.error(f"Ошибка сохранения {key}: {e}")
            self._conn.rollback()
            return False
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Загрузка данных"""
        if not self._connected or not self._cursor:
            return None
        
        try:
            self._cursor.execute(f"""
                SELECT data FROM {self.table_name} WHERE key = ?
            """, (key,))
            
            row = self._cursor.fetchone()
            
            if row:
                data = json.loads(row["data"])
                self._logger.debug(f"Данные загружены: {key}")
                return data
            
            return None
            
        except Exception as e:
            self._logger.error(f"Ошибка загрузки {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Удаление данных"""
        if not self._connected or not self._cursor:
            return False
        
        try:
            self._cursor.execute(f"""
                DELETE FROM {self.table_name} WHERE key = ?
            """, (key,))
            
            self._conn.commit()
            deleted = self._cursor.rowcount > 0
            
            if deleted:
                self._logger.debug(f"Данные удалены: {key}")
            
            return deleted
            
        except Exception as e:
            self._logger.error(f"Ошибка удаления {key}: {e}")
            self._conn.rollback()
            return False
    
    def exists(self, key: str) -> bool:
        """Проверка существования"""
        if not self._connected or not self._cursor:
            return False
        
        self._cursor.execute(f"""
            SELECT 1 FROM {self.table_name} WHERE key = ?
        """, (key,))
        
        return self._cursor.fetchone() is not None
    
    def list_keys(self, pattern: str = "%") -> List[str]:
        """Список ключей"""
        if not self._connected or not self._cursor:
            return []
        
        # Замена * на % для SQL LIKE
        sql_pattern = pattern.replace("*", "%")
        
        self._cursor.execute(f"""
            SELECT key FROM {self.table_name} WHERE key LIKE ?
        """, (sql_pattern,))
        
        return [row["key"] for row in self._cursor.fetchall()]
    
    def query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """Выполнение SQL запроса"""
        if not self._connected or not self._cursor:
            return []
        
        try:
            self._cursor.execute(sql, params)
            return [dict(row) for row in self._cursor.fetchall()]
        except Exception as e:
            self._logger.error(f"Ошибка запроса: {e}")
            return []
    
    def get_count(self) -> int:
        """Количество записей"""
        result = self.query(f"SELECT COUNT(*) as count FROM {self.table_name}")
        return result[0]["count"] if result else 0
    
    def clear(self) -> bool:
        """Очистка таблицы"""
        if not self._connected or not self._cursor:
            return False
        
        try:
            self._cursor.execute(f"DELETE FROM {self.table_name}")
            self._conn.commit()
            self._logger.info("Таблица очищена")
            return True
        except Exception as e:
            self._logger.error(f"Ошибка очистки: {e}")
            return False
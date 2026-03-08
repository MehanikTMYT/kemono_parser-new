"""
Тесты для хранилищ данных.
"""

import pytest
from pathlib import Path
from storage.json_storage import JSONStorage
from storage.sqlite_storage import SQLiteStorage


class TestJSONStorage:
    """Тесты JSON хранилища"""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Создание хранилища"""
        config = {"path": str(tmp_path / "json_data")}
        storage = JSONStorage(config)
        storage.connect()
        yield storage
        storage.disconnect()
    
    def test_save_load(self, storage):
        """Сохранение и загрузка"""
        data = {"key": "value", "number": 42}
        assert storage.save("test_key", data) == True
        
        loaded = storage.load("test_key")
        assert loaded["key"] == "value"
        assert loaded["number"] == 42
    
    def test_delete(self, storage):
        """Удаление"""
        storage.save("to_delete", {"data": "test"})
        assert storage.exists("to_delete") == True
        
        storage.delete("to_delete")
        assert storage.exists("to_delete") == False
    
    def test_exists(self, storage):
        """Проверка существования"""
        assert storage.exists("nonexistent") == False
        storage.save("existent", {})
        assert storage.exists("existent") == True
    
    def test_list_keys(self, storage):
        """Список ключей"""
        storage.save("key1", {})
        storage.save("key2", {})
        storage.save("other", {})
        
        keys = storage.list_keys("key*")
        assert len(keys) == 2


class TestSQLiteStorage:
    """Тесты SQLite хранилища"""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Создание хранилища"""
        config = {"path": str(tmp_path / "test.db")}
        storage = SQLiteStorage(config)
        storage.connect()
        yield storage
        storage.disconnect()
    
    def test_save_load(self, storage):
        """Сохранение и загрузка"""
        data = {"name": "test", "value": 123}
        assert storage.save("test_key", data) == True
        
        loaded = storage.load("test_key")
        assert loaded["name"] == "test"
        assert loaded["value"] == 123
    
    def test_delete(self, storage):
        """Удаление"""
        storage.save("to_delete", {"data": "test"})
        assert storage.exists("to_delete") == True
        
        storage.delete("to_delete")
        assert storage.exists("to_delete") == False
    
    def test_query(self, storage):
        """SQL запрос"""
        storage.save("key1", {"type": "a"})
        storage.save("key2", {"type": "b"})
        
        # Прямой SQL запрос
        results = storage.query("SELECT key FROM data WHERE key LIKE ?", ("key%",))
        assert len(results) == 2
    
    def test_get_count(self, storage):
        """Количество записей"""
        assert storage.get_count() == 0
        
        storage.save("k1", {})
        storage.save("k2", {})
        
        assert storage.get_count() == 2
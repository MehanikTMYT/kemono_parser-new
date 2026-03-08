"""
Тесты для API клиента.
"""

import pytest
from unittest.mock import Mock, patch
from api.kemono_client import KemonoClient
from api.rate_limiter import RateLimiter


class TestRateLimiter:
    """Тесты Rate Limiter"""
    
    def test_rate_limiter_init(self):
        """Инициализация rate limiter"""
        limiter = RateLimiter(calls_per_second=2)
        assert limiter.calls_per_second == 2
    
    def test_rate_limiter_wait(self):
        """Проверка ожидания"""
        limiter = RateLimiter(calls_per_second=10)
        # Не должно вызывать исключений
        limiter.wait()
    
    def test_rate_limiter_stats(self):
        """Проверка статистики"""
        limiter = RateLimiter(calls_per_second=5)
        limiter.wait()
        stats = limiter.get_stats()
        assert "requests_last_second" in stats
        assert "requests_last_minute" in stats
    
    def test_rate_limiter_reset(self):
        """Сброс rate limiter"""
        limiter = RateLimiter(calls_per_second=5)
        limiter.wait()
        limiter.reset()
        stats = limiter.get_stats()
        assert stats["requests_last_second"] == 0


class TestKemonoClient:
    """Тесты Kemono API клиента"""
    
    @pytest.fixture
    def client(self):
        """Создание клиента для тестов"""
        return KemonoClient(service="kemono", rate_limit=60)
    
    def test_client_init(self, client):
        """Инициализация клиента"""
        assert client.service == "kemono"
        assert "kemono.cr" in client.base_url
    
    @patch("requests.Session.get")
    def test_get_creators_list(self, mock_get, client):
        """Получение списка создателей"""
        mock_response = Mock()
        mock_response.text = "creator1\ncreator2\ncreator3"
        mock_get.return_value = mock_response
        
        creators = client.get_creators_list()
        assert len(creators) == 3
        assert "creator1" in creators
    
    def test_search_creator_empty(self, client):
        """Поиск создателя (пустой результат)"""
        # Без мока - реальный запрос (может вернуть пустоту)
        results = client.search_creator("nonexistent_creator_xyz")
        assert isinstance(results, list)
    
    def test_client_close(self, client):
        """Закрытие клиента"""
        client.close()
        # Не должно вызывать исключений
"""
Конфигурация pytest.
Фикстуры для тестов.
"""

import pytest
import os
import sys
from pathlib import Path

# Добавление корня проекта в path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_dir():
    """Путь к корню проекта"""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir():
    """Путь к тестовым данным"""
    test_dir = project_root / "tests" / "data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def sample_post_data():
    """Пример данных поста"""
    return {
        "id": "12345",
        "title": "Test Post",
        "content": "Test content with https://dropbox.com/file.zip link",
        "published": "2024-01-01T00:00:00Z",
        "attachments": [
            {
                "name": "file1.zip",
                "path": "https://kemono.cr/files/file1.zip",
                "file_hash": "abc123"
            }
        ],
        "user": {"name": "TestCreator"}
    }


@pytest.fixture
def sample_creator_data():
    """Пример данных создателя"""
    return {
        "creator_id": "test_creator",
        "service": "patreon",
        "name": "Test Creator",
        "url": "https://kemono.cr/patreon/user/test_creator"
    }


@pytest.fixture
def temp_config_file(tmp_path):
    """Временный файл конфигурации"""
    config_content = """
app:
  name: "Test App"
  debug: true

api:
  rate_limit: 60
  timeout: 10

modules:
  file_downloader:
    download_dir: "./test_downloads"
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Очистка тестовых файлов после тестов"""
    yield
    # Очистка может быть добавлена здесь
    pass


@pytest.fixture
def mock_requests_response():
    """Мок для requests response"""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)
        
        def json(self):
            return self._json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")
    
    return MockResponse
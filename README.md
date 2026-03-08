# Kemono Parser

Модульный парсер для Kemono/Coomer API с поддержкой расширения через плагины.

## 🚀 Возможности

- ✅ Поиск артистов по имени
- ✅ Парсинг всех постов создателя
- ✅ Извлечение файлов и внешних ссылок
- ✅ Проверка IP и работа через прокси
- ✅ Модульная архитектура
- ✅ SQLite и JSON хранилища
- ✅ CLI интерфейс
- ✅ Rate limiting для защиты от блокировок

## 📦 Установка

### Быстрая установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd kemono_parser

# Установка зависимостей
pip install -e ".[dev]"

# Или минимальная установка
pip install -e .
```

### Требования

- Python 3.8+
- pip
- (Опционально) playwright для расширенной функциональности

## 🔧 Настройка

### 1. Конфигурационный файл

Отредактируйте `config/config.yaml`:

```yaml
api:
  session_cookie: null  # Вставьте ваш session cookie
  
modules:
  proxy_manager:
    proxy_url: null  # Например: "http://proxy:port" или "socks5://proxy:port"
  
downloads:
  base_dir: "./downloads"
  organize_by: "creator"
```

### 2. Переменные окружения (опционально)

Создайте `.env` файл:

```bash
KP_SESSION_COOKIE=your_session_value
KP_PROXY_URL=http://proxy:port
KP_DOWNLOAD_DIR=./downloads
KP_LOG_LEVEL=INFO
KP_DEBUG=false
```

## 🔍 Как получить Session Cookie

1. Откройте браузер (Chrome/Firefox/Edge)
2. Зайдите на https://kemono.cr
3. Войдите в аккаунт (если нет - зарегистрируйтесь)
4. Откройте DevTools (F12)
5. Перейдите в **Application** → **Cookies** → **https://kemono.cr**
6. Найдите cookie с именем `session` и скопируйте значение
7. Вставьте в `config/config.yaml` или `.env`

## 💡 Использование

### CLI (Командная строка)

```bash
# Скачать контент артиста
kemono-parser download "ArtistName" --service patreon

# Скачать с указанием конфигурации
kemono-parser --config config/custom.yaml download "ArtistName" --service fanbox

# Список активных модулей
kemono-parser modules

# Получить помощь
kemono-parser --help
kemono-parser download --help
```

### Python API

```python
from core.app import KemonoParserApp

# Инициализация приложения
app = KemonoParserApp(config_path="config/config.yaml")
app.initialize()

# Скачивание контента артиста
result = app.run_artist_download("ArtistName", service="patreon")
print(f"Найдено постов: {result['posts_count']}")
print(f"Скачано файлов: {result['files_downloaded']}")

# Завершение работы
app.shutdown()
```

### Прямое использование API клиента

```python
from api.kemono_client import KemonoClient

client = KemonoClient(
    service="kemono",
    rate_limit=30,
    timeout=30,
    session_cookie="your_session_cookie"
)

# Поиск артиста
artists = client.search_creator("ArtistName", service="patreon")
for artist in artists:
    print(f"Найден: {artist['name']} (ID: {artist['creator_id']})")

# Получение постов
posts = client.get_all_creator_posts("patreon", "creator_id")
print(f"Всего постов: {len(posts)}")

# Закрытие соединения
client.close()
```

## 📁 Структура проекта

```
kemono_parser/
├── api/                 # API клиенты и rate limiter
│   ├── base_client.py
│   ├── kemono_client.py
│   └── rate_limiter.py
├── cli/                 # CLI интерфейс
│   └── commands.py
├── config/              # Конфигурация
│   ├── config.yaml
│   └── settings.py
├── core/                # Ядро системы
│   ├── app.py
│   ├── events.py
│   └── registry.py
├── downloaders/         # Загрузчики файлов
│   ├── dropbox_downloader.py
│   └── http_downloader.py
├── modules/             # Модули (плагины)
│   ├── api_client/
│   ├── artist_search/
│   ├── file_downloader/
│   ├── ip_checker/
│   ├── post_parser/
│   └── proxy_manager/
├── storage/             # Хранилища данных
│   ├── database.py
│   ├── json_storage.py
│   └── sqlite_storage.py
├── tests/               # Тесты
│   ├── test_api.py
│   ├── test_modules.py
│   └── test_storage.py
└── utils/               # Утилиты
    ├── helpers.py
    ├── logger.py
    └── validators.py
```

## 🔌 Создание собственного модуля

```python
from modules.base_module import BaseModule, ModuleState

class MyCustomModule(BaseModule):
    name = "my_custom_module"
    version = "1.0.0"
    description = "Мой кастомный модуль"
    dependencies = ["api_client"]  # Зависимости от других модулей
    
    def initialize(self) -> bool:
        """Инициализация модуля"""
        # Проверка конфигурации
        if not self.validate_config():
            self._set_state(ModuleState.ERROR)
            return False
        
        self._set_state(ModuleState.READY)
        return True
    
    def execute(self, **kwargs):
        """Основная логика модуля"""
        self._logger.info("Выполнение модуля...")
        # Ваша логика здесь
        return {"status": "success", "data": kwargs}
    
    def shutdown(self) -> None:
        """Очистка ресурсов"""
        super().shutdown()
        # Дополнительная очистка
```

### Регистрация модуля

Добавьте модуль в `core/app.py`:

```python
def register_default_modules(self) -> None:
    from modules.my_custom_module import MyCustomModule
    self.registry.register_class(MyCustomModule)
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С покрытием кода
pytest tests/ -v --cov=. --cov-report=html

# Конкретный файл тестов
pytest tests/test_api.py -v

# Конкретный тест
pytest tests/test_api.py::TestKemonoClient::test_client_init -v
```

### На что обратить внимание при тестировании

1. **Rate Limiter**:
   - Проверка корректного ожидания между запросами
   - Тестирование различных лимитов (в секунду, в минуту, burst)
   - Статистика запросов

2. **API Клиент**:
   - Обработка ошибок сети
   - Работа с session cookie
   - Поиск артистов (с моками и реальные запросы)
   - Обработка 429 (Too Many Requests) ответов

3. **Хранилища**:
   - Сохранение/загрузка данных
   - Работа с большими объемами данных
   - Целостность данных после перезапуска

4. **Модули**:
   - Корректность состояний (UNINITIALIZED → READY → RUNNING → ERROR)
   - Зависимости между модулями
   - Изоляция ошибок

5. **Интеграционные тесты**:
   - Полный цикл скачивания
   - Работа с прокси
   - Проверка скачанных файлов

## ⚙️ Конфигурация

### Основные параметры

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `api.rate_limit` | Лимит запросов в секунду | 30 |
| `api.timeout` | Таймаут запроса (сек) | 30 |
| `api.retry_count` | Количество попыток | 3 |
| `downloads.base_dir` | Папка загрузок | `./downloads` |
| `downloads.max_concurrent` | Макс. параллельных загрузок | 3 |
| `storage.type` | Тип хранилища | `sqlite` |

## ⚠️ Предупреждения

- **Соблюдайте авторские права** - используйте только для личного ознакомления
- **Уважайте rate limits** - не превышайте лимиты API
- **Используйте прокси** - если находитесь в регионе с ограничениями
- **Использование на ваш страх и риск**

## 🐛 Решение проблем

### Ошибка аутентификации
Проверьте session cookie в конфиге

### Слишком много запросов (429)
Увеличьте `api.rate_limit` или включите прокси

### Таймауты
Увеличьте `api.timeout` в конфиге

### Проблемы с прокси
Проверьте формат: `http://host:port` или `socks5://host:port`

## 📄 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request



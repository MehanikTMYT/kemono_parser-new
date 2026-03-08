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

## 📦 Установка

```bash
# Клонирование
git clone 
cd kemono_parser

# Установка зависимостей
pip install -r requirements.txt

# Или через pip
pip install -e .
```

🔧 Настройка
Скопируйте .env.example в .env
Отредактируйте config/config.yaml
Настройте прокси если находитесь в РФ

💡 Использование
CLI
```bash
# Скачать контент артиста
kemono-parser download "NebulaMaps" --service patreon

# Список модулей
kemono-parser modules

# Помощь
kemono-parser --help
```

🔍 Как получить Session Cookie

Откройте браузер (Chrome/Firefox/Edge)
Зайдите на https://kemono.cr
Войдите в аккаунт (если нет - зарегистрируйтесь)
Откройте DevTools (F12)
Перейдите в Application → Cookies → https://kemono.cr
Найдите session и скопируйте значение
Вставьте в .env или config/config.yaml

Python API

from core.app import KemonoParserApp

app = KemonoParserApp()
app.initialize()

result = app.run_artist_download("NebulaMaps", service="patreon")
print(result)

app.shutdown()

📁 Структура

kemono_parser/
├── api/           # API клиенты
├── config/        # Конфигурация
├── core/          # Ядро системы
├── modules/       # Модули (плагины)
├── storage/       # Хранилища данных
├── utils/         # Утилиты
├── cli/           # CLI интерфейс
└── tests/         # Тесты

🔌 Создание модуля
```python
from modules.base_module import BaseModule, ModuleState

class MyModule(BaseModule):
    name = "my_module"
    version = "1.0.0"
    description = "Описание"
    dependencies = []
    
    def initialize(self) -> bool:
        self._set_state(ModuleState.READY)
        return True
    
    def execute(self, **kwargs):
        return {"result": "ok"}
```

⚠️ Предупреждения
Соблюдайте авторские права
Уважайте rate limits API
Использование на ваш страх и риск

📄 Лицензия
MIT License



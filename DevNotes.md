## Виртуальное окружение

### Создать виртуальное окружение
```bash
python -m venv .venv
```

### Активация виртуального окружения
```bash
.venv\Scripts\activate
```

### Установить зависимость и добавить в requirements
```bash
pip install <package_name>
pip freeze > requirements.txt
```

### Установить зависимости из requirements.txt
```bash
pip install -r requirements.txt
```

## Запуск бота

### Установить переменные окружения
Создайте файл `.env` на основе `.env.example` и укажите токен бота:
```bash
cp .env.example .env
# Редактируйте .env и добавьте ваш токен от @BotFather
```

### Запустить бота
```bash
python src/main.py
```

## Структура проекта

```
book-shelf/
├── .env.example               # Пример файла окружения
├── .gitignore                 # Игнорируемые файлы
├── .venv/                     # Виртуальное окружение
├── data/                      # Данные (JSON файлы)
├── src/                       # Исходный код
│   ├── main.py                # Точка входа
│   ├── bot/                   # Telegram-бот
│   │   ├── __init__.py
│   │   ├── bot.py             # Основной класс бота
│   │   ├── handlers/          # Обработчики
│   │   │   ├── __init__.py
│   │   │   ├── commands.py    # Обработчики команд
│   │   │   ├── messages.py    # Обработчики сообщений
│   │   │   └── callbacks.py   # Обработчики callback-queries
│   │   └── keyboards/         # Клавиатуры
│   │       ├── __init__.py
│   │       └── main.py        # Основные клавиатуры
│   │
│   ├── core/                  # Ядро приложения
│   │   ├── __init__.py
│   │   ├── models.py          # Модели данных
│   │   ├── repository.py      # Работа с данными
│   │   └── services.py        # Бизнес-логика
│   │
│   └── utils/                 # Утилиты
│       ├── __init__.py
│       ├── config.py          # Конфигурация
│       ├── logger.py          # Логирование
│       └── helpers.py         # Вспомогательные функции
│
├── tests/                     # Тесты
├── requirements.txt           # Зависимости
└── README.md                  # Документация
```

## Основные команды бота

- `/start` - Начало работы
- `/help` - Помощь
- `/add` - Добавить новую книгу
- `/list` - Показать список книг
- `/stats` - Статистика чтения
- `/export` - Экспортировать библиотеку

## Технологический стек

- Python 3.8+
- python-telegram-bot 20.0+
- Pydantic 2.0+
- JSON для хранения данных

## Разработка

### Форматирование кода
```bash
black src/
isort src/
```

### Линтинг
```bash
flake8 src/
```

### Тестирование
```bash
pytest tests/
```

## Дополнительные настройки

### Настройка токена бота
1. Создайте бота у @BotFather в Telegram
2. Скопируйте токен
3. Добавьте его в файл `.env`:
   ```
   BOT_TOKEN=your_bot_token_here
   ```

### Настройка хранения данных
По умолчанию данные сохраняются в JSON файлы в директории `data/`. Вы можете изменить директорию, установив переменную `DATA_DIR` в файле `.env`.

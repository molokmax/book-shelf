# Book shelf
Персональный трекер чтения и менеджер книг

Приложение для управления вашим списком книг. Помогает систематизировать чтение, отслеживать прогресс и не забывать о книгах, которые вы планируете прочесть.

## Ключевые возможности:

- **Библиотека**: Добавляйте книги (название, автор, жанр, обложка).
- **Управление статусами**: Легко переводите книги между статусами: Хочу прочитать, Читаю сейчас, Прочитано, Отложено.
- **Приоритеты**: Устанавливайте приоритет чтения (например, Высокий, Средний, Низкий) для планирования.
- **Прогресс**: Отмечайте текущую страницу или процент прочтения.
- **Напоминания**: Гибкая система напоминаний (например, "Читать каждый день в 20:00").
- **Статистика и аналитика**: Визуализация ваших читательских привычек: книг в месяц, прочитанных страниц и т.д.
- **Экспорт данных**: Возможность сохранить вашу библиотеку в CSV‑файл через кнопку «Экспорт CSV» в разделе помощи.
- **Команда `/edit`**: Позволяет выбирать режим фильтрации (по статусу, по тегу, все) и редактировать выбранную книгу.
- **Новая команда `/details`**: Позволяет пользователям просмотреть полную информацию о выбранной книге, включая название, автора, теги, статус, количество страниц, прочитанные страницы, даты и ссылку.

## Технологический стек:
- Python 3.8+
- vk_api 11.10+
- Pydantic 2.0+
- SQLite для хранения данных

Для кого это: Для всех, кто любит читать и хочет привести свой reading list в порядок.

## Архитектура

- **src/vk_bot/command_router.py** — `CommandRouter` — центральный роутер команд, регистрирует обработчики с приоритетами и маршрутизирует команды к подходящему.
- **src/vk_bot/handlers/base.py** — `AbstractCommandHandler` — базовый класс для обработчиков с поддержкой `can_handle`, `priority`, `commands`.
- **src/vk_bot/handlers/*_handler.py** — Конкретные обработчики (`AddHandler`, `EditHandler`, `ListHandler`, `DetailsHandler`), наследующие `AbstractCommandHandler`.
- **src/vk_bot/repository/user_state.py** — `UserStateRepository` — хранилище состояния пользователя в SQLite (таблица `user_state`).
- **src/vk_bot/bot.py** — `VkBookShelfBot` — инициализирует `CommandRouter`, регистрирует обработчики и обрабатывает события VK.

## Запуск через Docker

Сборка образа:

```bash
docker build -t book-shelf .
```

Запуск через Docker Compose (использует `.env` с `BOT_TOKEN`):

```bash
docker compose up -d
docker compose logs -f
docker compose down
```

Данные SQLite хранятся в named volume `book-shelf-data`, смонтированном в `/app/data`. Образ исключает `.env` и каталог `data/` из контекста сборки, поэтому токен и база не попадают в слои образа.

Перенос существующей базы данных при переходе с systemd-деплоя:

```bash
systemctl --user stop book-shelf
docker compose up -d
docker cp data/database.db book-shelf:/app/data/database.db
docker compose restart
```

Откат на systemd:

```bash
docker cp book-shelf:/app/data/database.db data/database.db   # вернуть актуальные данные на хост
docker compose down
systemctl --user start book-shelf
```

Пошаговая инструкция по запуску на VPS: [docs/DEPLOY.md](./docs/DEPLOY.md).

## Публикация образа

Workflow `.github/workflows/docker-publish.yml` собирает образ и публикует его в Docker Hub при пуше тега вида `v*`.

Требуемые секреты репозитория (Settings → Secrets and variables → Actions):

- `DOCKERHUB_USERNAME` — логин Docker Hub (он же namespace образа).
- `DOCKERHUB_TOKEN` — access token Docker Hub (не пароль).

Выпуск версии:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

После завершения workflow в Docker Hub появится образ `<DOCKERHUB_USERNAME>/book-shelf` с тегами `X.Y.Z`, `X.Y` и `latest`. Тег `latest` обновляется только для стабильных версий (без суффикса pre-release). Допустим и сокращённый тег вида `vX.Y` — образ получит теги `X.Y` и `latest`.

Использование опубликованного образа:

```bash
docker pull <DOCKERHUB_USERNAME>/book-shelf:latest
docker run -d --name book-shelf --env-file .env \
  -v book-shelf-data:/app/data --restart unless-stopped \
  <DOCKERHUB_USERNAME>/book-shelf:latest
```

[Dev Notes](./DevNotes.md)

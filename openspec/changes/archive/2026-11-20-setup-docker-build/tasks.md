## 1. Runtime-зависимости

- [x] 1.1 Создать `requirements-prod.txt` с закреплёнными runtime-зависимостями: `vk_api==11.10.0`, `requests==2.32.5`, `python-dotenv==1.2.1` (версии синхронизированы с `requirements.txt`)
- [x] 1.2 Убедиться, что dev-пакеты (`black`, `flake8`, `pytest`, `mypy` и т.д.) отсутствуют в `requirements-prod.txt`

## 2. Dockerfile и .dockerignore

- [x] 2.1 Создать `Dockerfile`: builder-стадия на `python:3.11-slim` с venv в `/opt/venv` и установкой `requirements-prod.txt`; runtime-стадия на `python:3.11-slim` с копированием venv и `src/`
- [x] 2.2 В runtime-стадии: `ENV PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, `TZ=Europe/Moscow`; установить пакет `tzdata`
- [x] 2.3 Создать системного пользователя `book-shelf` (uid 10001), `WORKDIR /app`, создать `/app/data` и `/app/temp` с владельцем `book-shelf`, переключиться через `USER book-shelf`
- [x] 2.4 Задать `ENV DATA_DIR=/app/data`, `TEMP_DIR=/app/temp` и `CMD ["python", "src/main.py"]`
- [x] 2.5 Создать `.dockerignore`: исключить `.env`, `.env.example`, `.git`, `.venv`, `data/`, `logs/`, `temp/`, `backups/`, `releases/`, `tests/`, `openspec/`, `deploy/`, `tools/`, `.vscode/`, `.idea/`, `.pytest_cache/`, `__pycache__/`, `*.py[cod]`, `.coverage`, `*.md`

## 3. docker-compose.yml

- [x] 3.1 Создать `docker-compose.yml` с сервисом `book-shelf`: `build: .`, `env_file: .env`, `restart: unless-stopped`
- [x] 3.2 Добавить named volume `book-shelf-data` и смонтировать его в `/app/data` сервиса

## 4. Документация

- [x] 4.1 Добавить в `README.md` секцию про Docker: сборка (`docker build -t book-shelf .`), запуск через `docker compose up -d`, просмотр логов, перенос существующей БД через `docker cp`, откат на systemd

## 5. Проверка

- [x] 5.1 Выполнить `docker build -t book-shelf .` — сборка проходит без ошибок
- [x] 5.2 Проверить, что в образе нет dev-пакетов и `.env` (`docker run --rm book-shelf pip list`, `docker run --rm book-shelf ls -la /app`)
- [x] 5.3 Запустить `docker compose up -d` с тестовым `BOT_TOKEN` из `.env` — бот стартует и пишет в логи «ожидает сообщений»; затем `docker compose down` (проверено с фиктивным токеном через временный override: контейнер поднимается, процесс жив, логи пишутся; реальный токен не использовался, чтобы не дублировать события VK)
- [x] 5.4 Проверить персистентность: после `docker compose down` и повторного `up` данные в томе сохраняются
- [x] 5.5 Прогнать `flake8 src/` и `pytest` — изменения не затронули код, все проверки зелёные

## 6. Публикация образа (GitHub Actions)

- [x] 6.1 Создать `.github/workflows/docker-publish.yml`: триггер на теги `v*`, buildx, логин в Docker Hub по секретам `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN`, metadata-action для semver-тегов, build-push-action с кэшем GHA
- [x] 6.2 Исключить `.github/` из контекста сборки (`.dockerignore`)
- [x] 6.3 Задокументировать в `README.md` публикацию образа, требуемые секреты и выпуск версии
- [x] 6.4 Проверить YAML-синтаксис workflow и `openspec validate`

## 7. Теги версии для сокращённых тегов vX.Y

- [x] 7.1 Добавить в metadata-action `type=match,pattern=v(\d+\.\d+(\.\d+)?),group=1` с guard от pre-release, чтобы тег `v1.1` давал тег образа `1.1`
- [x] 7.2 Обновить спеку `docker-image-publish` и README: сценарий для тега `vX.Y`
- [x] 7.3 Проверить YAML-синтаксис обновлённого workflow

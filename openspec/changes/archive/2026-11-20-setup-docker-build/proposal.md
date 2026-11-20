## Why

Сейчас бот деплоится вручную: на сервере создаётся venv, ставится `requirements.txt` целиком (включая dev-зависимости) и запускается через systemd-юнит. Сборка не воспроизводима, перенос на другой сервер требует повторной ручной настройки окружения, а dev-пакеты попадают в прод. Docker-образ решает это одним воспроизводимым артефактом. Отдельно нужен версионированный артефакт для релизов и откатов, поэтому образ должен публиковаться в registry по тегам.

## What Changes

- Добавляется многоступенчатый `Dockerfile` на базе `python:3.11-slim`: сборка зависимостей и запуск бота от непривилегированного пользователя.
- Добавляется `requirements-prod.txt` с runtime-зависимостями (`vk_api`, `requests`, `python-dotenv`) для установки в образ; `requirements.txt` остаётся для разработки и тестов.
- Добавляется `.dockerignore`, исключающий `.env`, `data/`, `logs/`, `temp/`, `releases/`, `tests/`, venv и служебные каталоги из контекста сборки.
- Добавляется `docker-compose.yml` для локального и серверного запуска: проброс `BOT_TOKEN` и остальных переменных из окружения, том для `DATA_DIR`, политика `restart: unless-stopped`.
- Добавляется GitHub Actions workflow, который по пушу тега `v*` собирает образ и публикует его в Docker Hub (`<DOCKERHUB_USERNAME>/book-shelf`) с тегами версии и `latest`.
- Обновляется `README.md`: секции сборки/запуска через Docker и публикации образа.
- Существующий systemd-деплой (`deploy/`) не затрагивается и остаётся рабочим вариантом.

## Capabilities

### New Capabilities

- `docker-image-build`: сборка Docker-образа бота и его запуск контейнером с сохранением данных в томе.
- `docker-image-publish`: публикация собранного образа в Docker Hub по тегам `v*` через GitHub Actions.

### Modified Capabilities

<!-- Нет изменяемых существующих capability на уровне spec. -->

## Impact

- Новые файлы: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `requirements-prod.txt` (в корне репозитория), `.github/workflows/docker-publish.yml`.
- `README.md` — инструкции по Docker-запуску и публикации образа.
- Для публикации требуются секреты репозитория `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`.
- Код `src/` не меняется; переменные окружения (`BOT_TOKEN`, `DATA_DIR`, `TEMP_DIR`, `DEBUG`) используются как есть.
- Тесты не затрагиваются; `requirements.txt` и `pyproject.toml` остаются без изменений.

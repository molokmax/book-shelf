# syntax=docker/dockerfile:1

# --- Стадия сборки зависимостей ---
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Ставим prod-зависимости в изолированное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-prod.txt ./
RUN pip install -r requirements-prod.txt

# --- Стадия выполнения ---
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Moscow

# tzdata нужен для корректных локальных дат в статистике чтения
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin book-shelf

# Переносим готовое окружение из builder-стадии
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY src ./src

ENV DATA_DIR=/app/data \
    TEMP_DIR=/app/temp

# Каталоги для данных, временных файлов и логов с правами рабочего пользователя
RUN mkdir -p /app/data /app/temp /app/logs \
    && chown -R book-shelf:book-shelf /app

USER book-shelf

CMD ["python", "src/main.py"]

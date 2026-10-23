#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

IMAGE="molokmax/book-shelf"
CONTAINER="book-shelf"
VOLUME="book-shelf-data"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Передай 1 в качестве аргумента, чтобы завершиться с кодом ошибки
usage() {
    cat <<EOF
Использование: $0 <тег> [-h|--help]

Аргументы:
  <тег>         Тег образа Docker, например v1.2.0

Опции:
  -h, --help    Показать эту справку

Примеры:
  $0 v1.2.0
EOF
    exit "${1:-0}"
}

if [[ $# -lt 1 ]]; then
    log_error "Тег образа не передан"
    usage 1
fi

case "$1" in
    -h|--help) usage 0 ;;
esac

TAG="$1"
FULL_IMAGE="$IMAGE:$TAG"

# Проверяю, что Docker установлен
if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker не найден. Установи Docker и повтори запуск."
    exit 1
fi

# Проверяю, что Docker-демон доступен
if ! docker info >/dev/null 2>&1; then
    log_error "Docker-демон недоступен. Проверь, что Docker запущен."
    exit 1
fi

# Проверяю наличие .env в корне проекта
if [[ ! -f "$ENV_FILE" ]]; then
    log_error "Файл $ENV_FILE не найден."
    exit 1
fi

# Пересоздаю контейнер, если он уже есть. Данные сохраняются в volume.
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    log_warn "Контейнер $CONTAINER уже существует, пересоздаю..."
    docker rm -f "$CONTAINER" >/dev/null
fi

log_info "Запускаю $FULL_IMAGE..."
docker run -d \
    --name "$CONTAINER" \
    --env-file "$ENV_FILE" \
    -v "$VOLUME:/app/data" \
    --restart unless-stopped \
    "$FULL_IMAGE"

log_info "Контейнер запущен:"
docker ps --filter "name=^$CONTAINER$" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
DEFAULT_CONFIG="$PROJECT_DIR/tools/.servers.csv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat <<EOF
Использование: $0 [--config <путь>] [--output <путь>]

Опции:
  --config <путь>   Путь к CSV-файлу конфигурации (по умолчанию: $DEFAULT_CONFIG)
  --output <путь>   Путь для сохранения бекапа (по умолчанию: $BACKUP_DIR)
  -h, --help        Показать эту справку

Формат CSV (колонки container и backup_enabled необязательны):
  server,host,user,ssh_key_path,app_dir,service_name,db_path,container,backup_enabled

Если container задан, бекап создаётся внутри Docker-контейнера через
sqlite backup API: db_path — путь к базе внутри контейнера
(например, /app/data/database.db).

Если container пуст, бекап создаётся на хосте утилитой sqlite3:
db_path — путь к файлу базы на хосте.

Если backup_enabled задан как 0, no, false или off — строка пропускается,
бекап с этого сервера не делается. Пустое значение = бекап включён.

Примеры:
  # Docker-деплой
  vps,example.com,root,/home/user/.ssh/id_rsa,,book-shelf,/app/data/database.db,book-shelf,1
  # systemd-деплой
  vps,example.com,root,/home/user/.ssh/id_rsa,/home/user/book-shelf,book-shelf,/home/user/book-shelf/data/database.db,
  # бекап отключён
  old-vps,example.com,root,/home/user/.ssh/id_rsa,/home/user/book-shelf,book-shelf,/home/user/book-shelf/data/database.db,,0
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)     CONFIG="$2"; shift 2 ;;
        --output)     OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)    usage ;;
        *)            log_error "Неизвестный аргумент: $1"; usage ;;
    esac
done

CONFIG="${CONFIG:-$DEFAULT_CONFIG}"
OUTPUT_DIR="${OUTPUT_DIR:-$BACKUP_DIR}"

if [[ ! -f "$CONFIG" ]]; then
    log_error "Файл конфигурации не найден: $CONFIG"
    log_info "Создай файл в формате: server,host,user,ssh_key_path,app_dir,service_name,db_path,container,backup_enabled"
    exit 1
fi

CSV_CONTENT=$(grep -v '^#' "$CONFIG" | grep -v '^$' | tail -n +2)

if [[ -z "$CSV_CONTENT" ]]; then
    log_error "В файле конфигурации нет записей (строк с данными)."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

BACKUP_EXIT_CODE=0

while IFS=',' read -r SERVER_NAME HOST USER SSH_KEY _ _ DB_PATH CONTAINER BACKUP_ENABLED; do
    SERVER_NAME="${SERVER_NAME// /}"
    HOST="${HOST// /}"
    USER="${USER// /}"
    SSH_KEY="${SSH_KEY// /}"
    DB_PATH="${DB_PATH// /}"
    CONTAINER="${CONTAINER// /}"
    BACKUP_ENABLED="${BACKUP_ENABLED// /}"

    # Пропускаем серверы, для которых бекап отключён в конфиге
    BACKUP_ENABLED_LOWER=$(echo "$BACKUP_ENABLED" | tr '[:upper:]' '[:lower:]')
    if [[ "$BACKUP_ENABLED_LOWER" == "0" || "$BACKUP_ENABLED_LOWER" == "no" || "$BACKUP_ENABLED_LOWER" == "false" || "$BACKUP_ENABLED_LOWER" == "off" ]]; then
        log_info "Сервер $SERVER_NAME: бекап отключён в конфиге, пропускаю"
        continue
    fi

    if [[ -z "$HOST" || -z "$USER" || -z "$SSH_KEY" || -z "$DB_PATH" ]]; then
        log_warn "Пропускаю строку с пустыми полями: $HOST, $USER, $SSH_KEY, $DB_PATH"
        continue
    fi

    log_info "Подключаюсь к $USER@$HOST..."

    if [[ ! -f "$SSH_KEY" ]]; then
        log_error "SSH-ключ не найден: $SSH_KEY"
        BACKUP_EXIT_CODE=1
        continue
    fi

    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    SERVER_NAME_SAFE="${SERVER_NAME//./_}"
    BACKUP_FILE="$OUTPUT_DIR/${SERVER_NAME_SAFE}_${TIMESTAMP}.db"
    REMOTE_TMP="/tmp/backup_${TIMESTAMP}.db"

    SSH_OPTS=(-i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)

    if [[ -n "$CONTAINER" ]]; then
        # Проверяем, что контейнер существует и доступен
        if ! ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
            "docker inspect --format '{{.State.Running}}' $CONTAINER" >/dev/null 2>&1; then
            log_error "Контейнер $CONTAINER не найден или недоступен на $HOST"
            BACKUP_EXIT_CODE=1
            continue
        fi

        log_info "Создаю бекап внутри контейнера $CONTAINER ($DB_PATH)..."

        # Бекап через sqlite backup API внутри контейнера, затем docker cp на хост
        PY_BACKUP="docker exec $CONTAINER python -c 'import sqlite3; src=sqlite3.connect(\"$DB_PATH\"); dst=sqlite3.connect(\"$REMOTE_TMP\"); src.backup(dst)'"
        PY_VACUUM="docker exec $CONTAINER python -c 'import sqlite3; sqlite3.connect(\"$DB_PATH\").execute(\"VACUUM INTO \\\"$REMOTE_TMP\\\"\")'"

        if ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
            "$PY_BACKUP && docker cp $CONTAINER:$REMOTE_TMP $REMOTE_TMP && ls -l $REMOTE_TMP"; then
            log_info "Бекап создан через backup API: $REMOTE_TMP"
        elif ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
            "$PY_VACUUM && docker cp $CONTAINER:$REMOTE_TMP $REMOTE_TMP && ls -l $REMOTE_TMP"; then
            log_info "Бекап создан через VACUUM INTO: $REMOTE_TMP"
        else
            log_error "Не удалось создать бекап на сервере $HOST"
            BACKUP_EXIT_CODE=1
            continue
        fi
    else
        log_info "Создаю бекап базы $DB_PATH на сервере..."

        if ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
            "sqlite3 \"$DB_PATH\" \".backup '$REMOTE_TMP'\" && ls -l \"$REMOTE_TMP\""; then
            log_info "Бекап создан через .backup: $REMOTE_TMP"
        elif ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
            "sqlite3 \"$DB_PATH\" \"VACUUM INTO '$REMOTE_TMP'\" && ls -l \"$REMOTE_TMP\""; then
            log_info "Бекап создан через VACUUM INTO: $REMOTE_TMP"
        else
            log_error "Не удалось создать бекап на сервере $HOST"
            BACKUP_EXIT_CODE=1
            continue
        fi
    fi

    log_info "Скачиваю бекап с сервера..."
    if ! scp "${SSH_OPTS[@]}" \
        "${USER}@${HOST}:${REMOTE_TMP}" "$BACKUP_FILE"; then
        log_error "Не удалось скачать бекап с $HOST"
        # Чистим временные файлы на сервере (и в контейнере для docker-варианта)
        if [[ -n "$CONTAINER" ]]; then
            ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
                "docker exec $CONTAINER rm -f $REMOTE_TMP; rm -f $REMOTE_TMP" 2>/dev/null || true
        else
            ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "rm -f '$REMOTE_TMP'" 2>/dev/null || true
        fi
        BACKUP_EXIT_CODE=1
        continue
    fi

    log_info "Удаляю временный файл на сервере..."
    if [[ -n "$CONTAINER" ]]; then
        ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" \
            "docker exec $CONTAINER rm -f $REMOTE_TMP; rm -f $REMOTE_TMP" 2>/dev/null || true
    else
        ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" "rm -f '$REMOTE_TMP'" 2>/dev/null || true
    fi

    if [[ -f "$BACKUP_FILE" ]]; then
        SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null)
        log_info "Бекап сохранён: $BACKUP_FILE (${SIZE:-?} байт)"
    fi

done <<< "$CSV_CONTENT"

log_info "Готово! Бекапы сохранены в: $OUTPUT_DIR"

exit $BACKUP_EXIT_CODE

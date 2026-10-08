#!/bin/bash

# Скрипт восстановления базы данных на выбранном VPS.
# Выбирает бекап из каталога backups/ и сервер из tools/.servers.csv,
# останавливает сервис/контейнер, заменяет базу, чистит WAL/shm,
# исправляет права (для Docker) и запускает сервис обратно.

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
Использование: $0 [опции]

Восстанавливает выбранный бекап (из backups/) на выбранном VPS (из .servers.csv).
Перед заменой базы делает страховочный бекап текущей базы в backups/.

Опции:
  --config <путь>     Путь к CSV-файлу конфигурации (по умолчанию: $DEFAULT_CONFIG)
  --backup <файл>     Файл бекапа (имя из backups/ или полный путь).
                      Без опции показывается список и выбор в интерактиве.
  --server <имя>      Имя сервера из конфига (колонка server).
                      Без опции показывается список и выбор в интерактиве.
  --no-pre-backup     Не делать страховочный бекап текущей базы перед заменой.
  --yes               Не спрашивать подтверждение (для автоматизации).
  -h, --help          Показать эту справку

Примеры:
  $0                                  # интерактивный выбор бекапа и сервера
  $0 --server CloudCore --yes         # первый (последний) бекап на CloudCore без вопросов
  $0 --backup FastVPS_2026-10-08_19-00-01.db --server CloudCore
EOF
    exit 0
}

# --- Разбор аргументов ---
CONFIG="$DEFAULT_CONFIG"
BACKUP_ARG=""
SERVER_ARG=""
PRE_BACKUP=1
ASSUME_YES=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)        CONFIG="$2"; shift 2 ;;
        --backup)        BACKUP_ARG="$2"; shift 2 ;;
        --server)        SERVER_ARG="$2"; shift 2 ;;
        --no-pre-backup) PRE_BACKUP=0; shift ;;
        --yes)           ASSUME_YES=1; shift ;;
        -h|--help)       usage ;;
        *)               log_error "Неизвестный аргумент: $1"; usage ;;
    esac
done

# --- Чтение конфигурации серверов ---
if [[ ! -f "$CONFIG" ]]; then
    log_error "Файл конфигурации не найден: $CONFIG"
    log_info "Создай файл в формате: server,host,user,ssh_key_path,app_dir,service_name,db_path,container,backup_enabled"
    exit 1
fi

# Нормализация Windows-путей к SSH-ключам под Git Bash: C:\Users\... -> /c/Users/...
norm_path() {
    echo "$1" | sed 's|\\|/|g' | sed 's|^\([A-Za-z]\):|/\1|'
}

# Загружаем все строки CSV (кроме заголовка, комментариев и пустых строк)
declare -a SERVERS HOSTS USERS KEYS SERVICES DB_PATHS CONTAINERS

while IFS=',' read -r S_NAME S_HOST S_USER S_KEY S_APP S_SERVICE S_DB S_CONTAINER _; do
    S_NAME="${S_NAME// /}"
    S_HOST="${S_HOST// /}"
    S_USER="${S_USER// /}"
    S_KEY="${S_KEY// /}"
    S_SERVICE="${S_SERVICE// /}"
    S_DB="${S_DB// /}"
    S_CONTAINER="${S_CONTAINER// /}"

    if [[ -z "$S_HOST" || -z "$S_USER" ]]; then
        log_warn "Пропускаю строку конфига с пустыми host/user: $S_NAME"
        continue
    fi

    SERVERS+=("$S_NAME")
    HOSTS+=("$S_HOST")
    USERS+=("$S_USER")
    KEYS+=("$S_KEY")
    SERVICES+=("$S_SERVICE")
    DB_PATHS+=("$S_DB")
    CONTAINERS+=("$S_CONTAINER")
done < <(grep -v '^#' "$CONFIG" | grep -v '^$' | tail -n +2)

if [[ ${#SERVERS[@]} -eq 0 ]]; then
    log_error "В файле конфигурации нет серверов."
    exit 1
fi

# --- Выбор сервера ---
if [[ -n "$SERVER_ARG" ]]; then
    SERVER_INDEX=""
    for i in "${!SERVERS[@]}"; do
        if [[ "${SERVERS[$i]}" == "$SERVER_ARG" ]]; then
            SERVER_INDEX=$i
            break
        fi
    done
    if [[ -z "$SERVER_INDEX" ]]; then
        log_error "Сервер '$SERVER_ARG' не найден в конфиге. Доступны: ${SERVERS[*]}"
        exit 1
    fi
else
    echo "Доступные серверы:"
    for i in "${!SERVERS[@]}"; do
        MODE="systemd"
        [[ -n "${CONTAINERS[$i]}" ]] && MODE="docker"
        echo "  $((i+1)). ${SERVERS[$i]}  (${HOSTS[$i]}, $MODE)"
    done
    echo
    read -rp "Выбери номер сервера для восстановления: " CHOICE
    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [[ "$CHOICE" -lt 1 ]] || [[ "$CHOICE" -gt "${#SERVERS[@]}" ]]; then
        log_error "Некорректный выбор."
        exit 1
    fi
    SERVER_INDEX=$((CHOICE-1))
fi

TARGET_SERVER="${SERVERS[$SERVER_INDEX]}"
TARGET_HOST="${HOSTS[$SERVER_INDEX]}"
TARGET_USER="${USERS[$SERVER_INDEX]}"
TARGET_KEY=$(norm_path "${KEYS[$SERVER_INDEX]}")
TARGET_SERVICE="${SERVICES[$SERVER_INDEX]}"
TARGET_DB="${DB_PATHS[$SERVER_INDEX]}"
TARGET_CONTAINER="${CONTAINERS[$SERVER_INDEX]}"

if [[ -n "$TARGET_CONTAINER" ]]; then
    [[ -z "$TARGET_DB" ]] && { log_error "Для сервера $TARGET_SERVER задан container, но пуст db_path"; exit 1; }
else
    if [[ -z "$TARGET_DB" || -z "$TARGET_SERVICE" ]]; then
        log_error "Для сервера $TARGET_SERVER (systemd) нужны db_path и service_name в конфиге."
        exit 1
    fi
    if [[ "$TARGET_DB" == /app/* ]]; then
        log_warn "db_path '$TARGET_DB' похож на путь внутри контейнера, но container не задан. Проверь конфиг."
    fi
fi

# --- Выбор бекапа ---
if [[ -n "$BACKUP_ARG" ]]; then
    if [[ "$BACKUP_ARG" == /* ]]; then
        BACKUP_FILE="$BACKUP_ARG"
    else
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_ARG"
    fi
else
    mapfile -t BACKUPS < <(ls -1t "$BACKUP_DIR"/*.db 2>/dev/null || true)
    if [[ ${#BACKUPS[@]} -eq 0 ]]; then
        log_error "В каталоге $BACKUP_DIR нет файлов бекапов (*.db)."
        log_info "Сначала запусти tools/make_backup.sh"
        exit 1
    fi
    echo "Доступные бекапы (новые сверху):"
    for i in "${!BACKUPS[@]}"; do
        SIZE=$(du -h "${BACKUPS[$i]}" | cut -f1)
        echo "  $((i+1)). $(basename "${BACKUPS[$i]}")  ($SIZE)"
    done
    echo
    read -rp "Выбери номер бекапа: " CHOICE
    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [[ "$CHOICE" -lt 1 ]] || [[ "$CHOICE" -gt "${#BACKUPS[@]}" ]]; then
        log_error "Некорректный выбор."
        exit 1
    fi
    BACKUP_FILE="${BACKUPS[$((CHOICE-1))]}"
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    log_error "Файл бекапа не найден: $BACKUP_FILE"
    exit 1
fi

if [[ -z "$TARGET_KEY" || ! -f "$TARGET_KEY" ]]; then
    log_error "SSH-ключ не найден: ${KEYS[$SERVER_INDEX]}"
    exit 1
fi

# --- Проверка бекапа на целостность (если есть локальный инструмент) ---
if command -v python >/dev/null 2>&1; then
    INTEGRITY=$(python -c "import sqlite3; print(sqlite3.connect(r'$BACKUP_FILE').execute('PRAGMA integrity_check').fetchone()[0])" 2>/dev/null || true)
elif command -v sqlite3 >/dev/null 2>&1; then
    INTEGRITY=$(sqlite3 "$BACKUP_FILE" 'PRAGMA integrity_check;' 2>/dev/null || true)
fi
if [[ -n "${INTEGRITY:-}" && "$INTEGRITY" != "ok" ]]; then
    log_error "Локальный бекап повреждён (integrity_check: $INTEGRITY)"
    exit 1
fi
[[ -n "${INTEGRITY:-}" ]] && log_info "Локальный бекап цел (integrity_check: ok)"
[[ -z "${INTEGRITY:-}" ]] && log_warn "Нет локального python/sqlite3 — пропускаю проверку целостности бекапа"

# --- Сводка и подтверждение ---
echo
echo "Восстановление:"
echo "  Бекап:  $BACKUP_FILE"
echo "  Сервер: $TARGET_SERVER ($TARGET_USER@$TARGET_HOST)"
if [[ -n "$TARGET_CONTAINER" ]]; then
    echo "  Способ: docker (контейнер $TARGET_CONTAINER, база $TARGET_DB)"
else
    echo "  Способ: systemd (сервис $TARGET_SERVICE, база $TARGET_DB)"
fi
if [[ "$PRE_BACKUP" -eq 1 ]]; then
    echo "  Страховочный бекап текущей базы: да (в $BACKUP_DIR)"
else
    echo "  Страховочный бекап текущей базы: нет"
fi
echo

if [[ "$ASSUME_YES" -ne 1 ]]; then
    read -rp "Продолжить? Текущая база на сервере будет ЗАМЕНЕНА. [y/N]: " ANSWER
    if [[ "$ANSWER" != "y" && "$ANSWER" != "Y" && "$ANSWER" != "д" && "$ANSWER" != "Д" ]]; then
        log_info "Отменено."
        exit 0
    fi
fi

SSH_OPTS=(-i "$TARGET_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
SSH_DEST="$TARGET_USER@$TARGET_HOST"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
SERVER_SAFE="${TARGET_SERVER//./_}"
REMOTE_TMP="/tmp/restore_${TIMESTAMP}.db"
PRE_TMP="/tmp/pre_restore_${TIMESTAMP}.db"

# --- Очистка временных файлов на сервере при любом исходе ---
cleanup_remote() {
    ssh "${SSH_OPTS[@]}" "$SSH_DEST" "rm -f '$REMOTE_TMP' '$PRE_TMP'" 2>/dev/null || true
}
trap cleanup_remote EXIT

# --- 1. Загрузка бекапа на сервер ---
log_info "Загружаю бекап на $TARGET_HOST..."
if ! scp "${SSH_OPTS[@]}" "$BACKUP_FILE" "$SSH_DEST:$REMOTE_TMP"; then
    log_error "Не удалось загрузить бекап на сервер."
    exit 1
fi

# --- 2. Остановка сервиса/контейнера ---
if [[ -n "$TARGET_CONTAINER" ]]; then
    log_info "Проверяю контейнер $TARGET_CONTAINER..."
    RUNNING=$(ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "docker inspect --format '{{.State.Running}}' $TARGET_CONTAINER" 2>/dev/null || true)
    if [[ -z "$RUNNING" ]]; then
        log_error "Контейнер $TARGET_CONTAINER не найден на $TARGET_HOST"
        exit 1
    fi
    if [[ "$RUNNING" == "true" ]]; then
        log_info "Останавливаю контейнер $TARGET_CONTAINER..."
        ssh "${SSH_OPTS[@]}" "$SSH_DEST" "docker stop $TARGET_CONTAINER"
    else
        log_info "Контейнер $TARGET_CONTAINER уже остановлен."
    fi
    CONTAINER_WAS_RUNNING="$RUNNING"
else
    log_info "Останавливаю сервис $TARGET_SERVICE..."
    ssh "${SSH_OPTS[@]}" "$SSH_DEST" "systemctl stop $TARGET_SERVICE"
fi

# --- 3. Страховочный бекап текущей базы ---
if [[ "$PRE_BACKUP" -eq 1 ]]; then
    log_info "Делаю страховочный бекап текущей базы..."
    PRE_COPIED=0
    if [[ -n "$TARGET_CONTAINER" ]]; then
        if ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
            "docker cp $TARGET_CONTAINER:'$TARGET_DB' '$PRE_TMP' 2>/dev/null && test -f '$PRE_TMP'"; then
            PRE_COPIED=1
        fi
    else
        if ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
            "test -f '$TARGET_DB' && cp '$TARGET_DB' '$PRE_TMP' && test -f '$PRE_TMP'"; then
            PRE_COPIED=1
        fi
    fi

    if [[ "$PRE_COPIED" -eq 1 ]]; then
        PRE_LOCAL="$BACKUP_DIR/${SERVER_SAFE}_${TIMESTAMP}_before_restore.db"
        if scp "${SSH_OPTS[@]}" "$SSH_DEST:$PRE_TMP" "$PRE_LOCAL"; then
            log_info "Страховочный бекап сохранён: $PRE_LOCAL"
        else
            log_warn "Не удалось скачать страховочный бекап на локальную машину."
        fi
    else
        log_warn "Текущей базы на сервере нет (или её не удалось скопировать) — страховочный бекап пропущен."
    fi
fi

# --- 4. Замена базы ---
if [[ -n "$TARGET_CONTAINER" ]]; then
    log_info "Копирую бекап в контейнер $TARGET_CONTAINER ($TARGET_DB)..."
    if ! ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "docker cp '$REMOTE_TMP' $TARGET_CONTAINER:'$TARGET_DB'"; then
        log_error "Не удалось скопировать бекап в контейнер."
        exit 1
    fi

    # docker cp кладёт файл под root, а контейнер работает под book-shelf (uid 10001).
    # Чиним права и удаляем возможные WAL/shm через одноразовый контейнер с теми же volume.
    TARGET_DB_DIR="$(dirname "$TARGET_DB")"
    IMAGE_ID=$(ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "docker inspect --format '{{.Image}}' $TARGET_CONTAINER" 2>/dev/null || true)
    log_info "Исправляю права и чищу WAL/shm через вспомогательный контейнер..."
    if [[ -n "$IMAGE_ID" ]] && ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "docker run --rm -u root --volumes-from $TARGET_CONTAINER --entrypoint sh '$IMAGE_ID' -c 'rm -f \"\$0\" \"\$1\" && chown -R 10001:10001 \"\$2\"' '$TARGET_DB-wal' '$TARGET_DB-shm' '$TARGET_DB_DIR'"; then
        log_info "Права исправлены, WAL/shm удалены."
    else
        log_warn "Вспомогательный контейнер не отработал. Пробую исправить права после запуска контейнера..."
        ssh "${SSH_OPTS[@]}" "$SSH_DEST" "docker start $TARGET_CONTAINER"
        ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
            "docker exec -u root $TARGET_CONTAINER sh -c 'rm -f \"$TARGET_DB-wal\" \"$TARGET_DB-shm\"; chown -R book-shelf:book-shelf \"$TARGET_DB_DIR\"'"
        ssh "${SSH_OPTS[@]}" "$SSH_DEST" "docker restart $TARGET_CONTAINER"
    fi

    if [[ "$CONTAINER_WAS_RUNNING" == "true" ]]; then
        log_info "Запускаю контейнер $TARGET_CONTAINER..."
        ssh "${SSH_OPTS[@]}" "$SSH_DEST" "docker start $TARGET_CONTAINER"
    else
        log_info "Контейнер был остановлен до восстановления — оставляю его остановленным."
    fi
else
    TARGET_DB_DIR="$(dirname "$TARGET_DB")"
    log_info "Заменяю базу $TARGET_DB на сервере..."
    if ! ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "mkdir -p '$TARGET_DB_DIR' && cp '$REMOTE_TMP' '$TARGET_DB' && rm -f '$TARGET_DB-wal' '$TARGET_DB-shm'"; then
        log_error "Не удалось заменить базу на сервере."
        exit 1
    fi

    log_info "Запускаю сервис $TARGET_SERVICE..."
    ssh "${SSH_OPTS[@]}" "$SSH_DEST" "systemctl start $TARGET_SERVICE"
fi

# --- 5. Проверка восстановленной базы ---
log_info "Проверяю целостность восстановленной базы..."
if [[ -n "$TARGET_CONTAINER" ]]; then
    INTEGRITY=$(ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "docker exec $TARGET_CONTAINER python -c \"import sqlite3; print(sqlite3.connect('$TARGET_DB').execute('PRAGMA integrity_check').fetchone()[0])\"" 2>/dev/null || true)
else
    INTEGRITY=$(ssh "${SSH_OPTS[@]}" "$SSH_DEST" \
        "sqlite3 '$TARGET_DB' 'PRAGMA integrity_check;' 2>/dev/null || python3 -c \"import sqlite3; print(sqlite3.connect('$TARGET_DB').execute('PRAGMA integrity_check').fetchone()[0])\" 2>/dev/null" || true)
fi

if [[ "$INTEGRITY" == "ok" ]]; then
    log_info "Восстановленная база цела (integrity_check: ok)."
else
    log_warn "Не удалось проверить целостность на сервере: ${INTEGRITY:-нет инструмента проверки}"
fi

log_info "Готово! База $BACKUP_FILE восстановлена на $TARGET_SERVER."

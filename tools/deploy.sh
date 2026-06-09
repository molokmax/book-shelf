#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RELEASE_DIR="$PROJECT_ROOT/releases"
SERVERS_CSV="$PROJECT_ROOT/tools/.servers.csv"

if [ ! -d "$RELEASE_DIR" ]; then
    echo "❌ Каталог $RELEASE_DIR не найден. Сначала запусти create_release.sh"
    exit 1
fi

mapfile -t RELEASES < <(ls -1t "$RELEASE_DIR"/*.tar.gz 2>/dev/null || true)

if [ ${#RELEASES[@]} -eq 0 ]; then
    echo "❌ В каталоге $RELEASE_DIR нет архивов релизов."
    exit 1
fi

echo "Доступные релизы:"
for i in "${!RELEASES[@]}"; do
    NAME=$(basename "${RELEASES[$i]}")
    SIZE=$(du -h "${RELEASES[$i]}" | cut -f1)
    echo "  $((i+1)). $NAME  ($SIZE)"
done

echo
read -p "Выбери номер релиза для деплоя: " CHOICE

if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "${#RELEASES[@]}" ]; then
    echo "❌ Некорректный выбор."
    exit 1
fi

SELECTED_ARCHIVE="${RELEASES[$((CHOICE-1))]}"
echo "✅ Выбран: $(basename "$SELECTED_ARCHIVE")"

# --- Чтение конфигурации сервера ---
SERVER_LINE=$(tail -n +2 "$SERVERS_CSV" | head -1)
if [ -z "$SERVER_LINE" ]; then
    echo "❌ Не удалось прочитать конфигурацию сервера из .servers.csv"
    exit 1
fi

IFS=',' read -r SERVER_NAME SERVER_IP SERVER_USER SSH_KEY_PATH APP_DIR SERVICE_NAME DB_PATH <<< "$SERVER_LINE"

# Обрезка пробелов
SERVER_NAME=$(echo "$SERVER_NAME" | xargs)
SERVER_IP=$(echo "$SERVER_IP" | xargs)
SERVER_USER=$(echo "$SERVER_USER" | xargs)
SSH_KEY_PATH=$(echo "$SSH_KEY_PATH" | sed 's|\\|/|g' | sed 's|^\([A-Za-z]\):|/\1|')
APP_DIR=$(echo "$APP_DIR/app" | xargs)
SERVICE_NAME=$(echo "$SERVICE_NAME" | xargs)

if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ]; then
    echo "❌ Некорректные данные сервера в .servers.csv"
    exit 1
fi

SSH_DEST="$SERVER_USER@$SERVER_IP"
SSH_CMD="ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $SSH_DEST"
SCP_CMD="scp -i $SSH_KEY_PATH -o StrictHostKeyChecking=no"

echo
echo "🚀 Деплой на $SERVER_NAME ($SERVER_IP)..."
echo "   Каталог приложения: $APP_DIR"
echo "   Сервис: $SERVICE_NAME"

# --- Копирование архива на сервер ---
echo
echo "📤 Копирование архива на сервер..."
$SCP_CMD "$SELECTED_ARCHIVE" "$SSH_DEST:/tmp/"

REMOTE_ARCHIVE_NAME=$(basename "$SELECTED_ARCHIVE")

# --- Остановка сервиса ---
echo "⏹ Остановка сервиса $SERVICE_NAME..."
$SSH_CMD "systemctl stop $SERVICE_NAME"

# --- Распаковка и замена файлов ---
echo "📦 Распаковка релиза в $APP_DIR..."
$SSH_CMD "rm -rf $APP_DIR/* && tar -xzf /tmp/$REMOTE_ARCHIVE_NAME -C $APP_DIR/ && rm -f /tmp/$REMOTE_ARCHIVE_NAME"

echo "📦 Обновление зависимостей"
$SSH_CMD "cd $APP_DIR/.. && python3 -m venv .venv"
$SSH_CMD "cd $APP_DIR/.. && .venv/bin/pip3 install -r requirements.txt"

# --- Запуск сервиса ---
echo "▶️ Запуск сервиса $SERVICE_NAME..."
$SSH_CMD "systemctl start $SERVICE_NAME"

# --- Проверка статуса ---
echo "📋 Проверка статуса сервиса..."
sleep 2
$SSH_CMD "systemctl status $SERVICE_NAME --no-pager || true"

echo
echo "✅ Деплой завершён!"

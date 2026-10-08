# Установка docker на VPS

Ниже приведены команды из инструкции https://timeweb.cloud/tutorials/docker/kak-ustanovit-docker-na-ubuntu-22-04

```
sudo apt update

sudo apt install curl software-properties-common ca-certificates apt-transport-https -y

wget -O- https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor | sudo tee /etc/apt/keyrings/docker.gpg > /dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable"| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

apt-cache policy docker-ce

sudo apt install docker-ce -y

sudo systemctl status docker

sudo usermod -aG docker $USER
newgrp docker
```


# Деплой Book Shelf на VPS

Инструкция по запуску бота на VPS из готового Docker-образа. Установка Docker описана отдельно в [docker-setup.md](./docker-setup.md).

Образ уже содержит всё нужное: Python 3.11, runtime-зависимости, код, пользователя `book-shelf` и каталоги `/app/data` и `/app/temp`. Бот работает через VK Long Poll, то есть сам открывает исходящее соединение — входящие порты открывать не нужно.

## 1. Получение образа

Если образ публикуется workflow в Docker Hub:

```bash
# приватный репозиторий — залогиниться access token'ом вместо пароля
docker login

docker pull <USERNAME>/book-shelf:latest
```

Для прода лучше использовать конкретную версию (`X.Y.Z`), а не `latest`, чтобы обновления были управляемыми:

```bash
docker pull <USERNAME>/book-shelf:X.Y.Z
```

Если образа в registry нет, собери его из репозитория на VPS:

```bash
git clone <repo-url> && cd book-shelf
docker build -t book-shelf .
```

## 2. Секреты

`BOT_TOKEN` нельзя передавать в командной строке — он попадёт в историю shell и в `ps`. Только через `.env`:

```bash
mkdir -p /opt/book-shelf && cd /opt/book-shelf
nano .env
```

```ini
BOT_TOKEN=твой_токен_vk
DEBUG=false
```

```bash
chmod 600 .env
```

`DATA_DIR` и `TEMP_DIR` задавать не нужно: в образе они уже указывают на `/app/data` и `/app/temp`. Часовой пояс `TZ=Europe/Moscow` тоже зашит в образ.

## 3. Запуск

Вариант через `docker run`:

```bash
docker run -d --name book-shelf \
  --env-file .env \
  -v book-shelf-data:/app/data \
  --restart unless-stopped \
  <USERNAME>/book-shelf:X.Y.Z
```

Вариант через Compose (без клонирования репозитория). Файл `compose.yaml`:

```yaml
services:
  book-shelf:
    image: <USERNAME>/book-shelf:X.Y.Z
    env_file: .env
    volumes:
      - book-shelf-data:/app/data
    restart: unless-stopped

volumes:
  book-shelf-data:
```

```bash
docker compose up -d
```

Политика `restart: unless-stopped` плюс `systemctl enable docker` гарантируют, что после перезагрузки VPS контейнер поднимется сам.

## 4. Проверка

```bash
docker logs -f book-shelf
```

В логах должна появиться строка «Бот запущен и ожидает сообщений...». Если вместо неё ошибка «Неверный токен. Проверьте его.» — проблема в `BOT_TOKEN`.

## 5. База данных и бэкапы

База SQLite лежит в named volume `book-shelf-data` (внутри контейнера — файл `/app/data/database.db`). Volume живёт отдельно от контейнера: перезапуск, `docker stop`/`docker rm`, обновление и пересборка образа его не затрагивают.

Volume удаляется только явно: `docker volume rm book-shelf-data` или `docker compose down -v`. Эти команды не запускай без бэкапа.

Бэкап без остановки бота (безопасно для живого SQLite через backup API):

```bash
docker exec book-shelf python -c "import sqlite3; src=sqlite3.connect('/app/data/database.db'); dst=sqlite3.connect('/app/data/backup.db'); src.backup(dst)"
docker cp book-shelf:/app/data/backup.db ./backup-$(date +%F).db
docker exec book-shelf rm /app/data/backup.db
```

Простой вариант (требует остановки бота):

```bash
docker stop book-shelf
docker cp book-shelf:/app/data/database.db ./backup-$(date +%F).db
docker start book-shelf
```

Восстановление:

```bash
docker cp ./backup-2026-10-08.db book-shelf:/app/data/database.db
docker restart book-shelf
```

Перенос существующей базы со старого сервера (например, с systemd-деплоя):

```bash
docker cp data/database.db book-shelf:/app/data/database.db
docker restart book-shelf
```

## 6. Обновление версии

```bash
docker pull <USERNAME>/book-shelf:X.Y.Z
docker stop book-shelf && docker rm book-shelf
docker run -d --name book-shelf \
  --env-file .env \
  -v book-shelf-data:/app/data \
  --restart unless-stopped \
  <USERNAME>/book-shelf:X.Y.Z
```

Через Compose: поменять тег в `compose.yaml`, затем:

```bash
docker compose pull
docker compose up -d
```

Данные при обновлении не теряются: контейнер пересоздаётся, volume остаётся на месте.

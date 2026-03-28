# Deploy Guide

Ниже подробная инструкция, как подготовить GitHub, установить всё на сервер и запустить проект почти полностью автоматически.

## 1. Создание репозитория GitHub

Нужный remote:

```bash
git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git
```

Если репозиторий ещё не создан:

1. Войди в GitHub под пользователем `mary-antonova-2007`.
2. Нажми `New repository`.
3. Укажи имя `SOCKS5_Teleproxy`.
4. Не добавляй `.gitignore` и `README`, потому что они уже есть локально.
5. Создай репозиторий.

После этого в локальном проекте выполни:

```bash
git init
git branch -M main
git remote add origin git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

## 2. Если Git не установлен локально

### Windows

1. Скачай Git for Windows: `https://git-scm.com/download/win`
2. Установи с настройками по умолчанию.
3. Открой новый PowerShell или Git Bash.
4. Проверь:

```bash
git --version
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y git
git --version
```

### Rocky / AlmaLinux / CentOS

```bash
sudo dnf install -y git || sudo yum install -y git
git --version
```

## 3. Если Docker не установлен на сервере

Проще всего не ставить его вручную, а использовать `server-bootstrap.sh`, потому что он ставит Docker сам.

Но если нужно руками:

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$ID $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
docker --version
docker compose version
```

### Rocky / AlmaLinux / CentOS

```bash
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
docker --version
docker compose version
```

## 4. Клонирование проекта на сервер

Если на сервере уже настроен SSH-ключ для GitHub:

```bash
git clone git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git
cd SOCKS5_Teleproxy
```

Если репозиторий публичный, можно через HTTPS:

```bash
git clone https://github.com/mary-antonova-2007/SOCKS5_Teleproxy.git
cd SOCKS5_Teleproxy
```

## 5. Полностью автоматический deploy на VPS

### Вариант A. Запустить bootstrap-скрипт из уже клонированного проекта

```bash
sudo PUBLIC_API_HOST=SERVER_IP \
  API_PORT=8088 \
  SOCKS5_PORT=1080 \
  SUPERADMIN_USERNAME=superadmin \
  SUPERADMIN_PASSWORD='replace-superadmin-password' \
  INITIAL_ADMIN_USERNAME=admin \
  INITIAL_ADMIN_PASSWORD='replace-admin-password' \
  bash server-bootstrap.sh
```

Что делает скрипт:

- ставит `git`, `curl`, `jq`
- ставит Docker и Docker Compose plugin
- включает `docker.service`
- клонирует или обновляет проект в `APP_DIR` (по умолчанию `/opt/SOCKS5_TeleProxy`)
- запускает `./deploy.sh --auto`

Полезные переменные:

- `REPO_URL` — URL репозитория
- `REPO_BRANCH` — ветка, по умолчанию `main`
- `APP_DIR` — каталог установки, по умолчанию `/opt/SOCKS5_TeleProxy`
- `PUBLIC_API_HOST` — IP или домен сервера
- `API_PORT` — порт API и админки
- `SOCKS5_PORT` — порт SOCKS5
- `SUPERADMIN_USERNAME`
- `SUPERADMIN_PASSWORD`
- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`
- `AUTO_START=0` — только подготовить сервер, но не запускать deploy

### Вариант B. Загрузить на новый VPS один скрипт

Иногда VPS-провайдер позволяет вставить shell-скрипт при создании инстанса. Для этого можно использовать `server-bootstrap.sh` как основу cloud-init/custom script.

Минимальный сценарий:

```bash
#!/usr/bin/env bash
set -euo pipefail
curl -fsSL https://raw.githubusercontent.com/mary-antonova-2007/SOCKS5_Teleproxy/main/server-bootstrap.sh -o /root/server-bootstrap.sh
chmod +x /root/server-bootstrap.sh
REPO_URL=git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git \
APP_DIR=/opt/SOCKS5_TeleProxy \
PUBLIC_API_HOST=SERVER_IP \
API_PORT=8088 \
SOCKS5_PORT=1080 \
SUPERADMIN_USERNAME=superadmin \
SUPERADMIN_PASSWORD='replace-superadmin-password' \
INITIAL_ADMIN_USERNAME=admin \
INITIAL_ADMIN_PASSWORD='replace-admin-password' \
bash /root/server-bootstrap.sh
```

Важно:

- этот способ заработает только после того, как репозиторий уже будет доступен на GitHub
- если используется `git@github.com:...`, на сервере должен быть SSH-ключ с доступом к репозиторию
- для публичного репозитория можно заменить `REPO_URL` на HTTPS

## 6. Ручной deploy после клонирования

Если не хочется использовать bootstrap:

```bash
cp .env.example .env
chmod +x deploy.sh uninstall.sh login.sh create_user.sh delete_user.sh list_users.sh docs/smoke-test.sh
./deploy.sh
```

Или без вопросов:

```bash
./deploy.sh --auto
```

## 7. Где открывать админку после deploy

Если у тебя:

- `PUBLIC_API_HOST=203.0.113.10`
- `API_PORT=8088`

Тогда:

- админка: `http://203.0.113.10:8088/`
- health: `http://203.0.113.10:8088/health`

## 8. Что проверить после запуска

Проверить контейнеры:

```bash
docker compose ps
```

Посмотреть health:

```bash
curl http://127.0.0.1:8088/health
```

Прогнать smoke-test:

```bash
./docs/smoke-test.sh
```

## 9. Обновление проекта на сервере

Если проект уже развёрнут:

```bash
cd /opt/SOCKS5_TeleProxy
git pull --ff-only origin main
./deploy.sh --auto
```

Если используется `server-bootstrap.sh`, можно запускать его повторно: он обновит репозиторий и снова выполнит deploy.

## 10. Что хранить в секрете

Не публикуй:

- `.env`
- `SUPERADMIN_PASSWORD`
- `INITIAL_ADMIN_PASSWORD`
- `JWT_SECRET`
- содержимое `data/users.json`

Эти файлы уже добавлены в `.gitignore`, поэтому по умолчанию в git они не попадут.

## 11. Где смотреть логи SOCKS5

На сервере:

```bash
cd /opt/SOCKS5_TeleProxy
tail -f data/3proxy.log.$(date +%Y.%m.%d)
docker logs -f telegram-socks5-proxy-1
```

Для Telegram на IPv4-only VPS особенно важна настройка:

```env
PROXY_RESOLVE_MODE=ipv4
PROXY_DEBUG_LOGGING=true
```

Это уменьшает зависания на попытках `IPv6 connect()` и делает логи заметно информативнее.

## 12. MTProto proxy

Если Telegram плохо работает через SOCKS5, можно включить встроенный MTProto proxy:

```env
ENABLE_MTPROTO=true
MTPROTO_PORT=443
MTPROTO_CLIENT_SECRET=0123456789abcdef0123456789abcdef
MTPROTO_WORKERS=
MTPROTO_VERBOSITY=
MTPROTO_TLS_DOMAIN=
```

После деплоя получить ссылку для Telegram:

```bash
./mtproto_link.sh
```

Формат ссылки:

```text
tg://proxy?server=SERVER_IP&port=443&secret=ddYOUR_32_HEX_SECRET
```

Для Fake TLS режима:

```text
tg://proxy?server=SERVER_IP&port=443&secret=eeYOUR_32_HEX_SECRETHEX_ENCODED_DOMAIN
```

Основа конфигурации берётся из официального репозитория Telegram MTProxy:

- https://github.com/TelegramMessenger/MTProxy

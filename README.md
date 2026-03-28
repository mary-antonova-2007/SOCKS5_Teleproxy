# SOCKS5 TeleProxy

Проект поднимает SOCKS5-прокси и MTProto proxy для Telegram и даёт простую веб-админку на `HTML + CSS + JS` для управления пользователями.

В составе:

- `api` — FastAPI backend с JWT-авторизацией, REST API и встроенной админкой
- `proxy` — контейнер с `3proxy`
- `mtproxy` — MTProto proxy для клиентов Telegram
- `data/` — runtime-данные и сгенерированный конфиг прокси
- `media/logo.png` — логотип, который используется в админке и модалках
- `deploy.sh` — основной deploy-скрипт
- `server-bootstrap.sh` — серверный bootstrap-скрипт для VPS, который ставит зависимости, клонирует проект и запускает deploy

Админка открывается на корне API, например: `http://SERVER_IP:8088/`

## Возможности

- экран авторизации с логотипом
- header после входа с логотипом, приветствием и кнопкой выхода
- адаптивный список пользователей
- создание пользователя в красивой модалке
- редактирование пользователя кнопкой-карандашом
- удаление пользователя через модалку подтверждения
- поддержка светлой и тёмной схемы ОС через `prefers-color-scheme`
- диагностическое логирование `3proxy` и принудительный IPv4-resolve для Telegram-friendly режима
- MTProto proxy как альтернативный способ подключения Telegram

## Быстрый старт локально

1. Скопируй пример окружения:

```bash
cp .env.example .env
```

2. Выдай права на скрипты:

```bash
chmod +x deploy.sh uninstall.sh login.sh create_user.sh delete_user.sh list_users.sh docs/smoke-test.sh server-bootstrap.sh
```

3. Запусти деплой:

```bash
./deploy.sh
```

4. Открой:

- админку: `http://127.0.0.1:8088/`
- health-check: `http://127.0.0.1:8088/health`

## Полный автодеплой без вопросов

Если значения уже лежат в `.env` или подходят дефолты, можно выполнить:

```bash
./deploy.sh --auto
```

В `--auto` режиме:

- не задаются интерактивные вопросы
- если пароль `superadmin` или `admin` не задан, он будет сгенерирован автоматически
- итоговые значения сохраняются в `.env`

## Deploy на VPS одной командой

Для Ubuntu/Debian/Rocky/Alma/CentOS подготовлен `server-bootstrap.sh`.

Он умеет:

- установить `git`, `curl`, `jq`
- установить Docker Engine и Docker Compose plugin
- включить Docker как system service
- клонировать или обновить репозиторий
- выдать права на скрипты
- запустить `./deploy.sh --auto`

Пример запуска на сервере:

```bash
sudo REPO_URL=git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git \
  REPO_BRANCH=main \
  APP_DIR=/opt/SOCKS5_TeleProxy \
  PUBLIC_API_HOST=SERVER_IP \
  API_PORT=8088 \
  SOCKS5_PORT=1080 \
  SUPERADMIN_USERNAME=superadmin \
  SUPERADMIN_PASSWORD='change-this-superadmin-password' \
  INITIAL_ADMIN_USERNAME=admin \
  INITIAL_ADMIN_PASSWORD='change-this-admin-password' \
  bash server-bootstrap.sh
```

Если пароли не передать, они будут автоматически сгенерированы и записаны в `/opt/SOCKS5_TeleProxy/.env`.

Подробный серверный сценарий смотри в [docs/DEPLOY.md](/mnt/d/SOCKS5_TeleProxy/docs/DEPLOY.md).

## GitHub: подготовка репозитория

Локальный проект можно сразу превратить в git-репозиторий и привязать к нужному remote:

```bash
git init
git branch -M main
git remote add origin git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

Если удалённый репозиторий ещё не создан в GitHub, сначала создай его в аккаунте `mary-antonova-2007` с именем `SOCKS5_Teleproxy`, затем выполни команды выше.

## REST API

- `POST /auth/login`
- `GET /health`
- `GET /proxy-users`
- `POST /proxy-users`
- `PATCH /proxy-users/{username}`
- `DELETE /proxy-users/{username}`
- `GET /admins`
- `POST /admins`
- `PATCH /admins/{username}/password`
- `DELETE /admins/{username}`

## Диагностика SOCKS5

Если Telegram не подключается, смотри:

```bash
cd /opt/SOCKS5_TeleProxy
tail -f data/3proxy.log.$(date +%Y.%m.%d)
```

Полезные переменные:

- `PROXY_RESOLVE_MODE=ipv4` — заставляет `3proxy` резолвить только IPv4
- `PROXY_DEBUG_LOGGING=true` — включает более подробные записи и промежуточный `logdump`

## MTProto

Если Telegram плохо работает через SOCKS5, можно использовать встроенный MTProto proxy.

Полезные переменные:

- `ENABLE_MTPROTO=true`
- `MTPROTO_PORT=443`
- `MTPROTO_CLIENT_SECRET=0123456789abcdef0123456789abcdef`
- `MTPROTO_TAG=` опционально, если зарегистрируешь прокси в `@MTProxybot`

Важно:

- в `.env` секрет хранится как базовые `32` hex-символа
- в ссылке `tg://proxy?...` скрипт сам добавляет клиентский префикс `dd`

Получить готовую ссылку:

```bash
./mtproto_link.sh
```

## Скрипты

- `deploy.sh` — основной деплой и bootstrap `.env`
- `server-bootstrap.sh` — автоматическая подготовка VPS
- `mtproto_link.sh` — вывести готовую ссылку `tg://proxy?...`
- `uninstall.sh` — остановка и удаление окружения
- `login.sh` — получить JWT
- `create_user.sh` — создать proxy user
- `delete_user.sh` — удалить proxy user
- `list_users.sh` — вывести список proxy users
- `docs/smoke-test.sh` — end-to-end smoke-test

## Тесты

API-тесты:

```bash
cd api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest
```

Smoke-test после деплоя:

```bash
./docs/smoke-test.sh
```

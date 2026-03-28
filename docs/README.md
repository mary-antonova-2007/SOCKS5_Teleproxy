# Telegram SOCKS5 Docs

В каталоге `docs/` лежит служебная документация по деплою и проверке проекта.

## Файлы

- [README.md](/mnt/d/SOCKS5_TeleProxy/README.md) — основное описание проекта
- [DEPLOY.md](/mnt/d/SOCKS5_TeleProxy/docs/DEPLOY.md) — подробная инструкция для GitHub и VPS
- [smoke-test.sh](/mnt/d/SOCKS5_TeleProxy/docs/smoke-test.sh) — скрипт end-to-end проверки

## Что проверяет `smoke-test.sh`

1. Логин под admin.
2. Создание тестового прокси-пользователя.
3. Проверка `GET /health` и `GET /proxy-users`.
4. Проверка SOCKS5 через `curl --proxy socks5h://...`.
5. Удаление тестового пользователя.

## Базовые переменные окружения

- `PROJECT_NAME`
- `PUBLIC_API_HOST`
- `API_PORT`
- `API_BASE_URL`
- `SOCKS5_PORT`
- `DATA_DIR`
- `SUPERADMIN_USERNAME`
- `SUPERADMIN_PASSWORD`
- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`

## Основные сценарии

- Для локального старта используй `./deploy.sh`
- Для деплоя без вопросов используй `./deploy.sh --auto`
- Для новой VPS используй `server-bootstrap.sh`

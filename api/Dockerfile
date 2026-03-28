FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY telegram_socks5_api /app/telegram_socks5_api

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn telegram_socks5_api.main:app --host 0.0.0.0 --port ${API_PORT:-8000}"]

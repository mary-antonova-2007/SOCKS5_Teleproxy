#!/bin/sh
set -eu

log() {
  printf '%s\n' "[mtproxy] $*"
}

die() {
  printf '%s\n' "[mtproxy] ERROR: $*" >&2
  exit 1
}

DATA_DIR=${DATA_DIR:-/data}
STATE_DIR="${DATA_DIR}/mtproxy"
PROXY_SECRET_FILE="${STATE_DIR}/proxy-secret"
PROXY_CONFIG_FILE="${STATE_DIR}/proxy-multi.conf"
CLIENT_SECRET="${MTPROTO_CLIENT_SECRET:-}"
PUBLIC_HOST="${MTPROTO_PUBLIC_HOST:-127.0.0.1}"
CLIENT_PORT="${MTPROTO_PORT:-443}"
LISTEN_PORT="${MTPROTO_LISTEN_PORT:-443}"
STATS_PORT="${MTPROTO_STATS_PORT:-8888}"
TAG="${MTPROTO_TAG:-}"
WORKERS="${MTPROTO_WORKERS:-}"
TLS_DOMAIN="${MTPROTO_TLS_DOMAIN:-}"
VERBOSITY="${MTPROTO_VERBOSITY:-}"

[ -n "$CLIENT_SECRET" ] || die "MTPROTO_CLIENT_SECRET is required"
case "$CLIENT_SECRET" in
  dd????????????????????????????????)
    CLIENT_SECRET="${CLIENT_SECRET#dd}"
    ;;
esac

case "$CLIENT_SECRET" in
  [0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])
    ;;
  *)
    die "MTPROTO_CLIENT_SECRET must be 32 hex digits, optionally prefixed with dd"
    ;;
esac

mkdir -p "$STATE_DIR"

refresh_files() {
  curl -fsSL https://core.telegram.org/getProxySecret -o "$PROXY_SECRET_FILE"
  curl -fsSL https://core.telegram.org/getProxyConfig -o "$PROXY_CONFIG_FILE"
}

refresh_files

(
  while true; do
    sleep 86400
    log "Refreshing Telegram proxy config"
    refresh_files || log "Failed to refresh Telegram proxy config"
  done
) &
refresh_pid=$!

cleanup() {
  kill "$refresh_pid" >/dev/null 2>&1 || true
}

trap cleanup INT TERM

set -- mtproto-proxy \
  -u nobody \
  -p "$STATS_PORT" \
  -H "$LISTEN_PORT" \
  -S "$CLIENT_SECRET" \
  --aes-pwd "$PROXY_SECRET_FILE" "$PROXY_CONFIG_FILE"

if [ -n "$VERBOSITY" ]; then
  case "$VERBOSITY" in
    ''|*[!0-9]*)
      die "MTPROTO_VERBOSITY must be a non-negative integer"
      ;;
    *)
      i=0
      while [ "$i" -lt "$VERBOSITY" ]; do
        set -- "$@" -v
        i=$((i + 1))
      done
      ;;
  esac
fi

if [ -z "$WORKERS" ] && [ -z "$TLS_DOMAIN" ]; then
  WORKERS=1
fi

if [ -n "$WORKERS" ] && [ "$WORKERS" != "0" ]; then
  set -- "$@" -M "$WORKERS"
fi

if [ -n "$TAG" ]; then
  set -- "$@" -P "$TAG"
fi

if [ -n "$TLS_DOMAIN" ]; then
  set -- "$@" -D "$TLS_DOMAIN"
fi

log "Starting MTProto proxy on ${PUBLIC_HOST}:${CLIENT_PORT}"
if [ -n "$TLS_DOMAIN" ]; then
  tls_secret="$(printf '%s' "$TLS_DOMAIN" | od -An -tx1 -v | tr -d ' \n')"
  log "Client link: tg://proxy?server=${PUBLIC_HOST}&port=${CLIENT_PORT}&secret=ee${CLIENT_SECRET}${tls_secret}"
else
  log "Client link: tg://proxy?server=${PUBLIC_HOST}&port=${CLIENT_PORT}&secret=dd${CLIENT_SECRET}"
fi

exec "$@"

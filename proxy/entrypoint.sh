#!/bin/sh
set -eu

log() {
  printf '%s\n' "[telegram-socks5-proxy] $*"
}

die() {
  printf '%s\n' "[telegram-socks5-proxy] ERROR: $*" >&2
  exit 1
}

is_uint() {
  case "${1:-}" in
    ''|*[!0-9]*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

require_port() {
  if ! is_uint "$1"; then
    die "$2 must be an integer"
  fi
  if [ "$1" -lt 1 ] || [ "$1" -gt 65535 ]; then
    die "$2 must be between 1 and 65535"
  fi
}

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[&|]/\\&/g'
}

render_template() {
  template_path=$1
  output_path=$2

  [ -f "$template_path" ] || die "template not found: $template_path"

  sed \
    -e "s|__PIDFILE_PATH__|$(escape_sed_replacement "$PIDFILE_PATH")|g" \
    -e "s|__LOG_PATH__|$(escape_sed_replacement "$LOG_PATH")|g" \
    -e "s|__SERVICE_NAME__|$(escape_sed_replacement "$SERVICE_NAME")|g" \
    -e "s|__PRIMARY_RESOLVER__|$(escape_sed_replacement "$PRIMARY_RESOLVER")|g" \
    -e "s|__SECONDARY_RESOLVER__|$(escape_sed_replacement "$SECONDARY_RESOLVER")|g" \
    -e "s|__SOCKS5_PORT__|$(escape_sed_replacement "$SOCKS5_PORT")|g" \
    -e "s|__BIND_ADDRESS__|$(escape_sed_replacement "$BIND_ADDRESS")|g" \
    "$template_path" > "$output_path"
}

json_status() {
  request_id=$1
  status=$2
  detail=$3
  printf '{"request_id":"%s","status":"%s","detail":"%s"}\n' "$request_id" "$status" "$detail" > "$STATUS_FILE"
}

DATA_DIR=${DATA_DIR:-/data}
CONFIG_PATH=${SOCKS5_PROXY_CONFIG_FILE:-$DATA_DIR/3proxy.cfg}
PIDFILE_PATH=${SOCKS5_PROXY_PID_FILE:-$DATA_DIR/3proxy.pid}
LOG_PATH=${SOCKS5_PROXY_LOG_FILE:-$DATA_DIR/3proxy.log}
REQUEST_FILE=${SOCKS5_PROXY_RELOAD_REQUEST_FILE:-$DATA_DIR/reload.request}
STATUS_FILE=${SOCKS5_PROXY_RELOAD_STATUS_FILE:-$DATA_DIR/reload.status}
TEMPLATE_PATH=${PROXY_TEMPLATE_PATH:-/usr/local/share/telegram-socks5-proxy/3proxy.cfg.tpl}
SERVICE_NAME=${PROXY_SERVICE_NAME:-telegram-socks5-proxy}
SOCKS5_PORT=${SOCKS5_PORT:-1080}
BIND_ADDRESS=${PROXY_BIND_ADDRESS:-0.0.0.0}
PRIMARY_RESOLVER=${PROXY_PRIMARY_RESOLVER:-1.1.1.1}
SECONDARY_RESOLVER=${PROXY_SECONDARY_RESOLVER:-8.8.8.8}

require_port "$SOCKS5_PORT" "SOCKS5_PORT"
mkdir -p "$DATA_DIR"

if ! command -v 3proxy >/dev/null 2>&1; then
  die "3proxy binary not found in PATH"
fi

if [ ! -f "$CONFIG_PATH" ]; then
  log "Creating fallback config at $CONFIG_PATH"
  render_template "$TEMPLATE_PATH" "$CONFIG_PATH"
fi

log "Using config $CONFIG_PATH"
log "Writing pidfile to $PIDFILE_PATH"
log "Starting 3proxy on SOCKS5 port $SOCKS5_PORT"

3proxy "$CONFIG_PATH" &
proxy_pid=$!

cleanup() {
  if kill -0 "$proxy_pid" >/dev/null 2>&1; then
    kill "$proxy_pid" >/dev/null 2>&1 || true
    wait "$proxy_pid" || true
  fi
}

trap cleanup INT TERM

last_request_id=""

while kill -0 "$proxy_pid" >/dev/null 2>&1; do
  if [ -f "$REQUEST_FILE" ]; then
    request_id=$(sed -n 's/.*"request_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$REQUEST_FILE" | head -n 1)
    if [ -n "$request_id" ] && [ "$request_id" != "$last_request_id" ]; then
      if kill -USR1 "$proxy_pid" >/dev/null 2>&1; then
        json_status "$request_id" "ok" "reload signal sent"
        last_request_id="$request_id"
      else
        json_status "$request_id" "error" "failed to signal 3proxy"
      fi
    fi
  fi
  sleep 1
done &
watcher_pid=$!

wait "$proxy_pid"
proxy_status=$?
kill "$watcher_pid" >/dev/null 2>&1 || true
wait "$watcher_pid" >/dev/null 2>&1 || true
exit "$proxy_status"

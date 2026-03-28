#!/usr/bin/env bash
set -euo pipefail

ts5_script_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

TS5_ROOT_DIR="$(ts5_script_dir)"

ts5_env_file_default() {
  printf '%s\n' "${TELEGRAM_SOCKS5_ENV_FILE:-$TS5_ROOT_DIR/.env}"
}

ts5_compose_file_default() {
  printf '%s\n' "${TELEGRAM_SOCKS5_COMPOSE_FILE:-$TS5_ROOT_DIR/docker-compose.yml}"
}

ts5_data_dir_default() {
  printf '%s\n' "${DATA_DIR:-$TS5_ROOT_DIR/data}"
}

ts5_api_url_default() {
  if [[ -n "${API_BASE_URL:-}" ]]; then
    printf '%s\n' "$API_BASE_URL"
    return 0
  fi

  local host="${PUBLIC_API_HOST:-127.0.0.1}"
  local port="${API_PORT:-8088}"
  printf 'http://%s:%s\n' "$host" "$port"
}

ts5_load_env_file() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 0
  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
}

ts5_require_bins() {
  local missing=()
  local bin
  for bin in "$@"; do
    command -v "$bin" >/dev/null 2>&1 || missing+=("$bin")
  done

  if (( ${#missing[@]} )); then
    printf 'Missing required command(s): %s\n' "${missing[*]}" >&2
    return 1
  fi
}

ts5_compose() {
  local env_file="$1"
  local compose_file="$2"
  shift 2
  docker compose --project-name "${PROJECT_NAME:-telegram-socks5}" --env-file "$env_file" -f "$compose_file" "$@"
}

ts5_warn() {
  printf 'WARN: %s\n' "$*" >&2
}

ts5_die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

ts5_prompt() {
  local prompt="$1"
  local default_value="${2:-}"
  local reply

  if [[ -n "$default_value" ]]; then
    read -r -p "$prompt [$default_value]: " reply
    printf '%s\n' "${reply:-$default_value}"
  else
    read -r -p "$prompt: " reply
    printf '%s\n' "$reply"
  fi
}

ts5_prompt_secret() {
  local prompt="$1"
  local default_value="${2:-}"
  local reply

  if [[ -n "$default_value" ]]; then
    read -r -s -p "$prompt [$default_value]: " reply
    printf '\n'
    printf '%s\n' "${reply:-$default_value}"
  else
    read -r -s -p "$prompt: " reply
    printf '\n'
    printf '%s\n' "$reply"
  fi
}

ts5_generate_secret() {
  tr -dc 'A-Za-z0-9' </dev/urandom | head -c 48
  printf '\n'
}

ts5_shell_quote() {
  printf '%q' "$1"
}

ts5_is_placeholder_value() {
  case "${1:-}" in
    ""|change-me*|CHANGE-ME*|Change-me*|replace-me*|REPLACE-ME*|example*|EXAMPLE*|your-*|YOUR-*|todo*|TODO*|changeme*|CHANGE_ME*|please-change*|PLEASE-CHANGE*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

ts5_empty_if_placeholder() {
  local value="${1:-}"
  if ts5_is_placeholder_value "$value"; then
    printf '\n'
  else
    printf '%s\n' "$value"
  fi
}

ts5_json_escape() {
  jq -Rn --arg value "$1" '$value'
}

ts5_urlencode() {
  jq -rn --arg value "$1" '$value|@uri'
}

ts5_login_token() {
  local api_url="$1"
  local username="$2"
  local password="$3"
  local payload

  payload="$(jq -n --arg username "$username" --arg password "$password" '{username: $username, password: $password}')"
  curl -fsS \
    -X POST "$api_url/auth/login" \
    -H 'Content-Type: application/json' \
    -d "$payload" \
    | jq -er '.access_token'
}

ts5_api_call() {
  local api_url="$1"
  local method="$2"
  local path="$3"
  local token="${4:-}"
  local payload="${5:-}"
  local url="${api_url%/}${path}"
  local args=(-fsS -X "$method" "$url" -H 'Content-Type: application/json')

  if [[ -n "$token" ]]; then
    args+=(-H "Authorization: Bearer $token")
  fi

  if [[ -n "$payload" ]]; then
    args+=(-d "$payload")
  fi

  curl "${args[@]}"
}

ts5_port_in_use() {
  local port="$1"
  ss -ltnH "( sport = :$port )" 2>/dev/null | grep -q .
}

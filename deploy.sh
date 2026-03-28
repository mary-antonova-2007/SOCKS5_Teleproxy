#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/telegram-socks5-common.sh"

usage() {
  cat <<'EOF'
Usage: deploy.sh [--auto] [--env-file FILE] [--compose-file FILE]
EOF
}

env_file="$(ts5_env_file_default)"
compose_file="$(ts5_compose_file_default)"
auto_mode=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto|--non-interactive)
      auto_mode=1
      shift
      ;;
    --env-file)
      env_file="$2"
      shift 2
      ;;
    --compose-file)
      compose_file="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      ts5_die "Unknown argument: $1"
      ;;
  esac
done

ts5_require_bins docker jq curl ss

if ! docker compose version >/dev/null 2>&1; then
  ts5_die "Docker Compose v2 is required"
fi

if [[ ! -f "$env_file" ]]; then
  cp "$SCRIPT_DIR/.env.example" "$env_file"
fi

ts5_load_env_file "$env_file"

project_name="${PROJECT_NAME:-telegram-socks5}"
api_port="${API_PORT:-8088}"
socks5_port="${SOCKS5_PORT:-1080}"
enable_mtproto="${ENABLE_MTPROTO:-true}"
mtproto_port="${MTPROTO_PORT:-443}"
mtproto_stats_port="${MTPROTO_STATS_PORT:-8888}"
mtproto_client_secret="$(ts5_empty_if_placeholder "${MTPROTO_CLIENT_SECRET:-}")"
mtproto_tag="${MTPROTO_TAG:-}"
public_api_host="${PUBLIC_API_HOST:-127.0.0.1}"
api_base_url="${API_BASE_URL:-http://${public_api_host}:${api_port}}"
superadmin_username="${SUPERADMIN_USERNAME:-superadmin}"
superadmin_password="$(ts5_empty_if_placeholder "${SUPERADMIN_PASSWORD:-}")"
initial_admin_username="${INITIAL_ADMIN_USERNAME:-admin}"
initial_admin_password="$(ts5_empty_if_placeholder "${INITIAL_ADMIN_PASSWORD:-}")"
jwt_secret="$(ts5_empty_if_placeholder "${JWT_SECRET:-}")"
jwt_algorithm="${JWT_ALGORITHM:-HS256}"
jwt_expires_minutes="${JWT_EXPIRES_MINUTES:-120}"
data_dir="${DATA_DIR:-./data}"

if (( auto_mode )); then
  SOCKS5_PORT="$socks5_port"
  API_PORT="$api_port"
  PUBLIC_API_HOST="$public_api_host"
  API_BASE_URL="http://${PUBLIC_API_HOST}:${API_PORT}"
  SUPERADMIN_USERNAME="$superadmin_username"
  SUPERADMIN_PASSWORD="${superadmin_password:-$(ts5_generate_secret)}"
  INITIAL_ADMIN_USERNAME="$initial_admin_username"
  INITIAL_ADMIN_PASSWORD="${initial_admin_password:-$(ts5_generate_secret)}"
else
  SOCKS5_PORT="$(ts5_prompt 'SOCKS5 port' "$socks5_port")"
  API_PORT="$(ts5_prompt 'API port' "$api_port")"
  PUBLIC_API_HOST="$(ts5_prompt 'Public API host for scripts' "$public_api_host")"
  API_BASE_URL="http://${PUBLIC_API_HOST}:${API_PORT}"
  SUPERADMIN_USERNAME="$(ts5_prompt 'Superadmin username' "$superadmin_username")"
  if [[ -z "$superadmin_password" ]]; then
    SUPERADMIN_PASSWORD="$(ts5_prompt_secret 'Superadmin password')"
  else
    SUPERADMIN_PASSWORD="$superadmin_password"
  fi

  INITIAL_ADMIN_USERNAME="$(ts5_prompt 'Initial admin username' "$initial_admin_username")"
  if [[ -z "$initial_admin_password" ]]; then
    INITIAL_ADMIN_PASSWORD="$(ts5_prompt_secret 'Initial admin password')"
  else
    INITIAL_ADMIN_PASSWORD="$initial_admin_password"
  fi
fi

ENABLE_MTPROTO="$enable_mtproto"
MTPROTO_PORT="$mtproto_port"
MTPROTO_STATS_PORT="$mtproto_stats_port"
MTPROTO_TAG="$mtproto_tag"
if [[ -z "$mtproto_client_secret" ]]; then
  MTPROTO_CLIENT_SECRET="$(ts5_generate_hex_secret)"
else
  MTPROTO_CLIENT_SECRET="$(ts5_normalize_mtproto_secret "$mtproto_client_secret")"
fi

if [[ -z "$jwt_secret" ]]; then
  JWT_SECRET="$(ts5_generate_secret)"
else
  JWT_SECRET="$jwt_secret"
fi

if ts5_port_in_use "$SOCKS5_PORT"; then
  ts5_die "Port $SOCKS5_PORT is already in use"
fi

if ts5_port_in_use "$API_PORT"; then
  ts5_die "Port $API_PORT is already in use"
fi

if [[ "$ENABLE_MTPROTO" == "true" ]] && ts5_port_in_use "$MTPROTO_PORT"; then
  ts5_die "Port $MTPROTO_PORT is already in use"
fi

cat >"$env_file" <<EOF
PROJECT_NAME=$project_name
PUBLIC_API_HOST=$PUBLIC_API_HOST
API_PORT=$API_PORT
API_BASE_URL=$API_BASE_URL
SOCKS5_PORT=$SOCKS5_PORT
DATA_DIR=$data_dir
SUPERADMIN_USERNAME=$SUPERADMIN_USERNAME
SUPERADMIN_PASSWORD=$SUPERADMIN_PASSWORD
INITIAL_ADMIN_USERNAME=$INITIAL_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD=$INITIAL_ADMIN_PASSWORD
SOCKS5_USERS_FILE=/data/users.json
SOCKS5_PROXY_CONFIG_FILE=/data/3proxy.cfg
SOCKS5_PROXY_PID_FILE=/data/3proxy.pid
SOCKS5_PROXY_LOG_FILE=/data/3proxy.log
SOCKS5_PROXY_RELOAD_REQUEST_FILE=/data/reload.request
SOCKS5_PROXY_RELOAD_STATUS_FILE=/data/reload.status
JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=$jwt_algorithm
JWT_EXPIRES_MINUTES=$jwt_expires_minutes
ENABLE_MTPROTO=$ENABLE_MTPROTO
MTPROTO_PORT=$MTPROTO_PORT
MTPROTO_STATS_PORT=$MTPROTO_STATS_PORT
MTPROTO_CLIENT_SECRET=$MTPROTO_CLIENT_SECRET
MTPROTO_TAG=$MTPROTO_TAG
SMOKE_TEST_URL=${SMOKE_TEST_URL:-https://api.ipify.org?format=json}
EOF
chmod 600 "$env_file"

mkdir -p "$SCRIPT_DIR/${data_dir#./}"

printf 'docker compose --project-name %s --env-file %s -f %s up -d --build\n' "$project_name" "$env_file" "$compose_file"
compose_args=(up -d --build)
if [[ "$ENABLE_MTPROTO" == "true" ]]; then
  compose_args=(--profile mtproto "${compose_args[@]}")
fi
PROJECT_NAME="$project_name" ts5_compose "$env_file" "$compose_file" "${compose_args[@]}"

printf 'Bootstrapping initial admin inside API container\n'
PROJECT_NAME="$project_name" ts5_compose "$env_file" "$compose_file" exec -T api \
  python -m telegram_socks5_api.cli bootstrap \
  --admin-username "$INITIAL_ADMIN_USERNAME" \
  --admin-password "$INITIAL_ADMIN_PASSWORD"

printf '\nDeployment completed.\n'
printf 'API:   %s\n' "$API_BASE_URL"
printf 'Admin: %s\n' "$API_BASE_URL"
printf 'SOCKS: socks5://<user>:<password>@127.0.0.1:%s\n' "$SOCKS5_PORT"
if [[ "$ENABLE_MTPROTO" == "true" ]]; then
  printf 'MTProto: tg://proxy?server=%s&port=%s&secret=%s\n' \
    "$PUBLIC_API_HOST" "$MTPROTO_PORT" "$(ts5_mtproto_link_secret "$MTPROTO_CLIENT_SECRET")"
fi
printf 'Superadmin: %s\n' "$SUPERADMIN_USERNAME"
printf 'Initial admin: %s\n' "$INITIAL_ADMIN_USERNAME"
printf 'Login test: %s/login.sh --json\n' "$SCRIPT_DIR"

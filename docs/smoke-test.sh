#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$DOCS_DIR/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT_DIR/telegram-socks5-common.sh"

usage() {
  cat <<'EOF'
Usage: smoke-test.sh [--api-url URL] [--socks-host HOST] [--socks-port PORT] [--smoke-url URL]
EOF
}

ts5_load_env_file "$(ts5_env_file_default)"

api_url="$(ts5_api_url_default)"
socks_host="${SOCKS_HOST:-127.0.0.1}"
socks_port="${SOCKS5_PORT:-1080}"
smoke_url="${SMOKE_TEST_URL:-https://api.ipify.org?format=json}"
admin_username="${ADMIN_USERNAME:-${SUPERADMIN_USERNAME:-}}"
admin_password="$(ts5_empty_if_placeholder "${ADMIN_PASSWORD:-${SUPERADMIN_PASSWORD:-}}")"
temp_username=""
temp_password=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url)
      api_url="$2"
      shift 2
      ;;
    --socks-host)
      socks_host="$2"
      shift 2
      ;;
    --socks-port)
      socks_port="$2"
      shift 2
      ;;
    --smoke-url)
      smoke_url="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      ts5_die "Unknown argument: $1"
      ;;
    *)
      ts5_die "Unexpected argument: $1"
      ;;
  esac
done

ts5_require_bins curl jq

if [[ -z "$admin_username" ]]; then
  admin_username="$(ts5_prompt 'Admin username')"
fi

if [[ -z "$admin_password" ]]; then
  admin_password="$(ts5_prompt_secret 'Admin password')"
fi

token="$(ts5_login_token "$api_url" "$admin_username" "$admin_password")"

temp_username="smoke-$(tr -dc 'a-z0-9' </dev/urandom | head -c 8)"
temp_password="$(ts5_generate_secret)"
cleanup() {
  if [[ -n "${temp_username:-}" ]]; then
    encoded_username="$(ts5_urlencode "$temp_username")"
    ts5_api_call "$api_url" DELETE "/proxy-users/$encoded_username" "$token" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

printf 'Creating temporary proxy user %s\n' "$temp_username"
create_payload="$(jq -n --arg username "$temp_username" --arg password "$temp_password" '{username: $username, password: $password, enabled: true}')"
ts5_api_call "$api_url" POST '/proxy-users' "$token" "$create_payload" >/dev/null

printf 'Checking /health\n'
ts5_api_call "$api_url" GET '/health' "$token" >/dev/null

printf 'Checking /proxy-users\n'
ts5_api_call "$api_url" GET '/proxy-users' "$token" | jq .

printf 'Checking SOCKS5 proxy through %s:%s\n' "$socks_host" "$socks_port"
curl -fsS \
  --proxy "socks5h://$temp_username:$temp_password@$socks_host:$socks_port" \
  "$smoke_url" >/dev/null

printf 'Smoke test passed.\n'

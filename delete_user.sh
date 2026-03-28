#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/telegram-socks5-common.sh"

usage() {
  cat <<'EOF'
Usage: delete_user.sh [--api-url URL] [--admin-user USER] [--admin-password PASS] USERNAME
EOF
}

ts5_load_env_file "$(ts5_env_file_default)"

api_url="$(ts5_api_url_default)"
admin_username="${ADMIN_USERNAME:-${SUPERADMIN_USERNAME:-}}"
admin_password="$(ts5_empty_if_placeholder "${ADMIN_PASSWORD:-${SUPERADMIN_PASSWORD:-}}")"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url)
      api_url="$2"
      shift 2
      ;;
    --admin-user)
      admin_username="$2"
      shift 2
      ;;
    --admin-password)
      admin_password="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      ts5_die "Unknown argument: $1"
      ;;
    *)
      break
      ;;
  esac
done

username="${1:-}"

ts5_require_bins curl jq

if [[ -z "$username" ]]; then
  usage
  exit 1
fi

if [[ -z "$admin_username" ]]; then
  admin_username="$(ts5_prompt 'Admin username')"
fi

if [[ -z "$admin_password" ]]; then
  admin_password="$(ts5_prompt_secret 'Admin password')"
fi

token="$(ts5_login_token "$api_url" "$admin_username" "$admin_password")"
encoded_username="$(ts5_urlencode "$username")"
response="$(ts5_api_call "$api_url" DELETE "/proxy-users/$encoded_username" "$token")"
printf '%s\n' "$response" | jq .

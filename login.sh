#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/telegram-socks5-common.sh"

usage() {
  cat <<'EOF'
Usage: login.sh [--api-url URL] [--username USER] [--password PASS] [--json]
EOF
}

ts5_load_env_file "$(ts5_env_file_default)"

api_url="$(ts5_api_url_default)"
username="${ADMIN_USERNAME:-${SUPERADMIN_USERNAME:-}}"
password="$(ts5_empty_if_placeholder "${ADMIN_PASSWORD:-${SUPERADMIN_PASSWORD:-}}")"
output_json=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url)
      api_url="$2"
      shift 2
      ;;
    --username)
      username="$2"
      shift 2
      ;;
    --password)
      password="$2"
      shift 2
      ;;
    --json)
      output_json=1
      shift
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

ts5_require_bins curl jq

if [[ -z "$username" ]]; then
  username="$(ts5_prompt 'Admin username')"
fi

if [[ -z "$password" ]]; then
  password="$(ts5_prompt_secret 'Admin password')"
fi

response="$(curl -fsS \
  -X POST "${api_url%/}/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg username "$username" --arg password "$password" '{username: $username, password: $password}')" \
)"

if (( output_json )); then
  printf '%s\n' "$response" | jq .
else
  printf '%s\n' "$response" | jq -er '.access_token'
fi

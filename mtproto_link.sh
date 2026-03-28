#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/telegram-socks5-common.sh"

env_file="$(ts5_env_file_default)"
ts5_load_env_file "$env_file"

public_host="${PUBLIC_API_HOST:-127.0.0.1}"
mtproto_port="${MTPROTO_PORT:-443}"
mtproto_secret="${MTPROTO_CLIENT_SECRET:-}"

if [[ -z "$mtproto_secret" ]]; then
  ts5_die "MTPROTO_CLIENT_SECRET is not set in $env_file"
fi

printf 'tg://proxy?server=%s&port=%s&secret=%s\n' \
  "$public_host" "$mtproto_port" "$(ts5_mtproto_link_secret "$mtproto_secret")"

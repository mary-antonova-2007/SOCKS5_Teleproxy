#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/telegram-socks5-common.sh"

usage() {
  cat <<'EOF'
Usage: uninstall.sh [--env-file FILE] [--compose-file FILE] [--purge-data] [--yes]
EOF
}

env_file="$(ts5_env_file_default)"
compose_file="$(ts5_compose_file_default)"
purge_data=0
assume_yes=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      env_file="$2"
      shift 2
      ;;
    --compose-file)
      compose_file="$2"
      shift 2
      ;;
    --purge-data)
      purge_data=1
      shift
      ;;
    --yes|-y)
      assume_yes=1
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

ts5_load_env_file "$env_file"
project_name="${PROJECT_NAME:-telegram-socks5}"
data_dir="${DATA_DIR:-./data}"

if [[ -f "$compose_file" ]]; then
  ts5_require_bins docker
  PROJECT_NAME="$project_name" ts5_compose "$env_file" "$compose_file" down -v --remove-orphans || true
fi

if (( assume_yes == 0 )) && (( purge_data == 0 )); then
  read -r -p "Remove .env and data directory too? [y/N]: " reply
  case "${reply,,}" in
    y|yes) purge_data=1 ;;
  esac
fi

if (( purge_data )); then
  rm -f "$env_file"
  rm -rf "$SCRIPT_DIR/${data_dir#./}"
  printf 'Removed %s and %s\n' "$env_file" "$SCRIPT_DIR/${data_dir#./}"
else
  printf 'Containers removed, env and data kept.\n'
fi

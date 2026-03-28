#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-git@github.com:mary-antonova-2007/SOCKS5_Teleproxy.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
APP_DIR="${APP_DIR:-/opt/SOCKS5_TeleProxy}"
RUN_USER="${RUN_USER:-${SUDO_USER:-root}}"
AUTO_START="${AUTO_START:-1}"

log() {
  printf '[bootstrap] %s\n' "$*"
}

die() {
  printf '[bootstrap] ERROR: %s\n' "$*" >&2
  exit 1
}

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    die "Run this script as root or via sudo."
  fi
}

detect_pkg_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    printf 'apt\n'
    return
  fi
  if command -v dnf >/dev/null 2>&1; then
    printf 'dnf\n'
    return
  fi
  if command -v yum >/dev/null 2>&1; then
    printf 'yum\n'
    return
  fi
  die "Supported package manager not found. Supported: apt, dnf, yum."
}

install_base_packages() {
  local manager="$1"
  case "$manager" in
    apt)
      export DEBIAN_FRONTEND=noninteractive
      apt-get update -y
      apt-get install -y ca-certificates curl git jq openssh-client gnupg lsb-release
      ;;
    dnf)
      dnf install -y ca-certificates curl git jq openssh-clients dnf-plugins-core
      ;;
    yum)
      yum install -y ca-certificates curl git jq openssh-clients yum-utils
      ;;
  esac
}

install_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    log "Docker and Docker Compose are already installed."
    return
  fi

  local manager="$1"
  case "$manager" in
    apt)
      install -m 0755 -d /etc/apt/keyrings
      if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
      fi
      . /etc/os-release
      printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/%s %s stable\n' \
        "$(dpkg --print-architecture)" "${ID}" "${VERSION_CODENAME}" >/etc/apt/sources.list.d/docker.list
      apt-get update -y
      apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      ;;
    dnf)
      dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      ;;
    yum)
      yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      ;;
  esac

  systemctl enable --now docker
}

prepare_workspace() {
  mkdir -p "$(dirname "$APP_DIR")"

  if [[ -d "$APP_DIR/.git" ]]; then
    log "Repository already exists, updating branch $REPO_BRANCH."
    git -C "$APP_DIR" fetch --all --prune
    git -C "$APP_DIR" checkout "$REPO_BRANCH"
    git -C "$APP_DIR" pull --ff-only origin "$REPO_BRANCH"
    return
  fi

  if [[ -e "$APP_DIR" && ! -d "$APP_DIR/.git" ]]; then
    die "$APP_DIR exists but is not a git repository."
  fi

  log "Cloning $REPO_URL into $APP_DIR."
  git clone --branch "$REPO_BRANCH" "$REPO_URL" "$APP_DIR"
}

configure_permissions() {
  chmod +x "$APP_DIR"/deploy.sh "$APP_DIR"/uninstall.sh "$APP_DIR"/login.sh \
    "$APP_DIR"/create_user.sh "$APP_DIR"/delete_user.sh "$APP_DIR"/list_users.sh \
    "$APP_DIR"/docs/smoke-test.sh "$APP_DIR"/server-bootstrap.sh

  if id "$RUN_USER" >/dev/null 2>&1; then
    usermod -aG docker "$RUN_USER" || true
    chown -R "$RUN_USER":"$RUN_USER" "$APP_DIR"
  fi
}

run_deploy() {
  if [[ "$AUTO_START" != "1" ]]; then
    log "AUTO_START=0, skipping deploy.sh execution."
    return
  fi

  log "Starting automatic deployment."
  (
    cd "$APP_DIR"
    ./deploy.sh --auto
  )
}

print_summary() {
  cat <<EOF

Bootstrap finished.
Project directory: $APP_DIR
Repository: $REPO_URL
Branch: $REPO_BRANCH

If passwords were not passed via environment variables, generated values are stored in:
  $APP_DIR/.env

Open the admin panel after deploy:
  http://${PUBLIC_API_HOST:-127.0.0.1}:${API_PORT:-8088}

If you added $RUN_USER to docker group, re-login for group changes to apply.
EOF
}

main() {
  require_root
  local manager
  manager="$(detect_pkg_manager)"
  install_base_packages "$manager"
  install_docker "$manager"
  prepare_workspace
  configure_permissions
  run_deploy
  print_summary
}

main "$@"

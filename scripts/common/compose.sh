#!/usr/bin/env bash
set -euo pipefail
# shellcheck source=./env.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/env.sh"

# normalize compose command (supports "docker compose" or "docker-compose")
_compose_raw="${COMPOSE_BIN:-docker compose}"
read -r -a _compose_cmd <<<"$_compose_raw"
if ! command -v "${_compose_cmd[0]}" >/dev/null 2>&1; then
  if command -v docker-compose >/dev/null 2>&1; then
    _compose_cmd=(docker-compose)
  else
    echo "[FATAL] docker compose or docker-compose not found. Set COMPOSE_BIN explicitly." >&2
    exit 127
  fi
fi

compose_dev() {
  "${_compose_cmd[@]}" --project-directory "$ROOT_DIR" -p "$PROJECT" -f "$ROOT_DIR/docker-compose.yml" "$@"
}

compose_ci() {
  "${_compose_cmd[@]}" --project-directory "$ROOT_DIR" -p "$PROJECT_CI" \
    -f "$ROOT_DIR/docker-compose.yml" -f "$ROOT_DIR/docker-compose.ci.yml" \
    --profile ci \
    "$@"
}

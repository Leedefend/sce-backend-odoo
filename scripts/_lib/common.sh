#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

# ---- defaults to support manual sourcing (without Makefile RUN_ENV) ----
: "${COMPOSE_BIN:=}"
: "${COMPOSE_PROJECT_NAME:=sc-backend-odoo}"
: "${PROJECT:=${COMPOSE_PROJECT_NAME}}"
: "${COMPOSE_FILE_BASE:=docker-compose.yml}"
: "${COMPOSE_FILES:=-f ${COMPOSE_FILE_BASE}}"

# 把 "sc_gate,sc_perm,/mod:tag" 统一转换为 "/MODULE:tag" 形式
normalize_test_tags() {
  local module="$1"
  local raw="${2:-}"
  raw="${raw// /}"          # 去空格
  raw="${raw#,}"            # 去头逗号
  raw="${raw%,}"            # 去尾逗号
  [[ -z "$raw" ]] && { echo ""; return 0; }

  IFS=',' read -r -a parts <<< "$raw"
  local out=()
  local p
  for p in "${parts[@]}"; do
    [[ -z "$p" ]] && continue
    if [[ "$p" == /*:* ]]; then
      out+=("$p")
    else
      # 同时保留裸 tag，确保 Odoo 解析（sc_gate,sc_perm 等）
      out+=("/${module}:${p}")
      out+=("$p")
    fi
  done

  local joined
  joined="$(IFS=','; echo "${out[*]}")"
  echo "$joined"
}

compose() {
  local cmd=()
  local proj="${PROJECT:-${COMPOSE_PROJECT_NAME:-sc-backend-odoo}}"
  local files="${COMPOSE_FILES:--f docker-compose.yml}"
  if [[ -n "${COMPOSE_BIN:-}" ]]; then
    read -r -a cmd <<<"${COMPOSE_BIN}"
  elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    cmd=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
    cmd=(docker-compose)
  else
    echo "[FATAL] docker compose or docker-compose not available" >&2
    exit 127
  fi
  # preserve arguments (including embedded spaces/newlines)
  # shellcheck disable=SC2086
  "${cmd[@]}" -p "${proj}" ${files} "$@"
}

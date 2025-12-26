#!/usr/bin/env bash
set -euo pipefail

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

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
  # preserve arguments (including embedded spaces/newlines)
  ${COMPOSE_BIN} -p "${PROJECT}" "$@"
}

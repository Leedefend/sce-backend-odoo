#!/usr/bin/env bash
set -euo pipefail

is_prod() {
  if [[ "${ENV:-}" == "prod" ]]; then
    return 0
  fi
  if [[ "${ENV_FILE:-}" == *".env.prod" ]]; then
    return 0
  fi
  return 1
}

guard_prod_forbid() {
  if is_prod; then
    echo "❌ forbidden in prod. Set ENV=dev or use a safe environment." >&2
    exit 2
  fi
}

guard_prod_danger() {
  if is_prod; then
    if [[ "${PROD_DANGER:-}" != "1" ]]; then
      echo "❌ prod danger guard: set PROD_DANGER=1 to proceed." >&2
      exit 2
    fi
  fi
}

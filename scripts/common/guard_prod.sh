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

guard_seed_profile_prod() {
  if is_prod; then
    local profile="${PROFILE:-}"
    if [[ -n "${profile}" && "${profile}" != "base" ]]; then
      echo "❌ prod seed guard: PROFILE must be 'base' (got '${profile}')." >&2
      exit 2
    fi
  fi
}

guard_seed_bootstrap_prod() {
  if is_prod; then
    if [[ "${SC_BOOTSTRAP_USERS:-}" =~ ^(1|true|True|yes|YES)$ ]] && [[ "${SEED_ALLOW_USERS_BOOTSTRAP:-}" != "1" ]]; then
      echo "❌ prod seed guard: set SEED_ALLOW_USERS_BOOTSTRAP=1 to allow users_bootstrap." >&2
      exit 2
    fi
  fi
}

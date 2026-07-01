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

guard_seed_db_explicit_prod() {
  if is_prod; then
    if [[ "${SEED_DB_NAME_EXPLICIT:-}" != "1" ]]; then
      echo "❌ prod seed guard: set SEED_DB_NAME_EXPLICIT=1 and pass DB_NAME explicitly." >&2
      exit 2
    fi
  fi
}

is_demo_db() {
  local db="${DB_NAME:-${DB:-}}"
  case "${db}" in
    sc_demo|sc_test|sc_demo_*|sc_test_*)
      return 0
      ;;
  esac
  return 1
}

is_truthy() {
  [[ "${1:-}" =~ ^(1|true|True|yes|YES)$ ]]
}

is_daily_dev_project() {
  [[ "${COMPOSE_PROJECT_NAME:-${PROJECT:-}}" == "sc-backend-odoo-dev" ]]
}

guard_demo_module_db() {
  local module="${MODULE:-}"
  if [[ ",${module}," != *",smart_construction_demo,"* ]]; then
    return 0
  fi
  if is_truthy "${SC_ALLOW_DEMO_DATA:-}"; then
    return 0
  fi
  if is_daily_dev_project; then
    echo "❌ demo data guard: smart_construction_demo is forbidden in daily dev project ${COMPOSE_PROJECT_NAME:-${PROJECT:-}}. Set SC_ALLOW_DEMO_DATA=1 only for an intentional demo rebuild." >&2
    exit 2
  fi
  if is_demo_db; then
    return 0
  fi
  echo "❌ demo data guard: smart_construction_demo is forbidden for DB_NAME=${DB_NAME:-}. Use sc_demo/sc_test or set SC_ALLOW_DEMO_DATA=1 intentionally." >&2
  exit 2
}

guard_seed_demo_steps_db() {
  local selected="${PROFILE:-}${STEPS:-}"
  if [[ ! "${selected}" =~ (demo|showroom) ]]; then
    return 0
  fi
  if is_truthy "${SC_ALLOW_DEMO_DATA:-}"; then
    return 0
  fi
  if is_daily_dev_project; then
    echo "❌ demo data guard: demo/showroom seed steps are forbidden in daily dev project ${COMPOSE_PROJECT_NAME:-${PROJECT:-}}. Set SC_ALLOW_DEMO_DATA=1 only for an intentional demo rebuild." >&2
    exit 2
  fi
  if is_demo_db; then
    return 0
  fi
  echo "❌ demo data guard: demo/showroom seed steps are forbidden for DB_NAME=${DB_NAME:-}. Use sc_demo/sc_test or set SC_ALLOW_DEMO_DATA=1 intentionally." >&2
  exit 2
}

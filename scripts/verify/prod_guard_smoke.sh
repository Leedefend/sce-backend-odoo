#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT_DIR"
DB_TARGET="${DB_NAME:-sc_demo}"

expect_fail() {
  local name="$1"; shift
  local out
  if out="$("$@" 2>&1)"; then
    echo "[prod.guard] FAIL expected fail: ${name}"
    echo "$out"
    exit 1
  fi
  GUARD_EXPECTED_FAIL=$((GUARD_EXPECTED_FAIL + 1))
  GUARD_PASS=$((GUARD_PASS + 1))
  echo "[prod.guard] PASS expected fail: ${name}"
}

expect_no_guard() {
  local name="$1"; shift
  local out
  set +e
  out="$("$@" 2>&1)"
  local rc=$?
  set -e
  if echo "$out" | grep -q "prod danger guard"; then
    echo "[prod.guard] FAIL guard blocked: ${name}"
    echo "$out"
    exit 1
  fi
  if [[ "${rc}" -ne 0 ]]; then
    BUSINESS_FAIL=$((BUSINESS_FAIL + 1))
  fi
  GUARD_PASS=$((GUARD_PASS + 1))
  echo "[prod.guard] PASS guard cleared (business rc=${rc}): ${name}"
}

GUARD_TOTAL=0
GUARD_PASS=0
GUARD_EXPECTED_FAIL=0
BUSINESS_FAIL=0

run_fail() { GUARD_TOTAL=$((GUARD_TOTAL + 1)); expect_fail "$@"; }
run_clear() { GUARD_TOTAL=$((GUARD_TOTAL + 1)); expect_no_guard "$@"; }

ENV=prod ENV_FILE=.env.prod run_fail "make db.reset" make db.reset DB_NAME=sc_demo
ENV=prod ENV_FILE=.env.prod run_fail "make mod.upgrade (no unlock)" make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_demo
ENV=prod ENV_FILE=.env.prod PROD_DANGER=1 run_clear "make mod.upgrade (unlock)" make mod.upgrade MODULE=smart_construction_core DB_NAME=__guard_smoke__
ENV=prod ENV_FILE=.env.prod run_fail "script db/reset" bash scripts/db/reset.sh
ENV=prod ENV_FILE=.env.prod run_fail "seed.run profile demo_full" PROFILE=demo_full make seed.run DB_NAME="${DB_TARGET}"
ENV=prod ENV_FILE=.env.prod run_fail "seed.run without explicit db" PROFILE=base make seed.run DB_NAME="${DB_TARGET}"
ENV=prod ENV_FILE=.env.prod run_fail "seed.run users_bootstrap without allow" PROFILE=base SC_BOOTSTRAP_USERS=1 make seed.run DB_NAME="${DB_TARGET}"
ENV=prod ENV_FILE=.env.prod SEED_DB_NAME_EXPLICIT=1 SEED_GUARD_ONLY=1 SEED_ALLOW_USERS_BOOTSTRAP=1 SC_BOOTSTRAP_USERS=1 PROFILE=base run_clear "seed.run users_bootstrap with allow" make seed.run DB_NAME="${DB_TARGET}"

echo "[prod.guard] SUMMARY guard_tests=${GUARD_TOTAL} pass=${GUARD_PASS} guard_fail_expected=${GUARD_EXPECTED_FAIL} business_fail=${BUSINESS_FAIL}"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
env_name="${ENV:-}"
db_name="${DB_TARGET}"
git_sha="${GIT_SHA:-}"
if [[ -z "${git_sha}" ]] && command -v git >/dev/null 2>&1; then
  git_sha="$(git rev-parse --short HEAD 2>/dev/null || true)"
fi
rc=0
printf '{"guard_tests":%s,"pass":%s,"guard_fail_expected":%s,"business_fail":%s,"timestamp":"%s","env":"%s","db_name":"%s","rc":%s,"git_sha":"%s"}\n' \
  "${GUARD_TOTAL}" "${GUARD_PASS}" "${GUARD_EXPECTED_FAIL}" "${BUSINESS_FAIL}" "${timestamp}" "${env_name}" "${db_name}" "${rc}" "${git_sha}"

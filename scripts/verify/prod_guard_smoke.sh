#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT_DIR"

expect_fail() {
  local name="$1"; shift
  local out
  if out="$("$@" 2>&1)"; then
    echo "[prod.guard] FAIL expected fail: ${name}"
    echo "$out"
    exit 1
  fi
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
  echo "[prod.guard] PASS guard cleared: ${name} (rc=${rc})"
}

ENV=prod ENV_FILE=.env.prod expect_fail "make db.reset" make db.reset DB_NAME=sc_demo
ENV=prod ENV_FILE=.env.prod expect_fail "make mod.upgrade (no unlock)" make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_demo
ENV=prod ENV_FILE=.env.prod PROD_DANGER=1 expect_no_guard "make mod.upgrade (unlock)" make mod.upgrade MODULE=smart_construction_core DB_NAME=__guard_smoke__
ENV=prod ENV_FILE=.env.prod expect_fail "script db/reset" bash scripts/db/reset.sh
ENV=prod ENV_FILE=.env.prod expect_fail "seed.run profile demo_full" PROFILE=demo_full make seed.run DB_NAME=sc_demo
ENV=prod ENV_FILE=.env.prod expect_fail "seed.run users_bootstrap without allow" PROFILE=base SC_BOOTSTRAP_USERS=1 make seed.run DB_NAME=sc_demo
ENV=prod ENV_FILE=.env.prod SEED_ALLOW_USERS_BOOTSTRAP=1 SC_BOOTSTRAP_USERS=1 PROFILE=base expect_no_guard "seed.run users_bootstrap with allow" make seed.run DB_NAME=sc_demo

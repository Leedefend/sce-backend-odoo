#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8070}"
DB_NAME="${DB_NAME:-sc_demo}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
E2E_LOGIN="${E2E_LOGIN:-admin}"
E2E_PASSWORD="${E2E_PASSWORD:-admin}"

ts() {
  date +"%H:%M:%S"
}

echo "[$(ts)] fe_smoke: base=${BASE_URL} db=${DB_NAME}"

if [[ -z "${AUTH_TOKEN}" && -n "${E2E_LOGIN}" && -n "${E2E_PASSWORD}" ]]; then
  login_payload='{"intent":"login","params":{"db":"'"${DB_NAME}"'","login":"'"${E2E_LOGIN}"'","password":"'"${E2E_PASSWORD}"'"}}'
  login_status="$(
    curl -sS -o /tmp/fe_smoke_login.json -w "%{http_code}" \
      -H "Content-Type: application/json" \
      -H "X-Anonymous-Intent: 1" \
      -d "${login_payload}" \
      "${BASE_URL}/api/v1/intent" || true
  )"
  if [[ "${login_status}" != "200" ]]; then
    echo "[$(ts)] FAIL: login status=${login_status}"
    if [[ -f /tmp/fe_smoke_login.json ]]; then
      echo "login response:"
      cat /tmp/fe_smoke_login.json
    fi
    exit 1
  fi
  AUTH_TOKEN="$(python3 - <<'PY'
import json
import sys
try:
  data=json.load(open("/tmp/fe_smoke_login.json"))
except Exception:
  sys.exit(0)
token=(data.get("data") or {}).get("token") or ""
print(token)
PY
)"
  if [[ -z "${AUTH_TOKEN}" ]]; then
    echo "[$(ts)] FAIL: login token missing"
    exit 1
  fi
fi

payload='{"intent":"app.init","params":{"scene":"web","with_preload":false,"root_xmlid":"smart_construction_core.menu_sc_root"}}'

auth_header=()
if [[ -n "${AUTH_TOKEN}" ]]; then
  auth_header=(-H "Authorization: Bearer ${AUTH_TOKEN}")
fi

status_code="$(
  curl -sS -o /tmp/fe_smoke_resp.json -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "X-Odoo-DB: ${DB_NAME}" \
    "${auth_header[@]}" \
    -d "${payload}" \
    "${BASE_URL}/api/v1/intent" || true
)"

if [[ "${status_code}" != "200" ]]; then
  echo "[$(ts)] FAIL: status=${status_code}"
  if [[ -f /tmp/fe_smoke_resp.json ]]; then
    echo "response:"
    cat /tmp/fe_smoke_resp.json
  fi
  exit 1
fi

nav_version="$(python3 - <<'PY'
import json
import sys
try:
  data=json.load(open("/tmp/fe_smoke_resp.json"))
except Exception:
  sys.exit(0)
meta=data.get("meta") or {}
nav_meta=data.get("nav_meta") or {}
print(meta.get("nav_version") or nav_meta.get("menu") or meta.get("parts",{}).get("nav") or "")
PY
)"

trace_id="$(python3 - <<'PY'
import json
import sys
try:
  data=json.load(open("/tmp/fe_smoke_resp.json"))
except Exception:
  sys.exit(0)
meta=data.get("meta") or {}
print(meta.get("trace_id") or meta.get("traceId") or "")
PY
)"

echo "[$(ts)] OK: app.init 200"
echo "nav_version=${nav_version}"
echo "trace_id=${trace_id}"

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
  login_next_intent="$(python3 - <<'PY'
import json
import sys
try:
  data=json.load(open("/tmp/fe_smoke_login.json"))
except Exception:
  sys.exit(0)
payload=(data.get("data") or {})
bootstrap=payload.get("bootstrap") or {}
print(bootstrap.get("next_intent") or "")
PY
)"
  if [[ "${login_next_intent}" != "system.init" && "${login_next_intent}" != "session.bootstrap" ]]; then
    echo "[$(ts)] FAIL: login bootstrap.next_intent invalid (${login_next_intent})"
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
if not token:
  session=((data.get("data") or {}).get("session") or {})
  token=session.get("token") or ""
print(token)
PY
)"
  if [[ -z "${AUTH_TOKEN}" ]]; then
    echo "[$(ts)] FAIL: login token missing"
    exit 1
  fi
fi

payload='{"intent":"system.init","params":{"scene":"web","with_preload":false,"root_xmlid":"smart_construction_core.menu_sc_root"}}'

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

mapfile -t smoke_fields < <(python3 - <<'PY'
import json
import sys
try:
  envelope=json.load(open("/tmp/fe_smoke_resp.json"))
except Exception:
  sys.exit(0)
payload=(envelope.get("data") or {})
meta=envelope.get("meta") or {}
nav=payload.get("nav") if isinstance(payload.get("nav"), list) else []
default_route=payload.get("default_route") if isinstance(payload.get("default_route"), dict) else {}
role_surface=payload.get("role_surface") if isinstance(payload.get("role_surface"), dict) else {}
landing_path=role_surface.get("landing_path") or ""
landing_scene=role_surface.get("landing_scene_key") or ""
landing_source="default_route"
if not (default_route.get("scene_key") or default_route.get("route")):
  landing_source="role_surface"
for item in (
  meta.get("trace_id") or meta.get("traceId") or "",
  str(len(nav)),
  default_route.get("scene_key") or "",
  default_route.get("route") or "",
  default_route.get("reason") or "",
  landing_scene,
  landing_path,
  landing_source,
):
  print(item)
PY
)

trace_id="${smoke_fields[0]:-}"
nav_count="${smoke_fields[1]:-}"
default_route_scene="${smoke_fields[2]:-}"
default_route_path="${smoke_fields[3]:-}"
default_route_reason="${smoke_fields[4]:-}"
role_landing_scene="${smoke_fields[5]:-}"
role_landing_path="${smoke_fields[6]:-}"
landing_source="${smoke_fields[7]:-}"

if [[ -z "${trace_id}" ]]; then
  echo "[$(ts)] FAIL: system.init trace_id missing"
  exit 1
fi

if [[ "${nav_count}" == "0" || -z "${nav_count}" ]]; then
  echo "[$(ts)] FAIL: system.init nav missing"
  exit 1
fi

if [[ -z "${default_route_scene}" && -z "${default_route_path}" && -z "${role_landing_scene}" && -z "${role_landing_path}" ]]; then
  echo "[$(ts)] FAIL: system.init landing target missing default_route and role_surface fallback"
  exit 1
fi

echo "[$(ts)] OK: login -> system.init 200"
echo "nav_count=${nav_count}"
echo "default_route.scene_key=${default_route_scene}"
echo "default_route.route=${default_route_path}"
echo "default_route.reason=${default_route_reason}"
echo "role_surface.landing_scene_key=${role_landing_scene}"
echo "role_surface.landing_path=${role_landing_path}"
echo "landing_source=${landing_source}"
echo "trace_id=${trace_id}"

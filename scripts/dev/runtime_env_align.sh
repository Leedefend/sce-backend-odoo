#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CHECK_ONLY="false"

if [[ "${1:-}" == "--check-only" ]]; then
  CHECK_ONLY="true"
fi

log() { printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"; }

cd "${ROOT_DIR}"

show_matrix() {
  cat <<'EOF'
Runtime Alignment Matrix:
  - daily(dev): backend=http://localhost:8069 db=sc_demo frontend=http://127.0.0.1:5174 (FRONTEND_PROFILE=daily)
  - test:       backend=http://localhost:8071 db=sc_test frontend=http://127.0.0.1:5174 (FRONTEND_PROFILE=test)
  - uat:        backend=http://localhost:18069 db=sc_prod_sim frontend=http://127.0.0.1:5174 (FRONTEND_PROFILE=uat)
EOF
}

check_db_auth() {
  local base_url="$1"
  local db_name="$2"
  python3 - <<PY
import json, urllib.request, sys
base='${base_url}'
db='${db_name}'
req=urllib.request.Request(base+'/web/session/authenticate',data=json.dumps({'jsonrpc':'2.0','method':'call','params':{'db':db,'login':'admin','password':'admin'},'id':1}).encode(),headers={'Content-Type':'application/json'},method='POST')
try:
    with urllib.request.urlopen(req,timeout=8) as r:
        body=json.loads(r.read().decode())
    uid=((body.get('result') or {}).get('uid') or 0)
    print(f'{base} {db} uid={uid}')
    sys.exit(0 if uid else 2)
except Exception as e:
    print(f'{base} {db} error={type(e).__name__}:{e}')
    sys.exit(3)
PY
}

show_matrix

if [[ "${CHECK_ONLY}" != "true" ]]; then
  log "restart daily(dev) runtime"
  make restart ENV=dev DB_NAME=sc_demo
  log "restart test runtime"
  make restart ENV=test DB_NAME=sc_test
fi

log "verify runtime db auth availability"
check_db_auth "http://localhost:8069" "sc_demo"
check_db_auth "http://localhost:8071" "sc_test"

log "alignment check finished"

#!/usr/bin/env bash
set -euo pipefail

DB_NAME=${DB_NAME:-sc_demo}
MODULE=${MODULE:-smart_construction_custom}

make mod.upgrade MODULE="$MODULE" DB_NAME="$DB_NAME"

docker compose exec -T odoo sh -lc "python3 - <<'PY'
import json
import urllib.request

BASE='http://localhost:8069'
DB='$DB_NAME'
USER='admin'
PWD='admin'

def jsonrpc(service, method, args):
    data = json.dumps({"jsonrpc":"2.0","method":"call","params":{"service":service,"method":method,"args":args},"id":1}).encode()
    req = urllib.request.Request(f"{BASE}/jsonrpc", data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read().decode())
    if 'error' in payload:
        raise RuntimeError(payload['error'])
    return payload.get('result')

uid = jsonrpc('common','login',[DB, USER, PWD])
res = jsonrpc('object','execute_kw',[DB, uid, PWD, 'sc.security.policy', 'apply_business_full_policy', []])
print('apply_business_full_policy:', res)
PY"

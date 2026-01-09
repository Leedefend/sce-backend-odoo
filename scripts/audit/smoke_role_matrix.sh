#!/usr/bin/env bash
set -euo pipefail

DB_NAME=${DB_NAME:-sc_demo}
BASE_URL=${BASE_URL:-http://localhost:8069}

READ_USER=${READ_USER:-demo_role_project_read}
READ_PWD=${READ_PWD:-demo}
USER_USER=${USER_USER:-demo_role_project_user}
USER_PWD=${USER_PWD:-demo}
MANAGER_USER=${MANAGER_USER:-demo_role_project_manager}
MANAGER_PWD=${MANAGER_PWD:-demo}
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PWD=${ADMIN_PWD:-admin}

python3 - <<'PY'
import json
import os
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8069")
DB = os.environ.get("DB_NAME", "sc_demo")

READ_USER = os.environ.get("READ_USER", "demo_role_project_read")
READ_PWD = os.environ.get("READ_PWD", "demo")
USER_USER = os.environ.get("USER_USER", "demo_role_project_user")
USER_PWD = os.environ.get("USER_PWD", "demo")
MANAGER_USER = os.environ.get("MANAGER_USER", "demo_role_project_manager")
MANAGER_PWD = os.environ.get("MANAGER_PWD", "demo")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PWD = os.environ.get("ADMIN_PWD", "admin")

def jsonrpc(service, method, args):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"service": service, "method": method, "args": args},
        "id": 1,
    }).encode()
    req = urllib.request.Request(
        BASE + "/jsonrpc",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")

def login(user, pwd):
    return jsonrpc("common", "login", [DB, user, pwd])

def exec_kw(uid, pwd, model, method, args, kwargs=None):
    return jsonrpc("object", "execute_kw", [DB, uid, pwd, model, method, args, kwargs or {}])

def step(msg):
    print("==", msg)

step("read role: search_read project")
uid = login(READ_USER, READ_PWD)
if not uid:
    raise RuntimeError("login failed for %s" % READ_USER)
exec_kw(uid, READ_PWD, "project.project", "search_read", [[]], {"limit": 1, "fields": ["id", "name"]})

step("read role: create project should fail")
failed = False
try:
    exec_kw(uid, READ_PWD, "project.project", "create", [{"name": "Role Smoke Read"}])
except Exception:
    failed = True
if not failed:
    raise RuntimeError("read role can create project unexpectedly")

step("user role: create project")
uid = login(USER_USER, USER_PWD)
if not uid:
    raise RuntimeError("login failed for %s" % USER_USER)
project_user_id = exec_kw(uid, USER_PWD, "project.project", "create", [{"name": "Role Smoke User"}])
if not project_user_id:
    raise RuntimeError("user role failed to create project")

step("ensure partner for contract")
admin_uid = login(ADMIN_USER, ADMIN_PWD)
if not admin_uid:
    raise RuntimeError("login failed for admin user")
partner_ids = exec_kw(admin_uid, ADMIN_PWD, "res.partner", "search", [[("active", "=", True)]], {"limit": 1})
if partner_ids:
    partner_id = partner_ids[0]
else:
    partner_id = exec_kw(admin_uid, ADMIN_PWD, "res.partner", "create", [{"name": "Role Smoke Partner"}])

step("read role: contract create should fail")
uid_read = login(READ_USER, READ_PWD)
failed = False
try:
    exec_kw(
        uid_read,
        READ_PWD,
        "construction.contract",
        "create",
        [{
            "subject": "Role Smoke Contract (read)",
            "type": "in",
            "project_id": project_user_id,
            "partner_id": partner_id,
        }],
    )
except Exception:
    failed = True
if not failed:
    raise RuntimeError("read role can create contract unexpectedly")

step("user role: create contract + line")
uid_user = login(USER_USER, USER_PWD)
contract_id = exec_kw(
    uid_user,
    USER_PWD,
    "construction.contract",
    "create",
    [{
        "subject": "Role Smoke Contract (user)",
        "type": "in",
        "project_id": project_user_id,
        "partner_id": partner_id,
    }],
)
exec_kw(
    uid_user,
    USER_PWD,
    "construction.contract.line",
    "create",
    [{
        "contract_id": contract_id,
        "qty_contract": 1.0,
        "price_contract": 100.0,
    }],
)

step("manager role: confirm contract")
uid_mgr = login(MANAGER_USER, MANAGER_PWD)
exec_kw(uid_mgr, MANAGER_PWD, "construction.contract", "action_confirm", [[contract_id]])
state = exec_kw(uid_mgr, MANAGER_PWD, "construction.contract", "read", [[contract_id]], {"fields": ["state"]})[0]["state"]
if state != "confirmed":
    raise RuntimeError("manager role failed to confirm contract")

step("manager role: create + unlink project")
uid = login(MANAGER_USER, MANAGER_PWD)
if not uid:
    raise RuntimeError("login failed for %s" % MANAGER_USER)
project_mgr_id = exec_kw(uid, MANAGER_PWD, "project.project", "create", [{"name": "Role Smoke Manager"}])
exec_kw(uid, MANAGER_PWD, "project.project", "unlink", [[project_mgr_id]])

print("OK: role matrix smoke passed")
PY

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

wait_odoo() {
  local base="${BASE_URL}"
  local n=0
  local fallback_base=""
  if [ -z "${BASE_URL:-}" ]; then
    fallback_base="http://localhost:18080"
  fi
  if ! command -v curl >/dev/null 2>&1; then
    python3 - <<'PY'
import os
import time
import urllib.request

base = os.environ.get("BASE_URL", "http://localhost:8069")
fallback = "" if os.environ.get("BASE_URL") else "http://localhost:18080"

def ok(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

for _ in range(60):
    if ok(base + "/web/webclient/version_info"):
        raise SystemExit(0)
    if fallback and ok(fallback + "/web/webclient/version_info"):
        os.environ["BASE_URL"] = fallback
        raise SystemExit(0)
    time.sleep(1)
raise SystemExit("ERROR: odoo not ready after 60s")
PY
    return
  fi

  until curl -fsS "${base}/web/webclient/version_info" >/dev/null 2>&1; do
    n=$((n+1))
    if [ -n "${fallback_base}" ] && curl -fsS "${fallback_base}/web/webclient/version_info" >/dev/null 2>&1; then
      export BASE_URL="${fallback_base}"
      return
    fi
    if [ "$n" -ge 60 ]; then
      echo "ERROR: odoo not ready after 60s"
      exit 2
    fi
    sleep 1
  done
}

wait_odoo

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

step("env check")
jsonrpc("common", "version", [])
uid_read = login(READ_USER, READ_PWD)
uid_user = login(USER_USER, USER_PWD)
uid_manager = login(MANAGER_USER, MANAGER_PWD)
admin_uid = login(ADMIN_USER, ADMIN_PWD)
if not uid_read:
    raise RuntimeError("login failed for %s" % READ_USER)
if not uid_user:
    raise RuntimeError("login failed for %s" % USER_USER)
if not uid_manager:
    raise RuntimeError("login failed for %s" % MANAGER_USER)
if not admin_uid:
    raise RuntimeError("login failed for %s" % ADMIN_USER)

step("read role: search_read project")
exec_kw(uid_read, READ_PWD, "project.project", "search_read", [[]], {"limit": 1, "fields": ["id", "name"]})

step("read role: create project should fail")
failed = False
try:
    exec_kw(uid_read, READ_PWD, "project.project", "create", [{"name": "Role Smoke Read"}])
except Exception:
    failed = True
if not failed:
    raise RuntimeError("read role can create project unexpectedly")

step("user role: create project")
project_user_id = exec_kw(uid_user, USER_PWD, "project.project", "create", [{"name": "Role Smoke User"}])
if not project_user_id:
    raise RuntimeError("user role failed to create project")

step("ensure partner for contract")
partner_ids = exec_kw(admin_uid, ADMIN_PWD, "res.partner", "search", [[("active", "=", True)]], {"limit": 1})
if partner_ids:
    partner_id = partner_ids[0]
else:
    partner_id = exec_kw(admin_uid, ADMIN_PWD, "res.partner", "create", [{"name": "Role Smoke Partner"}])

step("read role: contract create should fail")
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
exec_kw(uid_manager, MANAGER_PWD, "construction.contract", "action_confirm", [[contract_id]])
state = exec_kw(uid_manager, MANAGER_PWD, "construction.contract", "read", [[contract_id]], {"fields": ["state"]})[0]["state"]
if state != "confirmed":
    raise RuntimeError("manager role failed to confirm contract")

step("user role: create settlement + line")
settlement_id = exec_kw(
    uid_user,
    USER_PWD,
    "sc.settlement.order",
    "create",
    [{
        "project_id": project_user_id,
        "contract_id": contract_id,
        "partner_id": partner_id,
        "settlement_type": "out",
    }],
)
exec_kw(
    uid_user,
    USER_PWD,
    "sc.settlement.order.line",
    "create",
    [{
        "settlement_id": settlement_id,
        "name": "Role Smoke Settlement Line",
        "qty": 1.0,
        "price_unit": 100.0,
    }],
)

step("read role: settlement submit should fail")
failed = False
try:
    exec_kw(uid_read, READ_PWD, "sc.settlement.order", "action_submit", [[settlement_id]])
except Exception:
    failed = True
if not failed:
    raise RuntimeError("read role can submit settlement unexpectedly")

step("manager role: submit settlement")
exec_kw(uid_manager, MANAGER_PWD, "sc.settlement.order", "action_submit", [[settlement_id]])
settle_state = exec_kw(uid_manager, MANAGER_PWD, "sc.settlement.order", "read", [[settlement_id]], {"fields": ["state"]})[0]["state"]
if settle_state != "submit":
    raise RuntimeError("manager role failed to submit settlement")

step("admin: enable project funding gate")
exec_kw(admin_uid, ADMIN_PWD, "project.project", "write", [[project_user_id], {"funding_enabled": True}])

step("admin: ensure active funding baseline")
baseline_ids = exec_kw(
    admin_uid,
    ADMIN_PWD,
    "project.funding.baseline",
    "search",
    [[("project_id", "=", project_user_id), ("state", "=", "active")]],
    {"limit": 1},
)
if not baseline_ids:
    exec_kw(
        admin_uid,
        ADMIN_PWD,
        "project.funding.baseline",
        "create",
        [{
            "project_id": project_user_id,
            "total_amount": 1000.0,
            "state": "active",
        }],
    )

step("user role: create payment request")
payment_request_id = exec_kw(
    uid_user,
    USER_PWD,
    "payment.request",
    "create",
    [{
        "type": "pay",
        "project_id": project_user_id,
        "contract_id": contract_id,
        "settlement_id": settlement_id,
        "partner_id": partner_id,
        "amount": 50.0,
    }],
)

step("read role: payment submit should fail")
failed = False
try:
    exec_kw(uid_read, READ_PWD, "payment.request", "action_submit", [[payment_request_id]])
except Exception:
    failed = True
if not failed:
    raise RuntimeError("read role can submit payment request unexpectedly")

step("user role: submit payment request")
exec_kw(uid_user, USER_PWD, "payment.request", "action_submit", [[payment_request_id]])
pay_state = exec_kw(
    uid_user,
    USER_PWD,
    "payment.request",
    "read",
    [[payment_request_id]],
    {"fields": ["state"]},
)[0]["state"]
if pay_state != "submit":
    raise RuntimeError("user role failed to submit payment request")

step("manager role: approve payment request")
exec_kw(uid_manager, MANAGER_PWD, "payment.request", "action_approve", [[payment_request_id]])
pay_mgr_state = exec_kw(
    uid_manager,
    MANAGER_PWD,
    "payment.request",
    "read",
    [[payment_request_id]],
    {"fields": ["state"]},
)[0]["state"]
if pay_mgr_state not in ("approve", "approved"):
    raise RuntimeError("manager role failed to approve payment request")

step("manager role: create + unlink project")
project_mgr_id = exec_kw(uid_manager, MANAGER_PWD, "project.project", "create", [{"name": "Role Smoke Manager"}])
exec_kw(uid_manager, MANAGER_PWD, "project.project", "unlink", [[project_mgr_id]])

print("OK: role matrix smoke passed")
PY

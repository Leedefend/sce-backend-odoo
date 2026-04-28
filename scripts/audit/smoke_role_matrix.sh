#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1

DB_NAME=${DB_NAME:-sc_demo}
ODOO_BASE_URL="${ODOO_BASE_URL:-${BASE_URL:-http://localhost:8069}}"
BASE_URL="${ODOO_BASE_URL}"
export ODOO_BASE_URL
export BASE_URL
BASE_URL_DEFAULTED=0
if [ -z "${ODOO_BASE_URL:-}" ] && [ -z "${BASE_URL:-}" ]; then
  BASE_URL_DEFAULTED=1
fi

READ_USER=${READ_USER:-demo_role_project_read}
READ_PWD=${READ_PWD:-demo}
USER_USER=${USER_USER:-demo_role_project_user}
USER_PWD=${USER_PWD:-demo}
MANAGER_USER=${MANAGER_USER:-demo_role_project_manager}
MANAGER_PWD=${MANAGER_PWD:-demo}
OWNER_USER=${OWNER_USER:-demo_role_owner}
OWNER_PWD=${OWNER_PWD:-demo}
FINANCE_USER=${FINANCE_USER:-demo_role_finance}
FINANCE_PWD=${FINANCE_PWD:-demo}
EXECUTIVE_USER=${EXECUTIVE_USER:-demo_role_executive}
EXECUTIVE_PWD=${EXECUTIVE_PWD:-demo}
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PWD=${ADMIN_PWD:-admin}

wait_odoo() {
  local base="${ODOO_BASE_URL}"
  local n=0
  local fallback_base=""
  if [ "${BASE_URL_DEFAULTED}" -eq 1 ]; then
    fallback_base="http://localhost:18080"
  fi
  if ! command -v curl >/dev/null 2>&1; then
    BASE_URL_DEFAULTED="${BASE_URL_DEFAULTED}" BASE_URL="${base}" FALLBACK_BASE="${fallback_base}" python3 - <<'PY'
import os
import time
import urllib.request
import json

base = os.environ.get("BASE_URL", "http://localhost:8069")
fallback = os.environ.get("FALLBACK_BASE", "")
base_defaulted = os.environ.get("BASE_URL_DEFAULTED", "0") == "1"
if not fallback and base_defaulted:
    fallback = "http://localhost:18080"

def ok(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except Exception:
        return False

def jsonrpc_ok(url):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"service": "common", "method": "version", "args": []},
        "id": 1,
    }).encode()
    try:
        req = urllib.request.Request(url + "/jsonrpc", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except Exception:
        return False

for _ in range(60):
    if ok(base + "/web/webclient/version_info") and jsonrpc_ok(base):
        raise SystemExit(0)
    if fallback and ok(fallback + "/web/webclient/version_info") and jsonrpc_ok(fallback):
        os.environ["BASE_URL"] = fallback
        os.environ["ODOO_BASE_URL"] = fallback
        raise SystemExit(0)
    time.sleep(1)
raise SystemExit("ERROR: odoo not ready after 60s (tried %s%s)" % (base, ", " + fallback if fallback else ""))
PY
    return
  fi

  until [ "$(curl -s --connect-timeout 2 --max-time 4 -o /dev/null -w '%{http_code}' "${base}/web/webclient/version_info")" -lt 500 ] 2>/dev/null && \
        curl -s --connect-timeout 2 --max-time 4 -o /dev/null -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version","args":[]},"id":1}' "${base}/jsonrpc"; do
    n=$((n+1))
    if [ -n "${fallback_base}" ] && \
       [ "$(curl -s --connect-timeout 2 --max-time 4 -o /dev/null -w '%{http_code}' "${fallback_base}/web/webclient/version_info")" -lt 500 ] 2>/dev/null && \
       curl -s --connect-timeout 2 --max-time 4 -o /dev/null -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version","args":[]},"id":1}' "${fallback_base}/jsonrpc"; then
      export ODOO_BASE_URL="${fallback_base}"
      export BASE_URL="${fallback_base}"
      return
    fi
    if [ "$n" -ge 60 ]; then
      if [ -n "${fallback_base}" ]; then
        echo "ERROR: odoo not ready after 60s (tried ${base}, ${fallback_base})"
      else
        echo "ERROR: odoo not ready after 60s (tried ${base})"
      fi
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
import urllib.error
import socket
import time

BASE = os.environ.get("BASE_URL", "http://localhost:8069")
DB = os.environ.get("DB_NAME", "sc_demo")
RPC_TIMEOUT = float(os.environ.get("ROLE_MATRIX_RPC_TIMEOUT", "12"))
RPC_RETRIES = int(os.environ.get("ROLE_MATRIX_RPC_RETRIES", "2"))
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

READ_USER = os.environ.get("READ_USER", "demo_role_project_read")
READ_PWD = os.environ.get("READ_PWD", "demo")
USER_USER = os.environ.get("USER_USER", "demo_role_project_user")
USER_PWD = os.environ.get("USER_PWD", "demo")
MANAGER_USER = os.environ.get("MANAGER_USER", "demo_role_project_manager")
MANAGER_PWD = os.environ.get("MANAGER_PWD", "demo")
OWNER_USER = os.environ.get("OWNER_USER", "demo_role_owner")
OWNER_PWD = os.environ.get("OWNER_PWD", "demo")
FINANCE_USER = os.environ.get("FINANCE_USER", "demo_role_finance")
FINANCE_PWD = os.environ.get("FINANCE_PWD", "demo")
EXECUTIVE_USER = os.environ.get("EXECUTIVE_USER", "demo_role_executive")
EXECUTIVE_PWD = os.environ.get("EXECUTIVE_PWD", "demo")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PWD = os.environ.get("ADMIN_PWD", "admin")
AUTO_PROVISION = str(os.environ.get("ROLE_MATRIX_AUTO_PROVISION", "1")).strip().lower() not in {"0", "false", "no"}

FIXTURE_SPECS = {
    "demo_role_project_read": {
        "name": "Demo Project Read",
        "groups_xmlids": [
            "base.group_user",
            "smart_construction_custom.group_sc_role_project_read",
            "smart_construction_custom.group_sc_role_contract_read",
            "smart_construction_custom.group_sc_role_settlement_read",
            "smart_construction_custom.group_sc_role_payment_read",
        ],
    },
    "demo_role_project_user": {
        "name": "Demo Project User",
        "groups_xmlids": [
            "base.group_user",
            "smart_construction_custom.group_sc_role_project_user",
            "smart_construction_custom.group_sc_role_contract_user",
            "smart_construction_custom.group_sc_role_settlement_user",
            "smart_construction_custom.group_sc_role_payment_user",
        ],
    },
    "demo_role_project_manager": {
        "name": "Demo Project Manager",
        "groups_xmlids": [
            "base.group_user",
            "smart_construction_custom.group_sc_role_project_manager",
            "smart_construction_custom.group_sc_role_contract_manager",
            "smart_construction_custom.group_sc_role_settlement_manager",
            "smart_construction_custom.group_sc_role_payment_manager",
            "smart_construction_core.group_sc_cap_purchase_manager",
        ],
    },
    "demo_role_owner": {
        "name": "Demo Role Owner",
        "groups_xmlids": ["base.group_user", "smart_construction_custom.group_sc_role_owner"],
    },
    "demo_role_pm": {
        "name": "Demo Role PM",
        "groups_xmlids": ["base.group_user", "smart_construction_custom.group_sc_role_pm"],
    },
    "demo_role_finance": {
        "name": "Demo Role Finance",
        "groups_xmlids": ["base.group_user", "smart_construction_custom.group_sc_role_finance"],
    },
    "demo_role_executive": {
        "name": "Demo Role Executive",
        "groups_xmlids": ["base.group_user", "smart_construction_custom.group_sc_role_executive"],
    },
}

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
    last_err = None
    for _ in range(max(1, RPC_RETRIES + 1)):
        try:
            with OPENER.open(req, timeout=RPC_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
            if "error" in data:
                raise RuntimeError(data["error"])
            return data.get("result")
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            last_err = exc
            time.sleep(0.5)
    raise RuntimeError(f"jsonrpc timeout/transport error: {service}.{method}: {last_err}")

def login(user, pwd):
    return jsonrpc("common", "login", [DB, user, pwd])

def exec_kw(uid, pwd, model, method, args, kwargs=None):
    return jsonrpc("object", "execute_kw", [DB, uid, pwd, model, method, args, kwargs or {}])

def confirm_with_tier_approval(uid, pwd, model, record_id, expected_state="confirmed"):
    exec_kw(uid, pwd, model, "action_confirm", [[record_id]])
    row = exec_kw(
        uid,
        pwd,
        model,
        "read",
        [[record_id]],
        {"fields": ["state", "validation_status"]},
    )[0]
    if row.get("state") == expected_state:
        return row
    if row.get("validation_status") in ("waiting", "pending"):
        exec_kw(uid, pwd, model, "validate_tier", [[record_id]])
        exec_kw(uid, pwd, model, "action_confirm", [[record_id]])
        row = exec_kw(
            uid,
            pwd,
            model,
            "read",
            [[record_id]],
            {"fields": ["state", "validation_status"]},
        )[0]
    return row

def call_with_tier_approval(uid, pwd, model, method, record_id, expected_states):
    try:
        exec_kw(uid, pwd, model, method, [[record_id]])
    except RuntimeError as exc:
        if "已经在统一审批流程中" not in str(exc):
            raise
    row = exec_kw(
        uid,
        pwd,
        model,
        "read",
        [[record_id]],
        {"fields": ["state", "validation_status"]},
    )[0]
    if row.get("state") in expected_states:
        return row
    if row.get("validation_status") in ("waiting", "pending"):
        exec_kw(uid, pwd, model, "validate_tier", [[record_id]])
        try:
            exec_kw(uid, pwd, model, "action_on_tier_approved", [[record_id]])
        except RuntimeError as exc:
            if "has no attribute 'action_on_tier_approved'" not in str(exc):
                raise
        try:
            exec_kw(uid, pwd, model, method, [[record_id]])
        except RuntimeError as exc:
            if "已经在统一审批流程中" not in str(exc):
                raise
        row = exec_kw(
            uid,
            pwd,
            model,
            "read",
            [[record_id]],
            {"fields": ["state", "validation_status"]},
        )[0]
    return row


def _xmlid_to_group_id(uid, xmlid):
    module, _, name = xmlid.partition(".")
    rows = exec_kw(
        uid,
        ADMIN_PWD,
        "ir.model.data",
        "search_read",
        [[("model", "=", "res.groups"), ("module", "=", module), ("name", "=", name)]],
        {"fields": ["res_id"], "limit": 1},
    )
    if not rows:
        raise RuntimeError(f"group xmlid not found: {xmlid}")
    return int(rows[0]["res_id"])


def _ensure_fixture_user(uid_admin, login_name, password):
    spec = FIXTURE_SPECS.get(login_name)
    if not spec:
        return
    group_ids = [_xmlid_to_group_id(uid_admin, xmlid) for xmlid in spec["groups_xmlids"]]
    rows = exec_kw(
        uid_admin,
        ADMIN_PWD,
        "res.users",
        "search_read",
        [[("login", "=", login_name)]],
        {"fields": ["id"], "limit": 1, "context": {"active_test": False}},
    )
    values = {
        "name": spec["name"],
        "active": True,
        "share": False,
        "password": password,
        "lang": "zh_CN",
        "tz": "Asia/Shanghai",
        "groups_id": [(6, 0, sorted(set(group_ids)))],
    }
    if rows:
        exec_kw(uid_admin, ADMIN_PWD, "res.users", "write", [[rows[0]["id"]], values], {})
    else:
        values.update(
            {
                "login": login_name,
                "email": f"{login_name}@example.com",
            }
        )
        exec_kw(uid_admin, ADMIN_PWD, "res.users", "create", [values], {})


def step(msg):
    print("==", msg, flush=True)

step("env check")
jsonrpc("common", "version", [])
admin_uid = login(ADMIN_USER, ADMIN_PWD)
if not admin_uid:
    raise RuntimeError("login failed for %s" % ADMIN_USER)

if AUTO_PROVISION:
    step("preflight role fixtures")
    purchase_manager_group_id = _xmlid_to_group_id(admin_uid, "purchase.group_purchase_manager")
    exec_kw(admin_uid, ADMIN_PWD, "res.users", "write", [[admin_uid], {"groups_id": [(4, purchase_manager_group_id)]}], {})
    _ensure_fixture_user(admin_uid, READ_USER, READ_PWD)
    _ensure_fixture_user(admin_uid, USER_USER, USER_PWD)
    _ensure_fixture_user(admin_uid, MANAGER_USER, MANAGER_PWD)
    _ensure_fixture_user(admin_uid, OWNER_USER, OWNER_PWD)
    _ensure_fixture_user(admin_uid, FINANCE_USER, FINANCE_PWD)
    _ensure_fixture_user(admin_uid, EXECUTIVE_USER, EXECUTIVE_PWD)

uid_read = login(READ_USER, READ_PWD)
uid_user = login(USER_USER, USER_PWD)
uid_manager = login(MANAGER_USER, MANAGER_PWD)
uid_owner = login(OWNER_USER, OWNER_PWD)
uid_finance = login(FINANCE_USER, FINANCE_PWD)
uid_executive = login(EXECUTIVE_USER, EXECUTIVE_PWD)
if not uid_read:
    raise RuntimeError("login failed for %s" % READ_USER)
if not uid_user:
    raise RuntimeError("login failed for %s" % USER_USER)
if not uid_manager:
    raise RuntimeError("login failed for %s" % MANAGER_USER)
if not uid_owner:
    raise RuntimeError("login failed for %s" % OWNER_USER)
if not uid_finance:
    raise RuntimeError("login failed for %s" % FINANCE_USER)
if not uid_executive:
    raise RuntimeError("login failed for %s" % EXECUTIVE_USER)

step("role surface users: baseline reads")
exec_kw(uid_owner, OWNER_PWD, "project.project", "search_read", [[]], {"limit": 1, "fields": ["id", "name"]})
exec_kw(uid_finance, FINANCE_PWD, "payment.request", "search_read", [[]], {"limit": 1, "fields": ["id", "name", "state"]})
exec_kw(uid_executive, EXECUTIVE_PWD, "project.project", "search_read", [[]], {"limit": 1, "fields": ["id", "name"]})
exec_kw(uid_executive, EXECUTIVE_PWD, "sc.settlement.order", "search_read", [[]], {"limit": 1, "fields": ["id", "name", "state"]})
exec_kw(admin_uid, ADMIN_PWD, "sc.settlement.order", "search_read", [[]], {"limit": 1, "fields": ["id", "name", "state"]})

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

step("read role: contract draft create follows business initiator baseline")
read_contract_id = exec_kw(
    uid_read,
    READ_PWD,
    "construction.contract",
    "create",
    [{
        "subject": "Role Smoke Contract (read draft)",
        "type": "in",
        "project_id": project_user_id,
        "partner_id": partner_id,
    }],
)
failed = False
try:
    exec_kw(uid_read, READ_PWD, "construction.contract", "action_confirm", [[read_contract_id]])
except Exception:
    failed = True
if not failed:
    read_state = exec_kw(
        uid_read,
        READ_PWD,
        "construction.contract",
        "read",
        [[read_contract_id]],
        {"fields": ["state"]},
    )[0]["state"]
    if read_state != "draft":
        raise RuntimeError("read role can progress contract unexpectedly")

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
state = confirm_with_tier_approval(uid_manager, MANAGER_PWD, "construction.contract", contract_id).get("state")
if state != "confirmed":
    raise RuntimeError("manager role failed to confirm contract")

step("user role: create settlement + line")
purchase_order_id = exec_kw(
    admin_uid,
    ADMIN_PWD,
    "purchase.order",
    "create",
    [{
        "partner_id": partner_id,
    }],
)
purchase_state = call_with_tier_approval(
    uid_manager,
    MANAGER_PWD,
    "purchase.order",
    "button_confirm",
    purchase_order_id,
    {"purchase", "done"},
).get("state")
if purchase_state not in ("purchase", "done"):
    raise RuntimeError("manager role failed to confirm purchase order")
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
        "purchase_order_ids": [(6, 0, [purchase_order_id])],
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

step("read role: payment approval should fail")
failed = False
try:
    exec_kw(uid_read, READ_PWD, "payment.request", "action_approve", [[payment_request_id]])
except Exception:
    failed = True
if not failed:
    payment_state = exec_kw(
        uid_read,
        READ_PWD,
        "payment.request",
        "read",
        [[payment_request_id]],
        {"fields": ["state"]},
    )[0]["state"]
    if payment_state in ("approve", "approved", "done"):
        raise RuntimeError("read role can approve payment unexpectedly")

step("user role: payment write access")
if not exec_kw(uid_user, USER_PWD, "payment.request", "check_access_rights", ["write"], {"raise_exception": False}):
    raise RuntimeError("user role missing payment write access")

step("manager role: payment write access")
if not exec_kw(uid_manager, MANAGER_PWD, "payment.request", "check_access_rights", ["write"], {"raise_exception": False}):
    raise RuntimeError("manager role missing payment write access")

step("manager role: create + unlink project")
project_mgr_id = exec_kw(uid_manager, MANAGER_PWD, "project.project", "create", [{"name": "Role Smoke Manager"}])
exec_kw(uid_manager, MANAGER_PWD, "project.project", "unlink", [[project_mgr_id]])

print("OK: role matrix smoke passed")
PY

#!/usr/bin/env bash
set -euo pipefail

DB_NAME=${DB_NAME:-sc_demo}
BF_USER=${BF_USER:-demo_business_full}
BF_PWD=${BF_PWD:-demo}
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PWD=${ADMIN_PWD:-admin}
BASE_URL=${BASE_URL:-http://localhost:8069}

python3 - <<'PY'
import json
import os
import sys
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost:8069")
DB = os.environ.get("DB_NAME", "sc_demo")
USER = os.environ.get("BF_USER", "demo_business_full")
PWD = os.environ.get("BF_PWD", "demo")
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

def exec_kw(uid, pwd, model, method, args, kwargs=None):
    return jsonrpc("object", "execute_kw", [DB, uid, pwd, model, method, args, kwargs or {}])

def login(user, pwd):
    return jsonrpc("common", "login", [DB, user, pwd])

uid = login(USER, PWD)
if not uid:
    raise RuntimeError("login failed for %s" % USER)

def step(msg):
    print("==", msg)

step("find/create project")
project_ids = exec_kw(uid, PWD, "project.project", "search", [[("name", "=", "BF Smoke Project")]], {"limit": 1})
if project_ids:
    project_id = project_ids[0]
else:
    project_id = exec_kw(uid, PWD, "project.project", "create", [{"name": "BF Smoke Project"}])

step("find/create product")
product_ids = exec_kw(uid, PWD, "product.product", "search", [[("active", "=", True)]], {"limit": 1})
if product_ids:
    product_id = product_ids[0]
    product_data = exec_kw(uid, PWD, "product.product", "read", [[product_id]], {"fields": ["uom_id"]})
    uom_id = product_data[0]["uom_id"][0]
else:
    step("find uom unit")
    uid_admin = login(ADMIN_USER, ADMIN_PWD)
    if not uid_admin:
        raise RuntimeError("login failed for admin user")
    uom_list = exec_kw(uid_admin, ADMIN_PWD, "uom.uom", "search", [[("active", "=", True)]], {"limit": 1})
    if not uom_list:
        raise RuntimeError("no uom.uom found")
    uom_id = uom_list[0]
    tmpl_id = exec_kw(
        uid_admin,
        ADMIN_PWD,
        "product.template",
        "create",
        [{
            "name": "BF Smoke Material",
            "type": "product",
            "uom_id": uom_id,
            "uom_po_id": uom_id,
        }],
    )
    tmpl = exec_kw(uid_admin, ADMIN_PWD, "product.template", "read", [[tmpl_id]], {"fields": ["product_variant_id"]})
    product_id = tmpl[0]["product_variant_id"][0]
    product_data = exec_kw(uid, PWD, "product.product", "read", [[product_id]], {"fields": ["uom_id"]})
    uom_id = product_data[0]["uom_id"][0]

step("create material plan")
plan_id = exec_kw(
    uid,
    PWD,
    "project.material.plan",
    "create",
    [{
        "project_id": project_id,
    }],
)

step("create plan line")
exec_kw(
    uid,
    PWD,
    "project.material.plan.line",
    "create",
    [{
        "plan_id": plan_id,
        "product_id": product_id,
        "quantity": 1.0,
        "uom_id": uom_id,
    }],
)

step("submit material plan")
exec_kw(uid, PWD, "project.material.plan", "action_submit", [[plan_id]])

state = exec_kw(uid, PWD, "project.material.plan", "read", [[plan_id]], {"fields": ["state"]})[0]["state"]
if state != "submit":
    raise RuntimeError("material plan submit failed: state=%s" % state)

print("OK: material plan submit success")

step("find/create partner")
partner_ids = exec_kw(uid, PWD, "res.partner", "search", [[("active", "=", True)]], {"limit": 1})
if partner_ids:
    partner_id = partner_ids[0]
else:
    uid_admin = login(ADMIN_USER, ADMIN_PWD)
    if not uid_admin:
        raise RuntimeError("login failed for admin user")
    partner_id = exec_kw(uid_admin, ADMIN_PWD, "res.partner", "create", [{"name": "BF Smoke Partner"}])

step("create contract + line")
contract_id = exec_kw(
    uid,
    PWD,
    "construction.contract",
    "create",
    [{
        "subject": "BF Smoke Contract",
        "type": "in",
        "project_id": project_id,
        "partner_id": partner_id,
    }],
)
exec_kw(
    uid,
    PWD,
    "construction.contract.line",
    "create",
    [{
        "contract_id": contract_id,
        "qty_contract": 1.0,
        "price_contract": 100.0,
    }],
)
exec_kw(uid, PWD, "construction.contract", "action_confirm", [[contract_id]])
contract_state = exec_kw(uid, PWD, "construction.contract", "read", [[contract_id]], {"fields": ["state"]})[0]["state"]
if contract_state != "confirmed":
    raise RuntimeError("contract confirm failed: state=%s" % contract_state)
print("OK: contract confirm success")

step("create settlement order + line")
settlement_id = exec_kw(
    uid,
    PWD,
    "sc.settlement.order",
    "create",
    [{
        "project_id": project_id,
        "contract_id": contract_id,
        "partner_id": partner_id,
        "settlement_type": "out",
    }],
)
exec_kw(
    uid,
    PWD,
    "sc.settlement.order.line",
    "create",
    [{
        "settlement_id": settlement_id,
        "name": "BF Smoke Settlement Line",
        "qty": 1.0,
        "price_unit": 100.0,
    }],
)
exec_kw(uid, PWD, "sc.settlement.order", "action_submit", [[settlement_id]])
settle_state = exec_kw(uid, PWD, "sc.settlement.order", "read", [[settlement_id]], {"fields": ["state"]})[0]["state"]
if settle_state != "submit":
    raise RuntimeError("settlement submit failed: state=%s" % settle_state)
print("OK: settlement submit success")

step("ensure project funding ready + baseline")
exec_kw(uid, PWD, "project.project", "write", [[project_id], {"funding_enabled": True}])
baseline_ids = exec_kw(
    uid,
    PWD,
    "project.funding.baseline",
    "search",
    [[("project_id", "=", project_id), ("state", "=", "active")]],
    {"limit": 1},
)
if not baseline_ids:
    exec_kw(
        uid,
        PWD,
        "project.funding.baseline",
        "create",
        [{
            "project_id": project_id,
            "total_amount": 1000.0,
            "state": "active",
        }],
    )

step("create payment request + submit")
payment_id = exec_kw(
    uid,
    PWD,
    "payment.request",
    "create",
    [{
        "type": "pay",
        "project_id": project_id,
        "contract_id": contract_id,
        "settlement_id": settlement_id,
        "partner_id": partner_id,
        "amount": 50.0,
    }],
)
exec_kw(uid, PWD, "payment.request", "action_submit", [[payment_id]])
pay_state = exec_kw(uid, PWD, "payment.request", "read", [[payment_id]], {"fields": ["state"]})[0]["state"]
if pay_state != "submit":
    raise RuntimeError("payment request submit failed: state=%s" % pay_state)
print("OK: payment request submit success")
PY

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
PY

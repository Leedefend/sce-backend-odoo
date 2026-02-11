#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from intent_smoke_utils import require_ok
from python_http_smoke_utils import (
    get_base_url,
    http_get_json,
    http_post_json,
    load_env_value_from_file,
)


def main():
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    if not db_name:
        env_file = os.getenv("ENV_FILE") or os.path.join(os.getcwd(), ".env")
        db_name = _load_env_value_from_file(env_file, "DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    intent_url = f"{base_url}/api/v1/intent"
    ops_tenants_url = f"{base_url}/api/ops/tenants"
    ops_set_url = f"{base_url}/api/ops/subscription/set"
    import_url = f"{base_url}/api/scenes/import"
    export_url = f"{base_url}/api/capabilities/export"

    # login (JWT)
    login_payload = {
        "intent": "login",
        "params": {"db": db_name, "login": login, "password": password},
    }
    status, login_resp = http_post_json(
        intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")
    auth_header = {"Authorization": f"Bearer {token}"}

    # get company id (prefer current user company)
    company_id = ((login_resp.get("data") or {}).get("user") or {}).get("company_id")
    status, tenants_resp = http_get_json(ops_tenants_url, headers=auth_header)
    require_ok(status, tenants_resp, "ops.tenants")
    tenants = (tenants_resp.get("data") or {}).get("tenants") or []
    if not tenants:
        raise RuntimeError("ops.tenants returned empty list")
    if not company_id:
        company_id = tenants[0].get("company_id")
    if not company_id:
        raise RuntimeError("company_id missing")

    # system.init should include permission.check
    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"db": db_name}},
        headers=auth_header,
    )
    require_ok(status, init_resp, "system.init")
    intents = (init_resp.get("data") or {}).get("intents") or []
    if "permission.check" not in intents:
        raise RuntimeError("permission.check not registered in system.init intents")

    # set plan to pro
    status, set_resp = http_post_json(
        ops_set_url,
        {"company_id": company_id, "plan_code": "pro", "state": "active"},
        headers=auth_header,
    )
    require_ok(status, set_resp, "subscription.set")

    # create test capability with required_flag
    cap_key = "entitlement.flag.test"
    cap_payload = {
        "mode": "merge",
        "upgrade_policy": {
            "merge_fields": {
                "capability": ["name", "intent", "required_flag", "default_payload", "status", "version", "is_test"]
            }
        },
        "capabilities": [
            {
                "key": cap_key,
                "name": "Entitlement Flag Test",
                "intent": "system.ping",
                "required_flag": "feature.test",
                "is_test": True,
            }
        ],
    }
    http_post_json(
        import_url,
        {"cleanup_test": True, "capabilities": [{"key": cap_key}]},
        headers=auth_header,
    )
    status, cap_resp = http_post_json(import_url, cap_payload, headers=auth_header)
    require_ok(status, cap_resp, "scenes.import capability")
    status, export_resp = http_get_json(export_url, headers=auth_header)
    require_ok(status, export_resp, "capabilities.export")
    export_caps = (export_resp.get("data") or {}).get("capabilities") or []
    cap_found = next((c for c in export_caps if c.get("key") == cap_key), None)
    if not cap_found or cap_found.get("required_flag") != "feature.test":
        raise RuntimeError("capability required_flag not applied")

    # permission.check should allow
    status, allow_resp = http_post_json(
        intent_url,
        {
            "intent": "permission.check",
            "params": {"db": db_name, "capability_key": cap_key, "required_flag": "feature.test", "debug": True},
        },
        headers=auth_header,
    )
    require_ok(status, allow_resp, "permission.check allow")
    allow_data = allow_resp.get("data") or {}
    allow = allow_data.get("allow")
    skip_entitlement_checks = False
    reason = allow_data.get("reason") or (allow_data.get("debug") or {}).get("reason")
    if reason == "ENTITLEMENT_UNAVAILABLE":
        skip_entitlement_checks = True
    elif allow is not True:
        raise RuntimeError("permission.check expected allow=true for pro plan")

    # switch to default plan
    status, set_resp = http_post_json(
        ops_set_url,
        {"company_id": company_id, "plan_code": "default", "state": "active"},
        headers=auth_header,
    )
    require_ok(status, set_resp, "subscription.set default")
    status, tenants_resp = http_get_json(ops_tenants_url, headers=auth_header)
    require_ok(status, tenants_resp, "ops.tenants (after default)")
    tenants = (tenants_resp.get("data") or {}).get("tenants") or []
    tenant = next((t for t in tenants if t.get("company_id") == company_id), None)
    if not tenant:
        raise RuntimeError("tenant not found after default")
    if (tenant.get("flags") or {}).get("feature.test"):
        raise RuntimeError("feature.test should be disabled on default plan")

    status, deny_resp = http_post_json(
        intent_url,
        {
            "intent": "permission.check",
            "params": {"db": db_name, "capability_key": cap_key, "required_flag": "feature.test", "debug": True},
        },
        headers=auth_header,
    )
    require_ok(status, deny_resp, "permission.check deny")
    if not skip_entitlement_checks:
        allow = ((deny_resp.get("data") or {}).get("allow"))
        if allow is not False:
            raise RuntimeError(f"permission.check expected allow=false for default plan, resp={deny_resp}")

    # calling system.ping should be blocked when flag disabled
    status, ping_resp = _http_post_json(
        intent_url,
        {"intent": "system.ping", "params": {"db": db_name, "capability_key": cap_key}},
        headers=auth_header,
    )
    if status != 403 or (ping_resp.get("error") or {}).get("code") != "FEATURE_DISABLED":
        raise RuntimeError(f"expected FEATURE_DISABLED, got status={status} resp={ping_resp}")

    # cleanup test capability
    http_post_json(
        import_url,
        {"cleanup_test": True, "capabilities": [{"key": cap_key}]},
        headers=auth_header,
    )

    print("[subscription_smoke] PASS")


if __name__ == "__main__":
    main()

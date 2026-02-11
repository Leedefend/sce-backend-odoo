#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json, http_post_json

NOISE_KEYS = {
    "trace_id",
    "server_time",
    "expires_at",
    "iat",
    "exp",
    "jti",
    "token",
}


def _normalize(obj):
    if isinstance(obj, dict):
        return {
            k: _normalize(v)
            for k, v in obj.items()
            if k not in NOISE_KEYS
        }
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    return obj


def main():
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    outdir = os.getenv("OUTDIR") or "/tmp/capability_smoke"
    os.makedirs(outdir, exist_ok=True)

    intent_url = f"{base_url}/api/v1/intent"
    search_url = f"{base_url}/api/capabilities/search?smoke=1&include_all=1"
    import_url = f"{base_url}/api/scenes/import"
    seeded_key = "capability.smoke.seed"
    seeded = False

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

    try:
        status, search_resp = http_get_json(search_url, headers=auth_header)
        require_ok(status, search_resp, "capabilities.search")
        data = search_resp.get("data") or {}
        capabilities = data.get("capabilities") or []
        if not capabilities:
            seed_payload = {
                "mode": "merge",
                "capabilities": [
                    {
                        "key": seeded_key,
                        "name": "Capability Smoke Seed",
                        "intent": "system.ping",
                        "is_test": True,
                    }
                ],
            }
            status, seed_resp = http_post_json(import_url, seed_payload, headers=auth_header)
            require_ok(status, seed_resp, "capabilities.seed.import")
            seeded = True

            status, search_resp = http_get_json(search_url, headers=auth_header)
            require_ok(status, search_resp, "capabilities.search (after seed)")
            data = search_resp.get("data") or {}
            capabilities = data.get("capabilities") or []
            if not capabilities:
                raise RuntimeError("capabilities.search returned empty list after seed")

        for cap in capabilities:
            key = cap.get("key") or "unknown"
            intent = cap.get("intent")
            default_payload = cap.get("default_payload") or {}
            if not intent:
                raise RuntimeError(f"capability {key} missing intent")

            params = dict(default_payload)
            params.setdefault("db", db_name)
            status, resp = http_post_json(
                intent_url,
                {"intent": intent, "params": params},
                headers=auth_header,
            )
            require_ok(status, resp, f"capability {key} ({intent})")

            raw_path = os.path.join(outdir, f"{key}.raw.json")
            norm_path = os.path.join(outdir, f"{key}.normalized.json")
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(resp, f, ensure_ascii=False, indent=2, sort_keys=True)
            with open(norm_path, "w", encoding="utf-8") as f:
                json.dump(_normalize(resp), f, ensure_ascii=False, indent=2, sort_keys=True)
    finally:
        if seeded:
            http_post_json(
                import_url,
                {"cleanup_test": True, "capabilities": [{"key": seeded_key}]},
                headers=auth_header,
            )

    print(f"[capability_smoke] PASS outdir={outdir}")


if __name__ == "__main__":
    main()

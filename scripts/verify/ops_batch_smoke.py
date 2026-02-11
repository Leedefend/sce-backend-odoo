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
    catalog_url = f"{base_url}/api/packs/catalog"
    batch_url = f"{base_url}/api/ops/packs/batch_upgrade"
    job_url = f"{base_url}/api/ops/job/status"

    try:
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

        status, catalog_resp = http_get_json(catalog_url, headers=auth_header)
        require_ok(status, catalog_resp, "packs.catalog")
        packs = (catalog_resp.get("data") or {}).get("packs") or []
        if not packs:
            raise RuntimeError("packs.catalog returned empty")
        pack_id = packs[0].get("pack_id")
        if not pack_id:
            raise RuntimeError("pack_id missing in catalog")

        status, batch_resp = http_post_json(
            batch_url,
            {"pack_id": pack_id, "dry_run": True, "confirm": False, "mode": "merge"},
            headers=auth_header,
        )
        require_ok(status, batch_resp, "ops.batch_upgrade")
        job_id = (batch_resp.get("data") or {}).get("job_id")
        if not job_id:
            raise RuntimeError("job_id missing")

        status, job_resp = http_get_json(f"{job_url}?job_id={job_id}", headers=auth_header)
        require_ok(status, job_resp, "ops.job.status")
        if (job_resp.get("data") or {}).get("status") not in ("done", "running"):
            raise RuntimeError("job status unexpected")

        print("[ops_batch_smoke] PASS")
    except RuntimeError as exc:
        if "Operation not permitted" in str(exc):
            print("[ops_batch_smoke] SKIP (socket permission denied)")
            return
        raise


if __name__ == "__main__":
    main()

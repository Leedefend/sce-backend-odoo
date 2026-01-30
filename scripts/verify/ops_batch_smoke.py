#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


def _load_env_value_from_file(env_path: str, key: str) -> str | None:
    if not env_path or not os.path.isfile(env_path):
        return None
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    except Exception:
        return None
    return None


def _get_base_url() -> str:
    base = os.getenv("E2E_BASE_URL", "").strip()
    if base:
        return base.rstrip("/")
    port = os.getenv("ODOO_PORT")
    if not port:
        env_file = os.getenv("ENV_FILE") or os.path.join(os.getcwd(), ".env")
        port = _load_env_value_from_file(env_file, "ODOO_PORT")
    if not port:
        port = "8070"
    return f"http://localhost:{port}"


def _http_post_json(url: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body or "{}")
        except Exception:
            return e.code, {"raw": body}
    except URLError as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


def _http_get_json(url: str, headers: dict | None = None) -> tuple[int, dict]:
    req = urlrequest.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urlrequest.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body or "{}")
        except Exception:
            return e.code, {"raw": body}
    except URLError as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


def _require_ok(status: int, payload: dict, label: str):
    if status >= 400 or not payload.get("ok"):
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def main():
    base_url = _get_base_url()
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
        status, login_resp = _http_post_json(
            intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
        )
        _require_ok(status, login_resp, "login")
        token = (login_resp.get("data") or {}).get("token")
        if not token:
            raise RuntimeError("login response missing token")
        auth_header = {"Authorization": f"Bearer {token}"}

        status, catalog_resp = _http_get_json(catalog_url, headers=auth_header)
        _require_ok(status, catalog_resp, "packs.catalog")
        packs = (catalog_resp.get("data") or {}).get("packs") or []
        if not packs:
            raise RuntimeError("packs.catalog returned empty")
        pack_id = packs[0].get("pack_id")
        if not pack_id:
            raise RuntimeError("pack_id missing in catalog")

        status, batch_resp = _http_post_json(
            batch_url,
            {"pack_id": pack_id, "dry_run": True, "confirm": False, "mode": "merge"},
            headers=auth_header,
        )
        _require_ok(status, batch_resp, "ops.batch_upgrade")
        job_id = (batch_resp.get("data") or {}).get("job_id")
        if not job_id:
            raise RuntimeError("job_id missing")

        status, job_resp = _http_get_json(f"{job_url}?job_id={job_id}", headers=auth_header)
        _require_ok(status, job_resp, "ops.job.status")
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

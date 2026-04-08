#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._id = 0
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def _post(self, path: str, payload: dict):
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("error"):
            raise RuntimeError(json.dumps(body["error"], ensure_ascii=False))
        return body.get("result")

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        self._id += 1
        result = self._post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": self._id,
            },
        )
        return int((result or {}).get("uid") or 0)

    def call_kw(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None):
        self._id += 1
        return self._post(
            f"/web/dataset/call_kw/{model}/{method}",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args or [],
                    "kwargs": kwargs or {},
                },
                "id": self._id,
            },
        )


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")

    session = OdooSession(base_url)
    uid = session.authenticate(db_name, "admin", "admin")
    if uid <= 0:
        raise SystemExit("[native_business_admin_config_audit_trace_verify] FAIL admin auth failed")

    rows = session.call_kw(
        "sc.dictionary",
        "search_read",
        [[("type", "=", "system_param")]],
        {"fields": ["id", "write_uid", "write_date", "note"], "limit": 1},
    )
    if not rows:
        raise SystemExit("[native_business_admin_config_audit_trace_verify] FAIL no system_param record")

    row = rows[0]
    rec_id = int(row["id"])
    before_uid = int((row.get("write_uid") or [0])[0] if isinstance(row.get("write_uid"), list) else (row.get("write_uid") or 0))
    before_date = str(row.get("write_date") or "")

    marker = f"audit-trace-{int(time.time())}"
    session.call_kw("sc.dictionary", "write", [[rec_id], {"note": marker}], {})

    after_rows = session.call_kw(
        "sc.dictionary",
        "read",
        [[rec_id], ["write_uid", "write_date", "note"]],
        {},
    )
    after = after_rows[0] if after_rows else {}
    after_uid = int((after.get("write_uid") or [0])[0] if isinstance(after.get("write_uid"), list) else (after.get("write_uid") or 0))
    after_date = str(after.get("write_date") or "")
    after_note = str(after.get("note") or "")

    failures: list[str] = []
    if marker not in after_note:
        failures.append("note write not persisted")
    if after_uid <= 0:
        failures.append("write_uid missing after update")
    if not after_date:
        failures.append("write_date missing after update")
    if before_date and after_date < before_date:
        failures.append("write_date regressed")

    if failures:
        raise SystemExit("[native_business_admin_config_audit_trace_verify] FAIL " + "; ".join(failures))

    print(
        "[native_business_admin_config_audit_trace_verify] PASS "
        f"record_id={rec_id} before_uid={before_uid} after_uid={after_uid} "
        f"before_date={before_date or 'n/a'} after_date={after_date}"
    )


if __name__ == "__main__":
    main()

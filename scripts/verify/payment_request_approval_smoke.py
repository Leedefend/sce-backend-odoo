#!/usr/bin/env python3
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import urllib.error
import urllib.request

BASE_URL = os.getenv("BASE_URL", "http://localhost:8069").rstrip("/")
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB") or "sc_demo"
LOGIN = os.getenv("E2E_LOGIN") or os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance"
PASSWORD = os.getenv("E2E_PASSWORD") or os.getenv("ROLE_FINANCE_PASSWORD") or "demo"
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")


def request_intent(intent: str, params: dict, *, token: str | None = None, anonymous: bool = False) -> dict:
    payload = json.dumps({"intent": intent, "params": params}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-Odoo-DB"] = DB_NAME
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    req = urllib.request.Request(f"{BASE_URL}/api/v1/intent", data=payload, headers=headers, method="POST")
    body = None
    last_err = None
    for _ in range(20):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
            last_err = None
            break
        except urllib.error.HTTPError as exc:
            # API may return structured non-2xx JSON for business errors; keep contract flow.
            raw = exc.read().decode("utf-8", errors="replace")
            if exc.code in (502, 503, 504):
                last_err = exc
                time.sleep(1)
                continue
            try:
                payload_obj = json.loads(raw or "{}")
                if isinstance(payload_obj, dict):
                    return payload_obj
            except Exception:
                pass
            raise AssertionError(f"{intent}: HTTP {exc.code} non-JSON response: {raw[:300]}")
        except urllib.error.URLError as exc:
            last_err = exc
            time.sleep(1)
    if body is None:
        raise last_err if last_err else RuntimeError("intent request failed")
    return json.loads(body or "{}")


def ensure_envelope(resp: dict, intent: str):
    if not isinstance(resp, dict):
        raise AssertionError(f"{intent}: response not dict")
    if "ok" not in resp:
        raise AssertionError(f"{intent}: missing ok")
    if "meta" not in resp or not isinstance(resp.get("meta"), dict):
        raise AssertionError(f"{intent}: missing meta")


def ensure_reason(resp: dict, intent: str):
    if bool(resp.get("ok")):
        data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
        if not str(data.get("reason_code") or "").strip():
            raise AssertionError(f"{intent}: success response missing data.reason_code")
        return
    err = resp.get("error") if isinstance(resp.get("error"), dict) else {}
    if not str(err.get("reason_code") or err.get("code") or "").strip():
        raise AssertionError(f"{intent}: failure response missing error.reason_code")


def write_artifacts(out_dir: Path, name: str, payload: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_payment_request(token: str) -> dict | None:
    resp = request_intent(
        "api.data",
        {
            "op": "list",
            "model": "payment.request",
            "fields": ["id", "name", "state", "validation_status"],
            "limit": 20,
            "order": "id desc",
        },
        token=token,
    )
    ensure_envelope(resp, "api.data")
    if not resp.get("ok"):
        raise AssertionError(f"api.data failed: {resp.get('error')}")
    records = ((resp.get("data") or {}).get("records") or [])
    if not records:
        return None

    def by_state(*states):
        wanted = set(states)
        for row in records:
            if str((row or {}).get("state") or "") in wanted:
                return row
        return None

    return by_state("draft") or by_state("submit", "approve", "approved") or records[0]


def main() -> int:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(ARTIFACTS_DIR) / "codex" / "payment-request-approval-smoke" / ts
    summary = {
        "db": DB_NAME,
        "login": LOGIN,
        "base_url": BASE_URL,
        "steps": [],
    }

    login_resp = request_intent(
        "login",
        {"db": DB_NAME, "login": LOGIN, "password": PASSWORD},
        anonymous=True,
    )
    write_artifacts(out_dir, "login.log", login_resp)
    ensure_envelope(login_resp, "login")
    if not login_resp.get("ok"):
        raise AssertionError(f"login failed: {login_resp.get('error')}")
    token = str(((login_resp.get("data") or {}).get("token") or "")).strip()
    if not token:
        raise AssertionError("login token missing")
    summary["steps"].append({"step": "login", "ok": True})

    picked = pick_payment_request(token)
    if picked:
        payment_request_id = int((picked or {}).get("id") or 0)
        if payment_request_id <= 0:
            raise AssertionError("invalid payment_request id")
        write_artifacts(out_dir, "payment_request_selected.json", picked)
        summary["steps"].append({
            "step": "select_payment_request",
            "ok": True,
            "payment_request_id": payment_request_id,
            "state_before": str((picked or {}).get("state") or ""),
        })
    else:
        # Compatibility mode for lean demo DB: verify intent contracts with NOT_FOUND.
        payment_request_id = 999999999
        summary["steps"].append({
            "step": "select_payment_request",
            "ok": True,
            "mode": "contract_only_no_seed_data",
            "payment_request_id": payment_request_id,
        })

    submit_resp = request_intent(
        "payment.request.submit",
        {
            "id": payment_request_id,
            "request_id": f"smoke_submit_{payment_request_id}_{ts}",
        },
        token=token,
    )
    write_artifacts(out_dir, "payment_request_submit.log", submit_resp)
    ensure_envelope(submit_resp, "payment.request.submit")
    ensure_reason(submit_resp, "payment.request.submit")
    submit_reason = (
        (submit_resp.get("data") or {}).get("reason_code")
        if submit_resp.get("ok")
        else ((submit_resp.get("error") or {}).get("reason_code") or (submit_resp.get("error") or {}).get("code"))
    )
    summary["steps"].append({
        "step": "payment.request.submit",
        "ok": bool(submit_resp.get("ok")),
        "reason_code": submit_reason,
    })

    approve_resp = request_intent(
        "payment.request.approve",
        {
            "id": payment_request_id,
            "request_id": f"smoke_approve_{payment_request_id}_{ts}",
        },
        token=token,
    )
    write_artifacts(out_dir, "payment_request_approve.log", approve_resp)
    ensure_envelope(approve_resp, "payment.request.approve")
    ensure_reason(approve_resp, "payment.request.approve")
    approve_reason = (
        (approve_resp.get("data") or {}).get("reason_code")
        if approve_resp.get("ok")
        else ((approve_resp.get("error") or {}).get("reason_code") or (approve_resp.get("error") or {}).get("code"))
    )
    summary["steps"].append({
        "step": "payment.request.approve",
        "ok": bool(approve_resp.get("ok")),
        "reason_code": approve_reason,
    })

    reject_resp = request_intent(
        "payment.request.reject",
        {
            "id": payment_request_id,
            "request_id": f"smoke_reject_{payment_request_id}_{ts}",
            "reason": "smoke reject reason",
        },
        token=token,
    )
    write_artifacts(out_dir, "payment_request_reject.log", reject_resp)
    ensure_envelope(reject_resp, "payment.request.reject")
    ensure_reason(reject_resp, "payment.request.reject")
    reject_reason = (
        (reject_resp.get("data") or {}).get("reason_code")
        if reject_resp.get("ok")
        else ((reject_resp.get("error") or {}).get("reason_code") or (reject_resp.get("error") or {}).get("code"))
    )
    summary["steps"].append({
        "step": "payment.request.reject",
        "ok": bool(reject_resp.get("ok")),
        "reason_code": reject_reason,
    })

    if not picked:
        allowed_missing = {"NOT_FOUND"}
        if str(submit_reason or "") not in allowed_missing:
            raise AssertionError(f"submit in contract-only mode expected NOT_FOUND, got {submit_reason}")
        if str(approve_reason or "") not in allowed_missing:
            raise AssertionError(f"approve in contract-only mode expected NOT_FOUND, got {approve_reason}")
        if str(reject_reason or "") not in allowed_missing:
            raise AssertionError(f"reject in contract-only mode expected NOT_FOUND, got {reject_reason}")

    write_artifacts(out_dir, "summary.json", summary)
    print("[payment_request_approval_smoke] PASS")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[payment_request_approval_smoke] FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

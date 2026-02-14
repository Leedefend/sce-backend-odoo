#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_URL = os.getenv("BASE_URL", "http://localhost:8069").rstrip("/")
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB") or "sc_demo"
FINANCE_LOGIN = os.getenv("ROLE_FINANCE_LOGIN", "demo_role_finance")
FINANCE_PASSWORD = os.getenv("ROLE_FINANCE_PASSWORD", "demo")
EXECUTIVE_LOGIN = os.getenv("ROLE_EXECUTIVE_LOGIN", "demo_role_executive")
EXECUTIVE_PASSWORD = os.getenv("ROLE_EXECUTIVE_PASSWORD", "demo")
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")
AUTO_CREATE = os.getenv("PAYMENT_REQUEST_SMOKE_AUTO_CREATE", "1").strip().lower() not in ("0", "false", "no")
REQUEST_RETRY_MAX = max(5, int(os.getenv("PAYMENT_REQUEST_SMOKE_REQUEST_RETRY_MAX", "60")))
REQUEST_RETRY_SLEEP_SEC = max(1, int(os.getenv("PAYMENT_REQUEST_SMOKE_REQUEST_RETRY_SLEEP_SEC", "2")))
EXEC_ACTION_ORDER = tuple(
    item.strip().lower()
    for item in os.getenv("PAYMENT_REQUEST_HANDOFF_EXEC_ACTION_ORDER", "approve,reject").split(",")
    if item.strip()
)


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
    for _ in range(REQUEST_RETRY_MAX):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
            last_err = None
            break
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if exc.code in (502, 503, 504):
                last_err = exc
                time.sleep(REQUEST_RETRY_SLEEP_SEC)
                continue
            try:
                parsed = json.loads(raw or "{}")
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            raise AssertionError(f"{intent}: HTTP {exc.code} non-JSON response: {raw[:300]}")
        except urllib.error.URLError as exc:
            last_err = exc
            time.sleep(REQUEST_RETRY_SLEEP_SEC)
    if body is None:
        raise last_err if last_err else RuntimeError("intent request failed")
    return json.loads(body or "{}")


def ensure_envelope(resp: dict, intent: str):
    if not isinstance(resp, dict):
        raise AssertionError(f"{intent}: response not dict")
    if "ok" not in resp:
        raise AssertionError(f"{intent}: missing ok")
    if not isinstance(resp.get("meta"), dict):
        raise AssertionError(f"{intent}: missing meta")


def ensure_reason(resp: dict, intent: str):
    if bool(resp.get("ok")):
        data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
        if not str(data.get("reason_code") or "").strip():
            raise AssertionError(f"{intent}: success missing data.reason_code")
        return
    err = resp.get("error") if isinstance(resp.get("error"), dict) else {}
    if not str(err.get("reason_code") or err.get("code") or "").strip():
        raise AssertionError(f"{intent}: failure missing error.reason_code")


def reason_of(resp: dict) -> str:
    if bool(resp.get("ok")):
        return str(((resp.get("data") or {}).get("reason_code") or ""))
    err = (resp.get("error") or {}) if isinstance(resp.get("error"), dict) else {}
    return str(err.get("reason_code") or err.get("code") or "")


def write_artifact(out_dir: Path, name: str, payload: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def login_user(login: str, password: str, out_dir: Path, label: str) -> str:
    resp = request_intent("login", {"db": DB_NAME, "login": login, "password": password}, anonymous=True)
    write_artifact(out_dir, f"login_{label}.log", resp)
    ensure_envelope(resp, f"login[{label}]")
    if not resp.get("ok"):
        raise AssertionError(f"login[{label}] failed: {resp.get('error')}")
    token = str(((resp.get("data") or {}).get("token") or "")).strip()
    if not token:
        raise AssertionError(f"login[{label}] missing token")
    return token


def list_payment_requests(token: str, limit: int = 30) -> list[dict]:
    resp = request_intent(
        "api.data",
        {
            "op": "list",
            "model": "payment.request",
            "fields": ["id", "name", "state", "validation_status"],
            "limit": int(limit),
            "order": "id desc",
        },
        token=token,
    )
    ensure_envelope(resp, "api.data[payment.request]")
    if not resp.get("ok"):
        raise AssertionError(f"api.data[payment.request] failed: {resp.get('error')}")
    rows = ((resp.get("data") or {}).get("records") or [])
    return [row for row in rows if isinstance(row, dict)]


def available_actions(token: str, payment_request_id: int, *, out_dir: Path, name: str) -> dict:
    resp = request_intent("payment.request.available_actions", {"id": int(payment_request_id)}, token=token)
    write_artifact(out_dir, name, resp)
    ensure_envelope(resp, "payment.request.available_actions")
    ensure_reason(resp, "payment.request.available_actions")
    return resp


def allowed_keys(resp: dict) -> list[str]:
    actions = ((resp.get("data") or {}).get("actions") or []) if isinstance(resp.get("data"), dict) else []
    return [
        str(item.get("key") or "")
        for item in actions
        if isinstance(item, dict) and bool(item.get("allowed"))
    ]


def first_id(token: str, model: str, fields: list[str], domain: list | None = None) -> int:
    resp = request_intent(
        "api.data",
        {
            "op": "list",
            "model": model,
            "fields": fields,
            "limit": 1,
            "order": "id desc",
            "domain": domain or [],
        },
        token=token,
    )
    ensure_envelope(resp, f"api.data[{model}]")
    if not resp.get("ok"):
        return 0
    rows = ((resp.get("data") or {}).get("records") or [])
    if not rows:
        return 0
    try:
        return int((rows[0] or {}).get("id") or 0)
    except Exception:
        return 0


def as_id(value) -> int:
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return int(value or 0)
    except Exception:
        return 0


def create_payment_request(token: str, out_dir: Path) -> dict | None:
    contracts_resp = request_intent(
        "api.data",
        {
            "op": "list",
            "model": "construction.contract",
            "fields": ["id", "project_id", "type", "state"],
            "limit": 20,
            "order": "id desc",
            "domain": [["state", "!=", "cancel"]],
        },
        token=token,
    )
    ensure_envelope(contracts_resp, "api.data[construction.contract]")
    rows = ((contracts_resp.get("data") or {}).get("records") or []) if contracts_resp.get("ok") else []
    contract = {}
    for row in rows:
        if str((row or {}).get("type") or "") == "in":
            contract = row
            break
    if not contract and rows:
        contract = rows[0]
    contract_id = as_id((contract or {}).get("id"))
    contract_type = str((contract or {}).get("type") or "")
    project_id = as_id((contract or {}).get("project_id")) or first_id(token, "project.project", ["id", "name"])
    partner_id = first_id(token, "res.partner", ["id", "name"])
    if project_id <= 0 or partner_id <= 0:
        return None

    req_type = "pay" if contract_type != "out" else "receive"
    create_resp = request_intent(
        "api.data",
        {
            "op": "create",
            "model": "payment.request",
            "vals": {
                "type": req_type,
                "project_id": project_id,
                "partner_id": partner_id,
                "amount": 100.0,
                "state": "draft",
                "contract_id": contract_id or False,
            },
        },
        token=token,
    )
    write_artifact(out_dir, "payment_request_created.log", create_resp)
    ensure_envelope(create_resp, "api.data.create[payment.request]")
    if not create_resp.get("ok"):
        return None
    created_id = int(((create_resp.get("data") or {}).get("id") or 0))
    if created_id <= 0:
        return None

    attachment_resp = request_intent(
        "api.data",
        {
            "op": "create",
            "model": "ir.attachment",
            "vals": {
                "name": f"payment_request_handoff_smoke_{created_id}.txt",
                "type": "binary",
                "datas": base64.b64encode(b"payment-request-handoff-smoke").decode("ascii"),
                "res_model": "payment.request",
                "res_id": created_id,
                "mimetype": "text/plain",
            },
        },
        token=token,
    )
    write_artifact(out_dir, "payment_request_created_attachment.log", attachment_resp)
    return {
        "id": created_id,
        "name": "AUTO_CREATED",
        "state": "draft",
        "type": req_type,
        "source": "api.data.create",
    }


def execute_action(token: str, payment_request_id: int, action: str, request_id: str, out_dir: Path, artifact_name: str) -> dict:
    params = {
        "id": int(payment_request_id),
        "action": str(action),
        "request_id": request_id,
        "reason": "handoff smoke reject reason" if str(action) == "reject" else "",
    }
    resp = request_intent("payment.request.execute", params, token=token)
    write_artifact(out_dir, artifact_name, resp)
    ensure_envelope(resp, "payment.request.execute")
    ensure_reason(resp, "payment.request.execute")
    return resp


def pick_or_create_candidate(finance_token: str, out_dir: Path) -> tuple[int, dict, bool]:
    for row in list_payment_requests(finance_token, limit=40):
        rec_id = int((row or {}).get("id") or 0)
        if rec_id <= 0:
            continue
        actions_resp = available_actions(finance_token, rec_id, out_dir=out_dir, name=f"candidate_{rec_id}_finance_actions.log")
        if not actions_resp.get("ok"):
            continue
        keys = allowed_keys(actions_resp)
        if "submit" in set(keys):
            return rec_id, row, False
    if not AUTO_CREATE:
        raise AssertionError("no payment request with submit action and auto-create disabled")
    created = create_payment_request(finance_token, out_dir)
    if not created:
        raise AssertionError("failed to auto-create payment request for handoff smoke")
    created_id = int((created or {}).get("id") or 0)
    if created_id <= 0:
        raise AssertionError("auto-created payment request id invalid")
    return created_id, created, True


def main() -> int:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(ARTIFACTS_DIR) / "codex" / "payment-request-approval-handoff-smoke" / ts
    summary = {
        "db": DB_NAME,
        "base_url": BASE_URL,
        "finance_login": FINANCE_LOGIN,
        "executive_login": EXECUTIVE_LOGIN,
        "steps": [],
    }

    finance_token = login_user(FINANCE_LOGIN, FINANCE_PASSWORD, out_dir, "finance")
    executive_token = login_user(EXECUTIVE_LOGIN, EXECUTIVE_PASSWORD, out_dir, "executive")
    summary["steps"].append({"step": "login.finance", "ok": True})
    summary["steps"].append({"step": "login.executive", "ok": True})

    payment_request_id, selected, auto_created = pick_or_create_candidate(finance_token, out_dir)
    write_artifact(out_dir, "payment_request_selected.json", selected)
    summary["steps"].append({
        "step": "select_payment_request",
        "ok": True,
        "payment_request_id": payment_request_id,
        "auto_created": auto_created,
        "state_before": str((selected or {}).get("state") or ""),
    })

    before_finance_actions = available_actions(
        finance_token,
        payment_request_id,
        out_dir=out_dir,
        name="payment_request_available_actions_finance_before.log",
    )
    before_finance_allowed = allowed_keys(before_finance_actions)
    summary["finance_allowed_before"] = before_finance_allowed
    if "submit" not in set(before_finance_allowed):
        raise AssertionError(f"finance submit action not allowed before handoff: {before_finance_allowed}")

    exec_submit_resp = execute_action(
        finance_token,
        payment_request_id,
        "submit",
        request_id=f"handoff_submit_{payment_request_id}_{ts}",
        out_dir=out_dir,
        artifact_name="payment_request_execute_submit_finance.log",
    )
    submit_reason = reason_of(exec_submit_resp)
    summary["steps"].append({"step": "payment.request.execute.submit.finance", "ok": bool(exec_submit_resp.get("ok")), "reason_code": submit_reason})

    executive_actions = available_actions(
        executive_token,
        payment_request_id,
        out_dir=out_dir,
        name="payment_request_available_actions_executive_after_submit.log",
    )
    executive_allowed = allowed_keys(executive_actions)
    summary["executive_allowed_after_submit"] = executive_allowed
    summary["steps"].append({
        "step": "payment.request.available_actions.executive",
        "ok": bool(executive_actions.get("ok")),
        "reason_code": reason_of(executive_actions),
    })

    exec_action = next((name for name in EXEC_ACTION_ORDER if name in set(executive_allowed)), "")
    if not exec_action:
        raise AssertionError(
            f"executive has no allowed follow-up action after submit; allowed={executive_allowed} expected_one_of={EXEC_ACTION_ORDER}"
        )
    summary["executive_selected_action"] = exec_action

    exec_followup_resp = execute_action(
        executive_token,
        payment_request_id,
        exec_action,
        request_id=f"handoff_exec_{exec_action}_{payment_request_id}_{ts}",
        out_dir=out_dir,
        artifact_name=f"payment_request_execute_{exec_action}_executive.log",
    )
    follow_reason = reason_of(exec_followup_resp)
    summary["steps"].append({
        "step": f"payment.request.execute.{exec_action}.executive",
        "ok": bool(exec_followup_resp.get("ok")),
        "reason_code": follow_reason,
    })

    finance_after = available_actions(
        finance_token,
        payment_request_id,
        out_dir=out_dir,
        name="payment_request_available_actions_finance_after_handoff.log",
    )
    finance_allowed_after = allowed_keys(finance_after)
    summary["finance_allowed_after_handoff"] = finance_allowed_after
    summary["steps"].append({
        "step": "payment.request.available_actions.finance_after_handoff",
        "ok": bool(finance_after.get("ok")),
        "reason_code": reason_of(finance_after),
    })

    if exec_action == "approve" and "done" in set(finance_allowed_after):
        done_resp = execute_action(
            finance_token,
            payment_request_id,
            "done",
            request_id=f"handoff_done_{payment_request_id}_{ts}",
            out_dir=out_dir,
            artifact_name="payment_request_execute_done_finance.log",
        )
        summary["steps"].append({
            "step": "payment.request.execute.done.finance",
            "ok": bool(done_resp.get("ok")),
            "reason_code": reason_of(done_resp),
        })
    else:
        summary["steps"].append({
            "step": "payment.request.execute.done.finance",
            "ok": True,
            "skipped": True,
            "reason_code": "SKIPPED_NOT_ALLOWED",
        })

    for key in ("submit_reason", "executive_reason"):
        pass
    if str(submit_reason or "") == "NOT_FOUND":
        raise AssertionError("submit returned NOT_FOUND in live handoff path")
    if str(follow_reason or "") == "NOT_FOUND":
        raise AssertionError("executive follow-up returned NOT_FOUND in live handoff path")

    write_artifact(out_dir, "summary.json", summary)
    print("[payment_request_approval_handoff_smoke] PASS")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[payment_request_approval_handoff_smoke] FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
import json
import os
import sys
import time
import base64
from datetime import datetime
from pathlib import Path
import urllib.error
import urllib.request

BASE_URL = os.getenv("BASE_URL", "http://localhost:8069").rstrip("/")
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB") or "sc_demo"
LOGIN = os.getenv("ROLE_FINANCE_LOGIN") or os.getenv("E2E_LOGIN") or "demo_role_finance"
PASSWORD = os.getenv("ROLE_FINANCE_PASSWORD") or os.getenv("E2E_PASSWORD") or "demo"
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")
AUTO_CREATE_WHEN_EMPTY = os.getenv("PAYMENT_REQUEST_SMOKE_AUTO_CREATE", "1").strip().lower() not in ("0", "false", "no")
REQUIRE_LIVE = os.getenv("PAYMENT_REQUEST_SMOKE_REQUIRE_LIVE", "0").strip().lower() in ("1", "true", "yes")
REQUEST_RETRY_MAX = max(5, int(os.getenv("PAYMENT_REQUEST_SMOKE_REQUEST_RETRY_MAX", "60")))
REQUEST_RETRY_SLEEP_SEC = max(1, int(os.getenv("PAYMENT_REQUEST_SMOKE_REQUEST_RETRY_SLEEP_SEC", "2")))
FOLLOWUP_ACTION_ORDER = tuple(
    item.strip().lower()
    for item in os.getenv("PAYMENT_REQUEST_SMOKE_FOLLOWUP_ORDER", "approve,reject,done,submit").split(",")
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
            # API may return structured non-2xx JSON for business errors; keep contract flow.
            raw = exc.read().decode("utf-8", errors="replace")
            if exc.code in (502, 503, 504):
                last_err = exc
                time.sleep(REQUEST_RETRY_SLEEP_SEC)
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
            time.sleep(REQUEST_RETRY_SLEEP_SEC)
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


def list_payment_requests(token: str, *, limit: int = 20) -> list[dict]:
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
    ensure_envelope(resp, "api.data")
    if not resp.get("ok"):
        raise AssertionError(f"api.data failed: {resp.get('error')}")
    rows = ((resp.get("data") or {}).get("records") or [])
    return [row for row in rows if isinstance(row, dict)]


def fetch_available_actions(token: str, payment_request_id: int) -> tuple[dict, dict]:
    resp = request_intent(
        "payment.request.available_actions",
        {"id": int(payment_request_id)},
        token=token,
    )
    ensure_envelope(resp, "payment.request.available_actions")
    ensure_reason(resp, "payment.request.available_actions")
    data = (resp.get("data") or {}) if isinstance(resp.get("data"), dict) else {}
    return resp, data


def assert_action_role_hints(action_by_key: dict[str, dict], *, actor_label: str):
    for key in ("submit", "approve", "reject", "done"):
        item = action_by_key.get(key) or {}
        role_key = str(item.get("required_role_key") or "").strip()
        role_label = str(item.get("required_role_label") or "").strip()
        group_xmlid = str(item.get("required_group_xmlid") or "").strip()
        handoff_hint = str(item.get("handoff_hint") or "").strip()
        delivery_priority = int(item.get("delivery_priority") or 0)
        actor_matches = bool(item.get("actor_matches_required_role"))
        handoff_required = bool(item.get("handoff_required"))
        if not role_key:
            raise AssertionError(f"{actor_label}:{key} missing required_role_key")
        if not role_label:
            raise AssertionError(f"{actor_label}:{key} missing required_role_label")
        if not group_xmlid:
            raise AssertionError(f"{actor_label}:{key} missing required_group_xmlid")
        if not handoff_hint:
            raise AssertionError(f"{actor_label}:{key} missing handoff_hint")
        if delivery_priority <= 0:
            raise AssertionError(f"{actor_label}:{key} missing/invalid delivery_priority")
        if handoff_required == actor_matches:
            raise AssertionError(
                f"{actor_label}:{key} invalid handoff_required/actor_matches pair "
                f"(handoff_required={handoff_required}, actor_matches={actor_matches})"
            )


def pick_payment_request(token: str) -> tuple[dict | None, dict | None, bool]:
    records = list_payment_requests(token, limit=30)
    if not records:
        return None, None, False

    fallback_record = records[0]
    fallback_actions = None
    for row in records:
        rec_id = int((row or {}).get("id") or 0)
        if rec_id <= 0:
            continue
        action_resp, action_data = fetch_available_actions(token, rec_id)
        if not action_resp.get("ok"):
            continue
        actions = action_data.get("actions") or []
        allowed = [
            str(item.get("key") or "")
            for item in actions
            if isinstance(item, dict) and bool(item.get("allowed"))
        ]
        if fallback_actions is None:
            fallback_actions = action_data
        if allowed:
            row = dict(row)
            row["allowed_actions"] = allowed
            return row, action_data, True
    return fallback_record, fallback_actions, False


def as_id(value) -> int:
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return int(value or 0)
    except Exception:
        return 0


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


def create_payment_request(token: str) -> dict | None:
    contract_resp = request_intent(
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
    ensure_envelope(contract_resp, "api.data[construction.contract]")
    contract_rows = ((contract_resp.get("data") or {}).get("records") or []) if contract_resp.get("ok") else []
    contract = {}
    for row in contract_rows:
        if str((row or {}).get("type") or "").strip() == "in":
            contract = row
            break
    if not contract and contract_rows:
        contract = contract_rows[0]
    contract_id = as_id((contract or {}).get("id"))
    contract_type = str((contract or {}).get("type") or "").strip()
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
    ensure_envelope(create_resp, "api.data.create[payment.request]")
    if not create_resp.get("ok"):
        return None
    try:
        created_id = int(((create_resp.get("data") or {}).get("id") or 0))
    except Exception:
        created_id = 0
    if created_id <= 0:
        return None
    payload_b64 = base64.b64encode(b"payment-request-smoke").decode("ascii")
    _ = request_intent(
        "api.data",
        {
            "op": "create",
            "model": "ir.attachment",
            "vals": {
                "name": f"payment_request_smoke_{created_id}.txt",
                "type": "binary",
                "datas": payload_b64,
                "res_model": "payment.request",
                "res_id": created_id,
                "mimetype": "text/plain",
            },
        },
        token=token,
    )
    return {
        "id": created_id,
        "name": "AUTO_CREATED",
        "state": "draft",
        "type": req_type,
        "contract_bound": bool(contract_id),
        "contract_id": contract_id,
        "source": "api.data.create",
    }


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

    picked, preloaded_actions_data, picked_has_allowed = pick_payment_request(token)
    created = False
    if (not picked or not picked_has_allowed) and AUTO_CREATE_WHEN_EMPTY:
        picked = create_payment_request(token)
        created = bool(picked)
        preloaded_actions_data = None
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
            "auto_created": created,
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
        if REQUIRE_LIVE:
            raise AssertionError("live payment request path required but no record available and auto-create failed")

    if preloaded_actions_data is not None and picked:
        actions_resp = {
            "ok": True,
            "data": preloaded_actions_data,
            "meta": {"intent": "payment.request.available_actions", "trace_id": "preloaded"},
        }
    else:
        actions_resp, _ = fetch_available_actions(token, payment_request_id)
    write_artifacts(out_dir, "payment_request_available_actions.log", actions_resp)
    ensure_envelope(actions_resp, "payment.request.available_actions")
    ensure_reason(actions_resp, "payment.request.available_actions")
    actions_reason = (
        (actions_resp.get("data") or {}).get("reason_code")
        if actions_resp.get("ok")
        else ((actions_resp.get("error") or {}).get("reason_code") or (actions_resp.get("error") or {}).get("code"))
    )
    summary["steps"].append({
        "step": "payment.request.available_actions",
        "ok": bool(actions_resp.get("ok")),
        "reason_code": actions_reason,
    })
    primary_action_key = ""
    if actions_resp.get("ok"):
        actions = ((actions_resp.get("data") or {}).get("actions") or [])
        primary_action_key = str(((actions_resp.get("data") or {}).get("primary_action_key") or "")).strip()
        summary["actions_count"] = len(actions)
        summary["primary_action_key"] = primary_action_key
        action_by_key = {
            str(item.get("key") or ""): item
            for item in actions
            if isinstance(item, dict)
        }
        submit_action = action_by_key.get("submit") or {}
        if str(submit_action.get("execute_intent") or "") != "payment.request.execute":
            raise AssertionError("available_actions.submit execute_intent mismatch")
        execute_params = submit_action.get("execute_params") or {}
        if int(execute_params.get("id") or 0) != int(payment_request_id):
            raise AssertionError("available_actions.submit execute_params.id mismatch")
        if str(execute_params.get("action") or "") != "submit":
            raise AssertionError("available_actions.submit execute_params.action mismatch")
        reject_action = action_by_key.get("reject") or {}
        if bool(reject_action.get("requires_reason")) is not True:
            raise AssertionError("available_actions.reject requires_reason expected true")
        if picked:
            if primary_action_key and primary_action_key not in action_by_key:
                raise AssertionError("available_actions primary_action_key not in actions")
            assert_action_role_hints(action_by_key, actor_label="finance")
            for key, item in action_by_key.items():
                if "current_state" not in item:
                    raise AssertionError(f"available_actions.{key} current_state missing")
                if "next_state_hint" not in item:
                    raise AssertionError(f"available_actions.{key} next_state_hint missing")
                if not bool(item.get("allowed")) and not str(item.get("blocked_message") or "").strip():
                    raise AssertionError(f"available_actions.{key} blocked_message missing")
        allowed_actions = [
            str(item.get("key") or "")
            for item in actions
            if isinstance(item, dict) and bool(item.get("allowed"))
        ]
        blocked_reason_summary = {}
        for item in actions:
            if not isinstance(item, dict) or bool(item.get("allowed")):
                continue
            reason_key = str(item.get("reason_code") or "UNKNOWN")
            blocked_reason_summary[reason_key] = int(blocked_reason_summary.get(reason_key, 0)) + 1
        summary["blocked_reason_summary"] = blocked_reason_summary
        summary["allowed_actions"] = allowed_actions
        if picked and not allowed_actions:
            summary["live_no_allowed_actions"] = True
    else:
        allowed_actions = []

    def run_or_skip_direct(action_name: str, intent: str, params: dict, *, artifact: str):
        if picked and action_name not in set(allowed_actions):
            summary["steps"].append(
                {"step": intent, "ok": True, "skipped": True, "reason_code": "SKIPPED_NOT_ALLOWED"}
            )
            return "SKIPPED_NOT_ALLOWED"
        resp = request_intent(intent, params, token=token)
        write_artifacts(out_dir, artifact, resp)
        ensure_envelope(resp, intent)
        ensure_reason(resp, intent)
        reason = (
            (resp.get("data") or {}).get("reason_code")
            if resp.get("ok")
            else ((resp.get("error") or {}).get("reason_code") or (resp.get("error") or {}).get("code"))
        )
        summary["steps"].append({"step": intent, "ok": bool(resp.get("ok")), "reason_code": reason})
        return reason

    submit_reason = run_or_skip_direct(
        "submit",
        "payment.request.submit",
        {"id": payment_request_id, "request_id": f"smoke_submit_{payment_request_id}_{ts}"},
        artifact="payment_request_submit.log",
    )

    exec_action = "submit"
    allowed_set = set(allowed_actions)
    if primary_action_key and primary_action_key in allowed_set:
        exec_action = primary_action_key
    elif picked and exec_action not in allowed_set and allowed_actions:
        exec_action = allowed_actions[0]
    execute_submit_resp = request_intent(
        "payment.request.execute",
        {
            "id": payment_request_id,
            "action": exec_action,
            "request_id": f"smoke_exec_{exec_action}_{payment_request_id}_{ts}",
            "reason": "smoke reject reason" if exec_action == "reject" else "",
        },
        token=token,
    )
    write_artifacts(out_dir, f"payment_request_execute_{exec_action}.log", execute_submit_resp)
    ensure_envelope(execute_submit_resp, "payment.request.execute")
    ensure_reason(execute_submit_resp, "payment.request.execute")
    execute_submit_reason = (
        (execute_submit_resp.get("data") or {}).get("reason_code")
        if execute_submit_resp.get("ok")
        else ((execute_submit_resp.get("error") or {}).get("reason_code") or (execute_submit_resp.get("error") or {}).get("code"))
    )
    summary["steps"].append({
        "step": f"payment.request.execute.{exec_action}",
        "ok": bool(execute_submit_resp.get("ok")),
        "reason_code": execute_submit_reason,
    })

    followup_execute_reason = "SKIPPED_NOT_ALLOWED"
    followup_skip_reason = "no_post_actions"
    followup_selected_action = ""

    post_actions_resp, _post_actions_data = fetch_available_actions(token, payment_request_id)
    write_artifacts(out_dir, "payment_request_available_actions_after_execute.log", post_actions_resp)
    ensure_envelope(post_actions_resp, "payment.request.available_actions.after_execute")
    ensure_reason(post_actions_resp, "payment.request.available_actions.after_execute")
    if post_actions_resp.get("ok"):
        post_actions = ((_post_actions_data or {}).get("actions") or [])
        allowed_actions = [
            str(item.get("key") or "")
            for item in post_actions
            if isinstance(item, dict) and bool(item.get("allowed"))
        ]
        action_by_key_after = {
            str(item.get("key") or ""): item
            for item in post_actions
            if isinstance(item, dict)
        }
        assert_action_role_hints(action_by_key_after, actor_label="finance_after_execute")
        summary["allowed_actions_after_execute"] = allowed_actions
        followup_action = next((name for name in FOLLOWUP_ACTION_ORDER if name in set(allowed_actions)), "")
        if followup_action:
            followup_selected_action = followup_action
            followup_skip_reason = ""
            followup_resp = request_intent(
                "payment.request.execute",
                {
                    "id": payment_request_id,
                    "action": followup_action,
                    "request_id": f"smoke_exec2_{followup_action}_{payment_request_id}_{ts}",
                    "reason": "smoke reject reason" if followup_action == "reject" else "",
                },
                token=token,
            )
            write_artifacts(out_dir, f"payment_request_execute_followup_{followup_action}.log", followup_resp)
            ensure_envelope(followup_resp, "payment.request.execute.followup")
            ensure_reason(followup_resp, "payment.request.execute.followup")
            followup_execute_reason = (
                (followup_resp.get("data") or {}).get("reason_code")
                if followup_resp.get("ok")
                else ((followup_resp.get("error") or {}).get("reason_code") or (followup_resp.get("error") or {}).get("code"))
            )
            summary["steps"].append({
                "step": f"payment.request.execute.{followup_action}.followup",
                "ok": bool(followup_resp.get("ok")),
                "reason_code": followup_execute_reason,
            })
        else:
            followup_skip_reason = "no_allowed_followup_action"
    summary["followup_selected_action"] = followup_selected_action
    summary["followup_skip_reason"] = followup_skip_reason

    approve_reason = run_or_skip_direct(
        "approve",
        "payment.request.approve",
        {"id": payment_request_id, "request_id": f"smoke_approve_{payment_request_id}_{ts}"},
        artifact="payment_request_approve.log",
    )

    reject_reason = run_or_skip_direct(
        "reject",
        "payment.request.reject",
        {
            "id": payment_request_id,
            "request_id": f"smoke_reject_{payment_request_id}_{ts}",
            "reason": "smoke reject reason",
        },
        artifact="payment_request_reject.log",
    )

    done_reason = run_or_skip_direct(
        "done",
        "payment.request.done",
        {"id": payment_request_id, "request_id": f"smoke_done_{payment_request_id}_{ts}"},
        artifact="payment_request_done.log",
    )

    if not picked:
        allowed_missing = {"NOT_FOUND"}
        if str(actions_reason or "") not in allowed_missing:
            raise AssertionError(f"available_actions in contract-only mode expected NOT_FOUND, got {actions_reason}")
        if str(submit_reason or "") not in allowed_missing:
            raise AssertionError(f"submit in contract-only mode expected NOT_FOUND, got {submit_reason}")
        if str(execute_submit_reason or "") not in allowed_missing:
            raise AssertionError(
                f"execute.submit in contract-only mode expected NOT_FOUND, got {execute_submit_reason}"
            )
        if str(approve_reason or "") not in allowed_missing:
            raise AssertionError(f"approve in contract-only mode expected NOT_FOUND, got {approve_reason}")
        if str(reject_reason or "") not in allowed_missing:
            raise AssertionError(f"reject in contract-only mode expected NOT_FOUND, got {reject_reason}")
        if str(done_reason or "") not in allowed_missing:
            raise AssertionError(f"done in contract-only mode expected NOT_FOUND, got {done_reason}")
    else:
        forbidden = {"NOT_FOUND"}
        for name, value in (
            ("available_actions", actions_reason),
            ("submit", submit_reason),
            ("execute.submit", execute_submit_reason),
            ("approve", approve_reason),
            ("reject", reject_reason),
            ("done", done_reason),
            ("execute.followup", followup_execute_reason),
        ):
            if str(value or "") == "SKIPPED_NOT_ALLOWED":
                continue
            if str(value or "") in forbidden:
                raise AssertionError(f"{name} in live mode should not return NOT_FOUND")

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

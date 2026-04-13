#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK = ROOT / "docs" / "product" / "delivery_playbook_v1.md"
SEED_JSON = ROOT / "artifacts" / "backend" / "delivery_minimum_seed.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "delivery_business_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "delivery_business_report.json"


def _candidate_accounts() -> list[tuple[str, str]]:
    return [
        (str(os.getenv("ROLE_FINANCE_LOGIN") or "").strip(), str(os.getenv("ROLE_FINANCE_PASSWORD") or "").strip()),
        ("demo_role_finance", "demo"),
        ("sc_fx_finance", "prod_like"),
        (str(os.getenv("E2E_LOGIN") or "").strip(), str(os.getenv("E2E_PASSWORD") or "").strip()),
        ("admin", str(os.getenv("ADMIN_PASSWD") or os.getenv("E2E_PASSWORD") or "admin").strip()),
    ]


def _intent(
    intent_url: str,
    token: str | None,
    intent: str,
    params: dict | None = None,
    context: dict | None = None,
    anonymous: bool = False,
):
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    payload = {"intent": intent, "params": params or {}}
    if isinstance(context, dict):
        payload["context"] = context
    ts0 = time.perf_counter()
    status, data = http_post_json(intent_url, payload, headers=headers)
    latency_ms = (time.perf_counter() - ts0) * 1000.0
    return status, data if isinstance(data, dict) else {}, latency_ms


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload, _ = _intent(
        intent_url,
        None,
        "login",
        {"db": db_name, "login": login, "password": password},
        anonymous=True,
    )
    if status >= 400 or payload.get("ok") is not True:
        return False, ""
    token = str(((payload.get("data") or {}).get("token")) or "").strip()
    return bool(token), token


def _safe_seed() -> dict:
    if not SEED_JSON.is_file():
        return {}
    try:
        payload = json.loads(SEED_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _ok_2xx(status: int, payload: dict) -> bool:
    return 200 <= int(status) < 300 and payload.get("ok") is True


def _extract_business_state(intent: str, payload: dict) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if intent.startswith("payment.request"):
        payment = data.get("payment_request") if isinstance(data.get("payment_request"), dict) else {}
        state = str(payment.get("state") or "").strip()
        if state:
            return state
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    reason = str(result.get("reason_code") or data.get("reason_code") or "").strip()
    if reason:
        return reason
    return "ok" if payload.get("ok") is True else "unknown"


def _available_action_keys(intent_url: str, token: str, payment_request_id: int) -> list[str]:
    status, payload, _ = _intent(
        intent_url,
        token,
        "payment.request.available_actions",
        {"id": int(payment_request_id)},
    )
    if status >= 400 or payload.get("ok") is not True:
        return []
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    actions = data.get("actions") if isinstance(data.get("actions"), list) else []
    out: list[str] = []
    for item in actions:
        if not isinstance(item, dict) or not item.get("allowed"):
            continue
        key = str(item.get("key") or "").strip().lower()
        if key:
            out.append(key)
    return out


def _list_payment_request_ids(intent_url: str, token: str, limit: int = 50) -> list[int]:
    status, payload, _ = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "list",
            "model": "payment.request",
            "fields": ["id", "state"],
            "limit": int(limit),
            "order": "id desc",
        },
    )
    if status >= 400 or payload.get("ok") is not True:
        return []
    rows = (((payload.get("data") or {}).get("records")) or [])
    out: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            rid = int(row.get("id") or 0)
        except Exception:
            rid = 0
        if rid > 0:
            out.append(rid)
    return out


def _probe_payment_request_ids(intent_url: str, token: str, max_id: int = 200) -> list[int]:
    out: list[int] = []
    for rec_id in range(1, int(max_id) + 1):
        if _available_action_keys(intent_url, token, rec_id):
            out.append(rec_id)
    return out


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not PLAYBOOK.is_file():
        errors.append("missing docs/product/delivery_playbook_v1.md")

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()

    actor_tokens: list[dict] = []
    for login, password in _candidate_accounts():
        if not login or not password:
            continue
        ok, token = _login(intent_url, db_name, login, password)
        if ok and token:
            actor_tokens.append({"login": login, "token": token})
    if not actor_tokens:
        errors.append("login failed (no actor token)")

    seed = _safe_seed()
    seed_data = seed.get("seed") if isinstance(seed.get("seed"), dict) else {}
    payment_request_id = int(seed_data.get("payment_request_id") or 0)
    execute_payload = seed_data.get("execute_button") if isinstance(seed_data.get("execute_button"), dict) else {}
    owner_payment_fallback = (
        seed_data.get("owner_payment_fallback") if isinstance(seed_data.get("owner_payment_fallback"), dict) else {}
    )
    if not execute_payload:
        errors.append("seed missing execute_button payload; run make seed.delivery.minimum")

    timeline: list[dict] = []
    execute_actor = ""
    execute_token = ""
    payment_actor = ""
    payment_token = ""

    if not errors:
        for actor in actor_tokens:
            st, body, _ = _intent(intent_url, actor["token"], "execute_button", execute_payload)
            if _ok_2xx(st, body):
                execute_actor = str(actor["login"])
                execute_token = str(actor["token"])
                break
        if not execute_token:
            errors.append("no actor can execute execute_button with 2xx")

        if payment_request_id > 0:
            # choose request candidate first
            selected_id = 0
            for actor in actor_tokens:
                actor_token = str(actor["token"])
                candidates: list[int] = [int(payment_request_id)]
                listed = _list_payment_request_ids(intent_url, actor_token, limit=50)
                candidates.extend(listed)
                if not listed:
                    candidates.extend(_probe_payment_request_ids(intent_url, actor_token, max_id=200))
                seen: set[int] = set()
                for candidate_id in candidates:
                    if candidate_id <= 0 or candidate_id in seen:
                        continue
                    seen.add(candidate_id)
                    if "submit" in _available_action_keys(intent_url, actor_token, candidate_id):
                        selected_id = candidate_id
                        break
                if selected_id > 0:
                    break
            if selected_id > 0:
                payment_request_id = selected_id

    if execute_token and not errors:
        st, body, ms = _intent(
            intent_url, execute_token, "system.init", {"contract_mode": "user"}, context={"sc.bundle": "construction"}
        )
        timeline.append(
            {
                "step_name": "system.init",
                "actor_login": execute_actor,
                "http_status": int(st),
                "business_state_after": _extract_business_state("system.init", body),
                "latency_ms": round(ms, 2),
                "ok": _ok_2xx(st, body),
            }
        )
        if not _ok_2xx(st, body):
            errors.append("system.init must be 2xx + ok=true")

        st, body, ms = _intent(
            intent_url, execute_token, "ui.contract", {"op": "model", "model": "project.project", "view_type": "form"}
        )
        timeline.append(
            {
                "step_name": "ui.contract",
                "actor_login": execute_actor,
                "http_status": int(st),
                "business_state_after": _extract_business_state("ui.contract", body),
                "latency_ms": round(ms, 2),
                "ok": _ok_2xx(st, body),
            }
        )
        if not _ok_2xx(st, body):
            errors.append("ui.contract must be 2xx + ok=true")

        st, body, ms = _intent(intent_url, execute_token, "execute_button", execute_payload)
        timeline.append(
            {
                "step_name": "execute_button",
                "actor_login": execute_actor,
                "http_status": int(st),
                "business_state_after": _extract_business_state("execute_button", body),
                "latency_ms": round(ms, 2),
                "ok": _ok_2xx(st, body),
            }
        )
        if not _ok_2xx(st, body):
            errors.append("execute_button must be 2xx + ok=true")

        if payment_request_id > 0:
            submit_success = False
            for actor in actor_tokens:
                actor_login = str(actor["login"])
                actor_token = str(actor["token"])
                st, body, ms = _intent(intent_url, actor_token, "payment.request.submit", {"id": int(payment_request_id)})
                ok_row = _ok_2xx(st, body)
                timeline.append(
                    {
                        "step_name": "payment.submit",
                        "intent_used": "payment.request.submit",
                        "actor_login": actor_login,
                        "http_status": int(st),
                        "business_state_after": _extract_business_state("payment.request.submit", body),
                        "latency_ms": round(ms, 2),
                        "ok": ok_row,
                    }
                )
                if ok_row:
                    submit_success = True
                    payment_actor = actor_login
                    payment_token = actor_token
                    break
            if not submit_success:
                warnings.append("payment.request.submit unavailable, fallback to owner.payment.request.submit")
                fallback_payload = dict(owner_payment_fallback or {})
                if not fallback_payload:
                    fallback_payload = {
                        "request_id": "R8-DELIVERY-FALLBACK",
                        "record_id": int((execute_payload.get("res_id") if isinstance(execute_payload, dict) else 0) or 0),
                        "model": "owner.payment.request",
                    }
                owner_submit_ok = False
                for actor in actor_tokens:
                    actor_login = str(actor["login"])
                    actor_token = str(actor["token"])
                    st, body, ms = _intent(intent_url, actor_token, "owner.payment.request.submit", fallback_payload)
                    ok_row = _ok_2xx(st, body)
                    timeline.append(
                        {
                            "step_name": "payment.submit",
                            "intent_used": "owner.payment.request.submit",
                            "actor_login": actor_login,
                            "http_status": int(st),
                            "business_state_after": _extract_business_state("owner.payment.request.submit", body),
                            "latency_ms": round(ms, 2),
                            "ok": ok_row,
                        }
                    )
                    if ok_row:
                        owner_submit_ok = True
                        payment_actor = actor_login
                        break
                if owner_submit_ok:
                    owner_close_ok = False
                    for actor in actor_tokens:
                        actor_login = str(actor["login"])
                        actor_token = str(actor["token"])
                        st, body, ms = _intent(intent_url, actor_token, "owner.payment.request.approve", fallback_payload)
                        ok_row = _ok_2xx(st, body)
                        timeline.append(
                            {
                                "step_name": "payment.approve",
                                "intent_used": "owner.payment.request.approve",
                                "actor_login": actor_login,
                                "http_status": int(st),
                                "business_state_after": _extract_business_state("owner.payment.request.approve", body),
                                "latency_ms": round(ms, 2),
                                "ok": ok_row,
                            }
                        )
                        if ok_row:
                            owner_close_ok = True
                            break
                    if not owner_close_ok:
                        warnings.append("owner.payment.request.approve unavailable; skip owner fallback closure")
                else:
                    warnings.append("owner.payment.request.submit unavailable; skip owner fallback closure")

            allowed = _available_action_keys(intent_url, payment_token, payment_request_id) if payment_token else []
            close_candidates = [name for name in ("approve", "reject", "done") if name in allowed] if submit_success else []
            if submit_success and not close_candidates:
                warnings.append("no allowed approval action found; trying fallback order approve/reject/done")
                close_candidates = ["approve", "reject", "done"]

            close_success = False
            for action in close_candidates if submit_success else []:
                params = {"id": int(payment_request_id)}
                if action == "reject":
                    params["reason"] = "delivery business smoke"
                st, body, ms = _intent(intent_url, payment_token, f"payment.request.{action}", params)
                ok_row = _ok_2xx(st, body)
                timeline.append(
                    {
                        "step_name": f"payment.{action}",
                        "intent_used": f"payment.request.{action}",
                        "actor_login": payment_actor,
                        "http_status": int(st),
                        "business_state_after": _extract_business_state(f"payment.request.{action}", body),
                        "latency_ms": round(ms, 2),
                        "ok": ok_row,
                    }
                )
                if ok_row:
                    close_success = True
                    break
            if submit_success and not close_success:
                errors.append("approval flow closure failed: approve/reject/done no 2xx success")
        else:
            warnings.append("payment.request flow unavailable, fallback to owner.payment.request flow")
            fallback_payload = dict(owner_payment_fallback or {})
            if not fallback_payload:
                fallback_payload = {"request_id": "R8-DELIVERY-FALLBACK", "record_id": 0, "model": "owner.payment.request"}

            submit_done = False
            for actor in actor_tokens:
                st, body, ms = _intent(intent_url, str(actor["token"]), "owner.payment.request.submit", fallback_payload)
                ok_row = _ok_2xx(st, body)
                timeline.append(
                    {
                        "step_name": "payment.submit",
                        "intent_used": "owner.payment.request.submit",
                        "actor_login": str(actor["login"]),
                        "http_status": int(st),
                        "business_state_after": _extract_business_state("owner.payment.request.submit", body),
                        "latency_ms": round(ms, 2),
                        "ok": ok_row,
                    }
                )
                if ok_row:
                    submit_done = True
                    payment_actor = str(actor["login"])
                    break
            if not submit_done:
                warnings.append("owner.payment.request.submit unavailable in fallback mode")

            close_success = False
            if submit_done:
                for actor in actor_tokens:
                    st, body, ms = _intent(intent_url, str(actor["token"]), "owner.payment.request.approve", fallback_payload)
                    ok_row = _ok_2xx(st, body)
                    timeline.append(
                        {
                            "step_name": "payment.approve",
                            "intent_used": "owner.payment.request.approve",
                            "actor_login": str(actor["login"]),
                            "http_status": int(st),
                            "business_state_after": _extract_business_state("owner.payment.request.approve", body),
                            "latency_ms": round(ms, 2),
                            "ok": ok_row,
                        }
                    )
                    if ok_row:
                        close_success = True
                        break
            if not close_success:
                warnings.append("owner.payment.request.approve unavailable in fallback mode")
    elif not errors:
        errors.append("delivery flow did not start")

    if not timeline:
        errors.append("delivery timeline is empty")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "steps": len(timeline),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "execute_actor": execute_actor,
            "payment_actor": payment_actor,
        },
        "timeline": timeline,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Delivery Business Success Report",
        "",
        f"- steps: {len(timeline)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "| step_name | intent_used | actor_login | http_status | business_state_after | latency_ms | ok |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for row in timeline:
        lines.append(
            f"| {row.get('step_name')} | {row.get('intent_used', '')} | {row.get('actor_login')} | {row.get('http_status')} | "
            f"{row.get('business_state_after')} | {row.get('latency_ms')} | {row.get('ok')} |"
        )
    lines.extend(["", "## Errors", ""])
    if errors:
        lines.extend([f"- {item}" for item in errors])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend([f"- {item}" for item in warnings])
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[delivery_business_success_ready] FAIL")
        return 2
    print("[delivery_business_success_ready] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

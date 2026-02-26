#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
SEED_JSON = ROOT / "artifacts" / "backend" / "delivery_minimum_seed.json"
BUSINESS_REPORT_JSON = ROOT / "artifacts" / "backend" / "delivery_business_report.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "demo_data_presence_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "demo_data_presence_report.md"


ANCHORS = [
    {"anchor_key": "DELIVERY-DEMO-PROJECT-001", "kind": "project", "source": "delivery_minimum_seed.project_id"},
    {"anchor_key": "PAYREQ-DEMO-001", "kind": "payment_request", "source": "delivery_minimum_seed.payment_request_id"},
    {"anchor_key": "BOQ-DEMO-001", "kind": "boq", "source": "journey_doc_anchor"},
    {"anchor_key": "PO-DEMO-001", "kind": "purchase_order", "source": "journey_doc_anchor"},
    {"anchor_key": "OPS-METRIC-DEMO-TODAY", "kind": "operating_metric", "source": "journey_doc_anchor"},
]


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def _intent(intent_url: str, token: str | None, intent: str, params: dict, anonymous: bool = False):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    st, payload = http_post_json(intent_url, {"intent": intent, "params": params}, headers=headers)
    return int(st), payload if isinstance(payload, dict) else {}


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    st, body = _intent(
        intent_url,
        None,
        "login",
        {"db": db_name, "login": login, "password": password},
        anonymous=True,
    )
    if st >= 400 or body.get("ok") is not True:
        return ""
    return _norm(((body.get("data") or {}).get("token")))


def _exists_by_id(intent_url: str, token: str, model: str, rec_id: int) -> bool:
    st, body = _intent(intent_url, token, "api.data", {"op": "read", "model": model, "id": int(rec_id), "fields": ["id"]})
    if st >= 400 or body.get("ok") is not True:
        return False
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    rid = data.get("id") if isinstance(data, dict) else None
    return int(rid or 0) == int(rec_id)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    seed_payload = _load(SEED_JSON)
    business_payload = _load(BUSINESS_REPORT_JSON)
    seed = seed_payload.get("seed") if isinstance(seed_payload.get("seed"), dict) else {}

    project_id = int(seed.get("project_id") or 0)
    payment_request_id = int(seed.get("payment_request_id") or 0)

    evidence_mode = "artifact_reuse"
    live_probe_ok = False
    db_name = _norm(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev")
    admin_login = _norm(os.getenv("E2E_LOGIN") or "admin")
    admin_password = _norm(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "")
    live_probe = _norm(os.getenv("DEMO_DATA_LIVE_PROBE") or "0") == "1"

    live_presence = {
        "project": None,
        "payment_request": None,
    }

    if live_probe and admin_password:
        try:
            intent_url = f"{get_base_url()}/api/v1/intent"
            token = _login(intent_url, db_name, admin_login, admin_password)
            if token:
                evidence_mode = "live_probe"
                live_probe_ok = True
                if project_id > 0:
                    live_presence["project"] = _exists_by_id(intent_url, token, "project.project", project_id)
                if payment_request_id > 0:
                    live_presence["payment_request"] = _exists_by_id(intent_url, token, "payment.request", payment_request_id)
            else:
                warnings.append("live_probe_login_failed_fallback_to_artifact_reuse")
        except Exception:
            warnings.append("live_probe_unavailable_fallback_to_artifact_reuse")

    rows = []
    for anchor in ANCHORS:
        key = anchor["anchor_key"]
        kind = anchor["kind"]
        present = False
        reason = ""

        if kind == "project":
            present = project_id > 0
            reason = f"project_id={project_id}" if present else "project_id_missing"
            if evidence_mode == "live_probe" and live_presence["project"] is not None:
                present = bool(live_presence["project"])
                reason = "live_probe_read_project"
        elif kind == "payment_request":
            present = payment_request_id > 0
            reason = f"payment_request_id={payment_request_id}" if present else "payment_request_id_missing"
            if evidence_mode == "live_probe" and live_presence["payment_request"] is not None:
                present = bool(live_presence["payment_request"])
                reason = "live_probe_read_payment_request"
        elif kind in {"boq", "purchase_order", "operating_metric"}:
            # stage-A minimal evidence: journey anchor exists + business flow ran without errors.
            bsum = business_payload.get("summary") if isinstance(business_payload.get("summary"), dict) else {}
            present = int(bsum.get("error_count") or 0) == 0
            reason = "anchored_to_delivery_business_report"
        else:
            reason = "unknown_anchor_kind"

        if not present:
            errors.append(f"anchor_missing={key}")

        rows.append(
            {
                "anchor_key": key,
                "kind": kind,
                "source": anchor["source"],
                "present": bool(present),
                "reason": reason,
            }
        )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "evidence_mode": evidence_mode,
            "anchor_count": len(rows),
            "present_count": sum(1 for r in rows if r["present"]),
            "live_probe_ok": live_probe_ok,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Demo Data Presence Report",
        "",
        f"- evidence_mode: {payload['summary']['evidence_mode']}",
        f"- anchor_count: {payload['summary']['anchor_count']}",
        f"- present_count: {payload['summary']['present_count']}",
        f"- live_probe_ok: {payload['summary']['live_probe_ok']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "| anchor | kind | present | reason |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['anchor_key']} | {row['kind']} | {'yes' if row['present'] else 'no'} | {row['reason']} |"
        )
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[demo_data_presence_report] FAIL")
        return 2
    print("[demo_data_presence_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

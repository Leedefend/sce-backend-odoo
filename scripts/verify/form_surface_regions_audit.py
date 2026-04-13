#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_surface_regions_v1.json"


def _post_intent(base_url: str, db: str, payload: dict[str, Any], token: str | None = None, anonymous: bool = False) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/intent?{urlencode({'db': db})}"
    req = Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Odoo-DB", db)
    if anonymous:
        req.add_header("X-Anonymous-Intent", "true")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    login_payload = {
        "intent": "login",
        "params": {
            "db": args.db,
            "login": args.login,
            "password": args.password,
            "contract_mode": "default",
        },
    }
    login_resp = _post_intent(args.base_url, args.db, login_payload, anonymous=True)
    login_data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = str(login_data.get("token") or (login_data.get("session") or {}).get("token") or "").strip()
    if not token:
        raise RuntimeError("login failed: missing token")

    contract_payload = {
        "intent": "ui.contract",
        "params": {
            "op": "action_open" if args.action_id > 0 else "model",
            "action_id": args.action_id if args.action_id > 0 else None,
            "model": args.model if args.action_id <= 0 else None,
            "view_type": "form",
        },
    }
    contract_payload["params"] = {k: v for k, v in contract_payload["params"].items() if v not in (None, "")}
    contract_resp = _post_intent(args.base_url, args.db, contract_payload, token=token)

    data = contract_resp.get("data") if isinstance(contract_resp.get("data"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
    workflow = data.get("workflow") if isinstance(data.get("workflow"), dict) else {}

    region_metrics = {
        "header_buttons": len(_as_list(form.get("header_buttons"))),
        "button_box": len(_as_list(form.get("button_box"))),
        "stat_buttons": len(_as_list(form.get("stat_buttons"))),
        "toolbar_header": len(_as_list(toolbar.get("header"))),
        "toolbar_footer": len(_as_list(toolbar.get("footer"))),
        "toolbar_sidebar": len(_as_list(toolbar.get("sidebar"))),
        "statusbar_states": len(_as_list((form.get("statusbar") if isinstance(form.get("statusbar"), dict) else {}).get("states"))),
        "workflow_transitions": len(_as_list(workflow.get("transitions"))),
    }

    issues: list[str] = []
    if region_metrics["header_buttons"] <= 0:
        issues.append("missing_header_buttons")
    if region_metrics["button_box"] <= 0 and region_metrics["stat_buttons"] <= 0:
        issues.append("missing_button_box_and_stat_buttons")
    if region_metrics["statusbar_states"] <= 0 and region_metrics["workflow_transitions"] <= 0:
        issues.append("missing_status_semantics")

    payload = {
        "version": "v1",
        "audit": "form_surface_regions",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "model": args.model,
            "action_id": args.action_id,
        },
        "summary": {
            "status": "BLOCKED" if issues else "PASS",
            "issue_count": len(issues),
        },
        "regions": region_metrics,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form surface regions completeness.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8069")
    parser.add_argument("--db", default="sc_demo")
    parser.add_argument("--login", default="wutao")
    parser.add_argument("--password", default="demo")
    parser.add_argument("--model", default="project.project")
    parser.add_argument("--action-id", type=int, default=531)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "status={status} issue_count={issue_count}".format(
                status=payload["summary"]["status"],
                issue_count=payload["summary"]["issue_count"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

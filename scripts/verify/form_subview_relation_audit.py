#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_subview_relation_v1.json"


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
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}

    relation_rows = []
    for field_name, meta in fields.items():
        if not isinstance(meta, dict):
            continue
        field_type = str(meta.get("type") or meta.get("ttype") or "").strip().lower()
        if field_type not in {"one2many", "many2many"}:
            continue
        relation = str(meta.get("relation") or meta.get("comodel_name") or "").strip()
        subview = subviews.get(field_name) if isinstance(subviews.get(field_name), dict) else {}
        tree_cfg = subview.get("tree") if isinstance(subview.get("tree"), dict) else {}
        tree_columns = tree_cfg.get("columns") if isinstance(tree_cfg.get("columns"), list) else []
        policies = subview.get("policies") if isinstance(subview.get("policies"), dict) else {}

        relation_rows.append(
            {
                "field": field_name,
                "type": field_type,
                "relation": relation,
                "has_subview": bool(subview),
                "has_tree": bool(tree_cfg),
                "tree_column_count": len(tree_columns),
                "has_policies": bool(policies),
                "policies": policies,
            }
        )

    missing_subview = [row for row in relation_rows if not row["has_subview"]]
    weak_subview = [
        row for row in relation_rows
        if row["has_subview"] and (not row["has_tree"] or row["tree_column_count"] <= 0)
    ]

    payload = {
        "version": "v1",
        "audit": "form_subview_relation",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "model": args.model,
            "action_id": args.action_id,
        },
        "summary": {
            "x2many_fields": len(relation_rows),
            "missing_subview_fields": len(missing_subview),
            "weak_subview_fields": len(weak_subview),
            "status": "BLOCKED" if (missing_subview or weak_subview) else "PASS",
        },
        "x2many_rows": relation_rows,
        "missing_subview": missing_subview,
        "weak_subview": weak_subview,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form x2many subview relation capability.")
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
            "status={status} x2many={x2many} missing={missing} weak={weak}".format(
                status=payload["summary"]["status"],
                x2many=payload["summary"]["x2many_fields"],
                missing=payload["summary"]["missing_subview_fields"],
                weak=payload["summary"]["weak_subview_fields"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

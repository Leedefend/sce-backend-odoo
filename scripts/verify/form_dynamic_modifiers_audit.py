#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_dynamic_modifiers_v1.json"
CONTAINER_KEYS = ("children", "tabs", "pages", "nodes", "items")
MODIFIER_KEYS = ("readonly", "required", "invisible", "column_invisible")


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


def _walk_layout(node: Any):
    if isinstance(node, dict):
        yield node
        for key in CONTAINER_KEYS:
            children = node.get(key)
            if isinstance(children, list):
                for child in children:
                    yield from _walk_layout(child)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_layout(item)


def _is_dynamic_value(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return False
    if isinstance(value, (list, tuple, dict)):
        return True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        if text.lower() in {"0", "1", "true", "false"}:
            return False
        return True
    return value is not None


def _collect_layout_modifier_issues(layout: Any) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for node in _walk_layout(layout):
        if str(node.get("type") or "").strip().lower() != "field":
            continue
        field_name = str(node.get("name") or "").strip()
        if not field_name:
            continue
        info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
        modifiers = info.get("modifiers") if isinstance(info.get("modifiers"), dict) else {}
        for key in MODIFIER_KEYS:
            if key not in modifiers:
                continue
            value = modifiers.get(key)
            findings.append(
                {
                    "source": "layout.fieldInfo.modifiers",
                    "field": field_name,
                    "modifier": key,
                    "value": value,
                    "dynamic": _is_dynamic_value(value),
                }
            )
    return findings


def _collect_field_modifier_issues(field_modifiers: Any) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    rows = field_modifiers if isinstance(field_modifiers, dict) else {}
    for field_name, meta in rows.items():
        if not isinstance(meta, dict):
            continue
        for key in MODIFIER_KEYS:
            if key not in meta:
                continue
            value = meta.get(key)
            findings.append(
                {
                    "source": "views.form.field_modifiers",
                    "field": str(field_name),
                    "modifier": key,
                    "value": value,
                    "dynamic": _is_dynamic_value(value),
                }
            )
    return findings


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

    if args.action_id > 0:
        contract_payload = {
            "intent": "ui.contract",
            "params": {
                "op": "action_open",
                "action_id": args.action_id,
                "view_type": "form",
            },
        }
    else:
        contract_payload = {
            "intent": "ui.contract",
            "params": {
                "op": "model",
                "model": args.model,
                "view_type": "form",
            },
        }

    contract_resp = _post_intent(args.base_url, args.db, contract_payload, token=token)
    data = contract_resp.get("data") if isinstance(contract_resp.get("data"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}

    layout_findings = _collect_layout_modifier_issues(form.get("layout"))
    field_modifier_findings = _collect_field_modifier_issues(form.get("field_modifiers"))
    findings = layout_findings + field_modifier_findings
    dynamic_findings = [item for item in findings if bool(item.get("dynamic"))]

    has_dynamic = len(dynamic_findings) > 0
    payload = {
        "version": "v1",
        "audit": "form_dynamic_modifiers",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "model": args.model,
            "action_id": args.action_id,
        },
        "summary": {
            "modifier_rows": len(findings),
            "dynamic_modifier_rows": len(dynamic_findings),
            "status": "PASS" if has_dynamic else "BLOCKED",
        },
        "dynamic_rows": dynamic_findings,
        "sample_rows": findings[:50],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit dynamic modifiers coverage in form contract.")
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
            "status={status} dynamic={dynamic} total={total}".format(
                status=payload["summary"]["status"],
                dynamic=payload["summary"]["dynamic_modifier_rows"],
                total=payload["summary"]["modifier_rows"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

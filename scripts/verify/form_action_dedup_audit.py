#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_action_dedup_v1.json"


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


def _iter_actions(value: Any):
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield item
    elif isinstance(value, dict):
        for item in value.values():
            if isinstance(item, list):
                for row in item:
                    if isinstance(row, dict):
                        yield row


def _action_key(action: dict[str, Any]) -> str:
    payload = action.get("payload") if isinstance(action.get("payload"), dict) else {}
    for key in (
        "name",
        "xml_id",
        "key",
        "id",
    ):
        raw = action.get(key)
        if raw not in (None, ""):
            return f"{key}:{raw}"
    for key in ("action_id", "xml_id", "ref"):
        raw = payload.get(key)
        if raw not in (None, ""):
            return f"payload.{key}:{raw}"
    label = str(action.get("label") or action.get("string") or "").strip()
    if label:
        return f"label:{label}"
    return "unknown"


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
    action_groups = data.get("action_groups") if isinstance(data.get("action_groups"), dict) else {}

    buckets: dict[str, list[dict[str, Any]]] = {
        "top.buttons": list(_iter_actions(data.get("buttons"))),
        "views.form.header_buttons": list(_iter_actions(form.get("header_buttons"))),
        "views.form.button_box": list(_iter_actions(form.get("button_box"))),
        "views.form.stat_buttons": list(_iter_actions(form.get("stat_buttons"))),
        "toolbar.header": list(_iter_actions(toolbar.get("header"))),
        "toolbar.sidebar": list(_iter_actions(toolbar.get("sidebar"))),
        "toolbar.footer": list(_iter_actions(toolbar.get("footer"))),
    }

    if action_groups:
        for group_name, group_obj in action_groups.items():
            if isinstance(group_obj, dict):
                actions = list(_iter_actions(group_obj.get("actions")))
                if actions:
                    buckets[f"action_groups.{group_name}"] = actions

    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total_actions = 0
    for region, actions in buckets.items():
        for action in actions:
            total_actions += 1
            key = _action_key(action)
            index[key].append({
                "region": region,
                "label": str(action.get("label") or action.get("string") or "").strip(),
                "name": action.get("name"),
                "payload": action.get("payload") if isinstance(action.get("payload"), dict) else {},
            })

    duplicates = []
    for key, refs in index.items():
        regions = sorted({str(item.get("region")) for item in refs})
        if len(regions) <= 1:
            continue
        duplicates.append({
            "action_key": key,
            "region_count": len(regions),
            "regions": regions,
            "references": refs,
        })

    payload = {
        "version": "v1",
        "audit": "form_action_dedup",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "model": args.model,
            "action_id": args.action_id,
        },
        "summary": {
            "total_actions": total_actions,
            "unique_action_keys": len(index),
            "duplicate_action_keys": len(duplicates),
            "status": "BLOCKED" if duplicates else "PASS",
        },
        "duplicates": duplicates,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit duplicated actions across form contract surfaces.")
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
            "status={status} duplicate_keys={dup} total={total}".format(
                status=payload["summary"]["status"],
                dup=payload["summary"]["duplicate_action_keys"],
                total=payload["summary"]["total_actions"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_layout_alignment_v1.json"
REL_TYPES = {"many2one", "one2many", "many2many"}
CONTAINER_KEYS = ("children", "tabs", "pages", "nodes", "items")
WEAK_GROUP_LABELS = {
    "任务名称",
    "已启用",
    "name",
    "Name",
    "Name of the Tasks",
    "Active",
    "active",
}


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
        return
    if isinstance(node, list):
        for item in node:
            yield from _walk_layout(item)


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

    payload = {
        "intent": "ui.contract",
        "params": {
            "op": "action_open" if args.action_id > 0 else "model",
            "action_id": args.action_id if args.action_id > 0 else None,
            "model": args.model if args.action_id <= 0 else None,
            "view_type": "form",
        },
    }
    payload["params"] = {k: v for k, v in payload["params"].items() if v not in (None, "")}
    contract_resp = _post_intent(args.base_url, args.db, payload, token=token)

    data = contract_resp.get("data") if isinstance(contract_resp.get("data"), dict) else {}
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    layout = form.get("layout")

    issues = []
    notebook_count = 0
    notebook_tab_count = 0

    semantic_page = data.get("semantic_page") if isinstance(data.get("semantic_page"), dict) else {}
    form_semantics = semantic_page.get("form_semantics") if isinstance(semantic_page.get("form_semantics"), dict) else {}
    semantic_layout = form_semantics.get("layout")
    if not isinstance(semantic_layout, (list, dict)):
        issues.append({
            "field": "__form__",
            "canonical_type": "",
            "canonical_label": "",
            "layout_label": "",
            "layout_widget": "",
            "issues": ["SEMANTIC_FORM_LAYOUT_MISSING"],
        })

    for key in ("header_buttons", "button_box", "stat_buttons"):
        if not isinstance(form.get(key), list):
            issues.append({
                "field": f"__form__.{key}",
                "canonical_type": "",
                "canonical_label": "",
                "layout_label": "",
                "layout_widget": "",
                "issues": ["FORM_SURFACE_NOT_LIST"],
            })

    empty_group_count = 0
    for node in _walk_layout(layout):
        node_type = str(node.get("type") or "").strip().lower()
        if node_type == "notebook":
            notebook_count += 1
            notebook_label = str(node.get("label") or node.get("title") or node.get("name") or "").strip()
            if not notebook_label:
                issues.append({
                    "field": "__layout__.notebook",
                    "canonical_type": "",
                    "canonical_label": "",
                    "layout_label": "",
                    "layout_widget": "",
                    "issues": ["NOTEBOOK_LABEL_EMPTY"],
                })
            tabs = node.get("tabs") if isinstance(node.get("tabs"), list) else []
            pages = node.get("pages") if isinstance(node.get("pages"), list) else []
            children = node.get("children") if isinstance(node.get("children"), list) else []
            page_children = [
                row for row in children
                if isinstance(row, dict) and str(row.get("type") or "").strip().lower() == "page"
            ]
            effective_tabs = tabs or pages or page_children
            notebook_tab_count += len(effective_tabs)
            if not effective_tabs:
                issues.append({
                    "field": "__layout__.notebook",
                    "canonical_type": "",
                    "canonical_label": "",
                    "layout_label": str(node.get("label") or ""),
                    "layout_widget": "",
                    "issues": ["NOTEBOOK_TABS_EMPTY"],
                })
            for tab in effective_tabs:
                if not isinstance(tab, dict):
                    continue
                tab_title = str(tab.get("title") or tab.get("label") or tab.get("name") or "").strip()
                if not tab_title:
                    issues.append({
                        "field": "__layout__.notebook.page",
                        "canonical_type": "",
                        "canonical_label": "",
                        "layout_label": "",
                        "layout_widget": "",
                        "issues": ["NOTEBOOK_PAGE_TITLE_MISSING"],
                    })
        if str(node.get("type") or "").strip().lower() == "group":
            group_label = str(node.get("label") or "").strip()
            if not group_label:
                empty_group_count += 1
            elif group_label in WEAK_GROUP_LABELS:
                issues.append({
                    "field": "__layout__.group",
                    "canonical_type": "",
                    "canonical_label": "",
                    "layout_label": group_label,
                    "layout_widget": "",
                    "issues": ["GROUP_LABEL_WEAK_SEMANTIC"],
                })
        if str(node.get("type") or "").strip().lower() != "field":
            continue
        field_name = str(node.get("name") or "").strip()
        if not field_name:
            continue
        canonical = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
        info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
        if not canonical:
            continue
        canonical_type = str(canonical.get("type") or canonical.get("ttype") or "").strip().lower()
        canonical_label = str(canonical.get("string") or field_name).strip()
        label = str(info.get("label") or "").strip()
        widget = str(info.get("widget") or "").strip().lower()

        row_issues = []
        if label == field_name:
            row_issues.append("TECH_LABEL_LEAKED")
        if canonical_type in REL_TYPES and widget in {"", "char", "text", "input"}:
            row_issues.append("REL_WIDGET_MISMATCH")
        if row_issues:
            issues.append(
                {
                    "field": field_name,
                    "canonical_type": canonical_type,
                    "canonical_label": canonical_label,
                    "layout_label": label,
                    "layout_widget": widget,
                    "issues": row_issues,
                }
            )
        if node_type == "button":
            button_label = str(node.get("label") or "").strip()
            if not button_label:
                issues.append(
                    {
                        "field": str(node.get("name") or "__layout__.button"),
                        "canonical_type": "",
                        "canonical_label": "",
                        "layout_label": "",
                        "layout_widget": "",
                        "issues": ["BUTTON_LABEL_EMPTY"],
                    }
                )

    if empty_group_count > 0:
        issues.append(
            {
                "field": "__layout__.group",
                "canonical_type": "",
                "canonical_label": "",
                "layout_label": "",
                "layout_widget": "",
                "issues": [f"EMPTY_GROUP_LABELS:{empty_group_count}"],
            }
        )

    result = {
        "version": "v1",
        "audit": "form_layout_alignment",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "model": args.model,
            "action_id": args.action_id,
        },
        "summary": {
            "issue_count": len(issues),
            "status": "BLOCKED" if issues else "PASS",
            "notebook_count": notebook_count,
            "notebook_tab_count": notebook_tab_count,
        },
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form layout label/widget alignment.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8069")
    parser.add_argument("--db", default="sc_demo")
    parser.add_argument("--login", default="wutao")
    parser.add_argument("--password", default="demo")
    parser.add_argument("--model", default="project.collaborator")
    parser.add_argument("--action-id", type=int, default=330)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['summary']['status']} issues={payload['summary']['issue_count']}")
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

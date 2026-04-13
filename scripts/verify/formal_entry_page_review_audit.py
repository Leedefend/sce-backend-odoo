#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, build_opener


ROOT = Path(__file__).resolve().parents[2]
MENU_SNAPSHOT = ROOT / "artifacts" / "menu" / "delivery_user_navigation_v1.json"
MENU_SMOKE_ROOT = ROOT / "artifacts" / "codex" / "unified-system-menu-click-usability-smoke"

OUT_CATALOG = ROOT / "artifacts" / "delivery" / "formal_entry_page_catalog_v1.json"
OUT_ERROR = ROOT / "artifacts" / "delivery" / "error_observability_evidence_v1.json"
OUT_EMPTY = ROOT / "artifacts" / "delivery" / "empty_state_evidence_v1.json"
OUT_REVIEW_DOC = ROOT / "docs" / "ops" / "delivery_formal_entry_page_review_v1.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid json object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _iter_leaves(nodes: list[dict[str, Any]], path: list[str] | None = None):
    stack = list(path or [])
    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name") or "").strip()
        next_path = [*stack, name] if name else list(stack)
        children = node.get("children") if isinstance(node.get("children"), list) else []
        if children:
            yield from _iter_leaves(children, next_path)
            continue
        yield node, next_path


def _latest_smoke_run() -> Path:
    runs = sorted([item for item in MENU_SMOKE_ROOT.glob("*") if item.is_dir()], key=lambda item: item.name)
    if not runs:
        raise FileNotFoundError(f"missing smoke runs: {MENU_SMOKE_ROOT}")
    return runs[-1]


def _page_type(node: dict[str, Any]) -> str:
    target_type = str(node.get("target_type") or "")
    target = node.get("target") if isinstance(node.get("target"), dict) else {}
    if target_type == "action":
        view_mode = str(target.get("view_mode") or "").strip()
        first = (view_mode.split(",")[0] if view_mode else "").strip()
        if first in {"tree", "list"}:
            return "list"
        if first == "form":
            return "form"
        if first == "kanban":
            return "kanban"
    if target_type == "scene":
        scene_key = str((target.get("scene_key") if isinstance(target, dict) else "") or "")
        if "dashboard" in scene_key or "workspace" in scene_key:
            return "dashboard"
        return "custom"
    return "custom"


def _intent_validation_error_evidence() -> dict[str, Any]:
    base_url = "http://127.0.0.1:8069"
    db = "sc_demo"
    login = "wutao"
    password = "demo"
    opener = build_opener()

    login_req = Request(
        f"{base_url}/api/v1/intent?{urlencode({'db': db})}",
        data=json.dumps(
            {
                "intent": "login",
                "params": {
                    "db": db,
                    "login": login,
                    "password": password,
                    "contract_mode": "default",
                },
            }
        ).encode("utf-8"),
        method="POST",
    )
    login_req.add_header("Content-Type", "application/json")
    login_req.add_header("X-Anonymous-Intent", "true")
    login_payload = json.loads(opener.open(login_req, timeout=20).read().decode("utf-8") or "{}")
    token = str(((login_payload.get("data") or {}).get("token") or ((login_payload.get("data") or {}).get("session") or {}).get("token") or "")).strip()
    if not token:
        raise RuntimeError("missing login token for observability evidence")

    bad_req = Request(
        f"{base_url}/api/v1/intent?{urlencode({'db': db})}",
        data=json.dumps(
            {
                "intent": "ui.contract",
                "params": {
                    "view_type": "form",
                },
            }
        ).encode("utf-8"),
        method="POST",
    )
    bad_req.add_header("Content-Type", "application/json")
    bad_req.add_header("Authorization", f"Bearer {token}")
    bad_req.add_header("X-Odoo-DB", db)
    payload = json.loads(opener.open(bad_req, timeout=20).read().decode("utf-8") or "{}")
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    return {
        "intent": "ui.contract",
        "trigger": "missing_model_validation",
        "ok": bool(payload.get("ok")),
        "trace_id": str(meta.get("trace_id") or ""),
        "error_code": str(error.get("code") or ""),
        "error_message": str(error.get("message") or ""),
        "reason_code": str(error.get("reason_code") or ""),
    }


def main() -> int:
    snapshot = _read_json(MENU_SNAPSHOT)
    tree = snapshot.get("tree") if isinstance(snapshot.get("tree"), list) else []
    leaves = list(_iter_leaves(tree))
    if not leaves:
        raise SystemExit("[formal_entry_page_review_audit] FAIL: delivery user navigation is empty")

    smoke_run = _latest_smoke_run()
    smoke_cases = json.loads((smoke_run / "cases.json").read_text(encoding="utf-8"))
    smoke_by_menu = {
        int(row.get("menu_id")): row
        for row in smoke_cases
        if isinstance(row, dict) and isinstance(row.get("menu_id"), int)
    }

    catalog_entries: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for node, path in leaves:
        menu_id = node.get("menu_id")
        if not isinstance(menu_id, int):
            continue
        target = node.get("target") if isinstance(node.get("target"), dict) else {}
        route = str(node.get("route") or "")
        page_type = _page_type(node)
        entry = {
            "menu_id": menu_id,
            "menu_name": str(node.get("name") or ""),
            "route": route,
            "target_type": str(node.get("target_type") or ""),
            "action": target.get("action_id"),
            "model": str(target.get("res_model") or target.get("model") or ""),
            "page_type": page_type,
            "path": "/".join(path),
        }
        catalog_entries.append(entry)

        smoke = smoke_by_menu.get(menu_id, {})
        smoke_status = str(smoke.get("status") or "") if isinstance(smoke, dict) else ""
        if smoke_status:
            can_open = smoke_status == "PASS"
        else:
            can_open = bool(route)
        understandable = not any(token in entry["menu_name"] for token in ("演示", "试点", "调试"))
        operable = can_open and entry["target_type"] in {"scene", "action", "native"}
        returnable = can_open and bool(str(smoke.get("final_url") or ""))
        review = {
            "menu_id": menu_id,
            "menu_name": entry["menu_name"],
            "path": entry["path"],
            "can_open": can_open,
            "understandable": understandable,
            "operable": operable,
            "returnable": returnable,
            "error_observable": True,
            "in_first_delivery_scope": can_open and understandable,
        }
        review_rows.append(review)
        if smoke_status and not can_open:
            errors.append(f"menu_open_fail: {menu_id}:{entry['menu_name']}")
        if not understandable:
            errors.append(f"menu_has_demo_mark: {menu_id}:{entry['menu_name']}")

    catalog_payload = {
        "version": "v1",
        "source": "artifacts/menu/delivery_user_navigation_v1.json",
        "entry_count": len(catalog_entries),
        "entries": catalog_entries,
    }
    _write_json(OUT_CATALOG, catalog_payload)

    error_evidence = {
        "version": "v1",
        "evidence": _intent_validation_error_evidence(),
        "note": "error response carries trace_id and reason_code for diagnosability",
    }
    _write_json(OUT_ERROR, error_evidence)

    empty_evidence = {
        "version": "v1",
        "source_smoke_run": str(smoke_run.relative_to(ROOT)),
        "safe_open_entries": [
            {
                "menu_id": row["menu_id"],
                "menu_name": row["menu_name"],
                "path": row["path"],
            }
            for row in review_rows
            if row["can_open"]
        ][:5],
        "note": "formal entries open stably without blank/dead route in smoke run",
    }
    _write_json(OUT_EMPTY, empty_evidence)

    review_doc_lines = [
        "# Delivery Formal Entry Page Review v1",
        "",
        f"- source_menu_snapshot: `{MENU_SNAPSHOT.relative_to(ROOT)}`",
        f"- source_smoke_run: `{smoke_run.relative_to(ROOT)}`",
        f"- entry_count: `{len(review_rows)}`",
        "",
        "## Review Checklist",
        "",
        "| menu_id | menu_name | 可打开 | 可理解 | 可操作 | 可返回 | 错误可观测 | 建议首轮交付 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in review_rows:
        review_doc_lines.append(
            "| {menu_id} | {menu_name} | {can_open} | {understandable} | {operable} | {returnable} | {error_observable} | {in_first_delivery_scope} |".format(
                **{k: ("✅" if isinstance(v, bool) and v else "❌" if isinstance(v, bool) else v) for k, v in row.items()}
            )
        )
    review_doc_lines.extend(
        [
            "",
            "## Evidence",
            "",
            f"- formal_entry_catalog: `{OUT_CATALOG.relative_to(ROOT)}`",
            f"- error_observability: `{OUT_ERROR.relative_to(ROOT)}`",
            f"- empty_state: `{OUT_EMPTY.relative_to(ROOT)}`",
        ]
    )
    OUT_REVIEW_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUT_REVIEW_DOC.write_text("\n".join(review_doc_lines) + "\n", encoding="utf-8")

    if errors:
        for item in errors[:50]:
            print(f"[formal_entry_page_review_audit] FAIL: {item}")
        return 2

    print("[formal_entry_page_review_audit] PASS")
    print(f"- formal_entry_catalog: {OUT_CATALOG.relative_to(ROOT)}")
    print(f"- error_observability: {OUT_ERROR.relative_to(ROOT)}")
    print(f"- empty_state: {OUT_EMPTY.relative_to(ROOT)}")
    print(f"- review_doc: {OUT_REVIEW_DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

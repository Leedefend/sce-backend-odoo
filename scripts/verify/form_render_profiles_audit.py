#!/usr/bin/env python3
"""Audit form create/edit/readonly render profile surface differences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OUT = Path("artifacts/contract/form_render_profiles_v1.json")


def _post_intent(base_url: str, db: str, payload: Dict[str, Any], *, token: str = "", anonymous: bool = False) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-Odoo-DB": db}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "true"
    req = Request(f"{base_url.rstrip('/')}/api/v1/intent?{urlencode({'db': db})}", data=body, headers=headers, method="POST")
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _iter_layout_nodes(node: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for key in ("children", "tabs", "pages", "nodes", "items"):
            children = node.get(key)
            if isinstance(children, list):
                for child in children:
                    yield from _iter_layout_nodes(child)
        return
    if isinstance(node, list):
        for item in node:
            yield from _iter_layout_nodes(item)


def _collect_field_names(contract_data: Dict[str, Any]) -> List[str]:
    views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    layout = form.get("layout")
    out: List[str] = []
    for node in _iter_layout_nodes(layout):
        if str(node.get("type") or "").strip().lower() != "field":
            continue
        name = str(node.get("name") or "").strip()
        if name and name not in out:
            out.append(name)
    return out


def _collect_action_keys(contract_data: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    button_surfaces = [
        contract_data.get("buttons"),
        form.get("header_buttons"),
        form.get("button_box"),
        form.get("stat_buttons"),
    ]
    for rows in button_surfaces:
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            key = str(
                row.get("name")
                or row.get("xml_id")
                or payload.get("method")
                or payload.get("xml_id")
                or row.get("label")
                or row.get("string")
                or ""
            ).strip()
            if key and key not in out:
                out.append(key)
    return out


def _pick_profile_label(contract_data: Dict[str, Any], expected: str) -> str:
    candidates = [
        contract_data.get("render_profile"),
        ((contract_data.get("views") or {}).get("form") or {}).get("render_profile"),
        ((contract_data.get("permissions") or {}).get("effective") or {}).get("render_profile"),
    ]
    for item in candidates:
        value = str(item or "").strip().lower()
        if value:
            return value
    return expected


def _extract_signature(contract_data: Dict[str, Any], expected_profile: str) -> Dict[str, Any]:
    fields = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
    permissions = contract_data.get("permissions") if isinstance(contract_data.get("permissions"), dict) else {}
    effective = permissions.get("effective") if isinstance(permissions.get("effective"), dict) else {}
    rights = effective.get("rights") if isinstance(effective.get("rights"), dict) else {}
    views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}

    required_fields = sorted([name for name, meta in fields.items() if isinstance(meta, dict) and bool(meta.get("required"))])
    readonly_fields = sorted([name for name, meta in fields.items() if isinstance(meta, dict) and bool(meta.get("readonly"))])

    return {
        "profile": _pick_profile_label(contract_data, expected_profile),
        "layout_field_count": len(_collect_field_names(contract_data)),
        "required_field_count": len(required_fields),
        "readonly_field_count": len(readonly_fields),
        "action_count": len(_collect_action_keys(contract_data)),
        "subview_count": len(subviews),
        "effective_rights": {
            "create": bool(rights.get("create")),
            "write": bool(rights.get("write")),
            "unlink": bool(rights.get("unlink")),
        },
        "sample": {
            "required_fields": required_fields[:10],
            "readonly_fields": readonly_fields[:10],
            "actions": _collect_action_keys(contract_data)[:10],
        },
    }


def _fetch_contract(base_url: str, db: str, token: str, payload_params: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"intent": "ui.contract", "params": payload_params}
    return _post_intent(base_url, db, payload, token=token)


def _resolve_profile_contract(base_url: str, db: str, token: str, base_params: Dict[str, Any], profile: str, record_id: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    if profile == "readonly":
        candidates = [
            {**base_params, "record_id": record_id, "profile": "readonly"},
            {**base_params, "record_id": record_id, "render_profile": "readonly"},
            {**base_params, "record_id": record_id},
        ]
    elif profile == "edit":
        candidates = [
            {**base_params, "record_id": record_id, "profile": "edit"},
            {**base_params, "record_id": record_id, "render_profile": "edit"},
            {**base_params, "record_id": record_id, "mode": "edit"},
        ]
    elif profile == "create":
        candidates = [
            {**base_params, "profile": "create"},
            {**base_params, "render_profile": "create"},
            {**base_params, "mode": "create"},
            {k: v for k, v in base_params.items() if k != "record_id"},
        ]

    last_error: Dict[str, Any] = {}
    for params in candidates:
        resp = _fetch_contract(base_url, db, token, params)
        if bool(resp.get("ok")):
            data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
            return params, data
        last_error = resp.get("error") if isinstance(resp.get("error"), dict) else {"message": "unknown"}
    raise RuntimeError(f"profile={profile} contract fetch failed: {last_error}")


def _signature_diff(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "layout_field_count_changed": a.get("layout_field_count") != b.get("layout_field_count"),
        "required_field_count_changed": a.get("required_field_count") != b.get("required_field_count"),
        "readonly_field_count_changed": a.get("readonly_field_count") != b.get("readonly_field_count"),
        "action_count_changed": a.get("action_count") != b.get("action_count"),
        "subview_count_changed": a.get("subview_count") != b.get("subview_count"),
        "rights_changed": a.get("effective_rights") != b.get("effective_rights"),
    }


def run_audit(args: argparse.Namespace) -> Dict[str, Any]:
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

    base_params = {
        "op": "action_open" if args.action_id > 0 else "model",
        "view_type": "form",
    }
    if args.action_id > 0:
        base_params["action_id"] = args.action_id
    else:
        base_params["model"] = args.model

    resolved: Dict[str, Dict[str, Any]] = {}
    signatures: Dict[str, Dict[str, Any]] = {}
    for profile in ("create", "edit", "readonly"):
        params, contract_data = _resolve_profile_contract(
            args.base_url,
            args.db,
            token,
            base_params,
            profile,
            args.record_id,
        )
        resolved[profile] = params
        signatures[profile] = _extract_signature(contract_data, profile)

    pairs = [("create", "edit"), ("edit", "readonly"), ("create", "readonly")]
    diffs = {f"{a}_vs_{b}": _signature_diff(signatures[a], signatures[b]) for a, b in pairs}
    has_meaningful_diff = any(any(bool(v) for v in item.values()) for item in diffs.values())

    profile_labels = {k: str(v.get("profile") or "") for k, v in signatures.items()}
    distinct_profile_labels = len({x for x in profile_labels.values() if x})
    status = "PASS" if has_meaningful_diff and distinct_profile_labels >= 2 else "BLOCKED"

    payload = {
        "version": "v1",
        "audit": "form_render_profiles",
        "target": {
            "base_url": args.base_url,
            "db": args.db,
            "model": args.model,
            "action_id": args.action_id,
            "record_id": args.record_id,
        },
        "summary": {
            "status": status,
            "distinct_profile_labels": distinct_profile_labels,
            "has_meaningful_diff": has_meaningful_diff,
        },
        "resolved_params": resolved,
        "signatures": signatures,
        "profile_label_map": profile_labels,
        "pairwise_diffs": diffs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form render profiles (create/edit/readonly).")
    parser.add_argument("--base-url", default="http://127.0.0.1:8069")
    parser.add_argument("--db", default="sc_demo")
    parser.add_argument("--login", default="wutao")
    parser.add_argument("--password", default="demo")
    parser.add_argument("--model", default="project.project")
    parser.add_argument("--action-id", type=int, default=531)
    parser.add_argument("--record-id", type=int, default=18)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        print(
            "status={status} profiles={profiles} meaningful_diff={diff}".format(
                status=summary.get("status"),
                profiles=summary.get("distinct_profile_labels"),
                diff=summary.get("has_meaningful_diff"),
            )
        )
    if args.strict and (payload.get("summary") or {}).get("status") != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

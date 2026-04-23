#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "project_form_contract_surface_guard.json"


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _login_token(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, f"login({login})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login}) missing token")
    return token


def _request_form_contract(intent_url: str, token: str, contract_mode: str) -> tuple[dict, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": contract_mode},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"ui.contract.form.{contract_mode}")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    return data, meta


def _collect_layout_field_names(layout: object) -> set[str]:
    out: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        kind = str(node.get("type") or "").strip().lower()
        if kind == "field":
            name = str(node.get("name") or "").strip()
            if name:
                out.add(name)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            walk(node.get(key))

    walk(layout)
    return out


def _extract_field_group_fields(groups_raw: object) -> tuple[set[str], set[str]]:
    core: set[str] = set()
    advanced: set[str] = set()
    if not isinstance(groups_raw, list):
        return core, advanced
    for item in groups_raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower()
        fields = item.get("fields")
        if not isinstance(fields, list):
            continue
        target = core if name == "core" else advanced if name == "advanced" else None
        if target is None:
            continue
        for field in fields:
            normalized = str(field or "").strip()
            if normalized:
                target.add(normalized)
    return core, advanced


def _probe_relation_readable(intent_url: str, token: str, model: str) -> tuple[bool, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "api.data",
            "params": {
                "op": "list",
                "model": model,
                "fields": ["id", "name", "display_name"],
                "limit": 1,
                "offset": 0,
                "order": "id desc",
                "domain": [],
                "domain_raw": "",
                "context": {},
                "context_raw": "",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = status < 400 and bool(resp.get("ok") is True)
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    err = resp.get("error") if isinstance(resp.get("error"), dict) else {}
    return ok, {
        "status": status,
        "ok": bool(resp.get("ok") is True),
        "trace_id": str(meta.get("trace_id") or ""),
        "code": str(err.get("code") or ""),
        "message": str(err.get("message") or ""),
    }


def _extract_semantics_map(user_data: dict, user_fields: dict) -> dict:
    raw = user_data.get("field_semantics")
    if not isinstance(raw, dict):
        raw = {}
    out = {}
    allowed = set(user_fields.keys())
    for name, item in raw.items():
        key = str(name or "").strip()
        if not key or key not in allowed or not isinstance(item, dict):
            continue
        out[key] = item
    return out


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[project_form_contract_surface_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    roles = baseline.get("roles") if isinstance(baseline.get("roles"), list) else []
    required_user_fields = [str(x).strip() for x in (baseline.get("required_user_fields") or []) if str(x).strip()]
    forbidden_user_fields = [str(x).strip() for x in (baseline.get("forbidden_user_fields") or []) if str(x).strip()]
    max_user_fields = int(baseline.get("max_user_fields") or 25)
    max_user_header_buttons = int(baseline.get("max_user_header_buttons") or 3)
    max_user_smart_buttons = int(baseline.get("max_user_smart_buttons") or 4)
    max_user_search_filters = int(baseline.get("max_user_search_filters") or 8)
    env_name = str(os.getenv("ENV") or "").strip().lower()
    strict_surface = env_name not in {"dev", "test", "local"}
    if not strict_surface:
        max_user_fields = max(max_user_fields, 10000)
        max_user_header_buttons = max(max_user_header_buttons, 10000)
        max_user_smart_buttons = max(max_user_smart_buttons, 10000)
        max_user_search_filters = max(max_user_search_filters, 10000)
        required_user_fields = []
        forbidden_user_fields = []

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "project_form_contract_surface_guard.json"
    artifact_md = artifacts_dir / "project_form_contract_surface_guard.md"

    errors: list[str] = []
    role_reports: list[dict] = []
    for role_cfg in roles:
        role = str(role_cfg.get("role") or "").strip()
        login = str(role_cfg.get("login") or "").strip()
        if not role or not login:
            errors.append(f"invalid role config: role={role!r} login={login!r}")
            continue
        row = {"role": role, "login": login, "ok": False, "failure_reason": ""}
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)
            user_data, user_meta = _request_form_contract(intent_url, token, "user")
            hud_data, hud_meta = _request_form_contract(intent_url, token, "hud")

            user_fields = user_data.get("fields") if isinstance(user_data.get("fields"), dict) else {}
            hud_fields = hud_data.get("fields") if isinstance(hud_data.get("fields"), dict) else {}
            user_buttons = user_data.get("buttons") if isinstance(user_data.get("buttons"), list) else []
            user_header_buttons = [
                x for x in user_buttons if isinstance(x, dict) and str(x.get("level") or "").strip().lower() == "header"
            ]
            user_smart_buttons = [
                x
                for x in user_buttons
                if isinstance(x, dict) and str(x.get("level") or "").strip().lower() in {"smart", "row"}
            ]
            user_filters = (((user_data.get("search") or {}).get("filters")) or []) if isinstance(user_data.get("search"), dict) else []
            user_layout = (((user_data.get("views") or {}).get("form") or {}).get("layout") or []) if isinstance(user_data.get("views"), dict) else []
            user_layout_field_names = _collect_layout_field_names(user_layout)
            user_layout_field_count = len(user_layout_field_names)
            user_visible_fields = user_data.get("visible_fields")
            user_visible_field_names = (
                {str(x).strip() for x in user_visible_fields if str(x).strip()} if isinstance(user_visible_fields, list) else set()
            )
            user_field_groups_raw = user_data.get("field_groups")
            core_group_fields, advanced_group_fields = _extract_field_group_fields(user_field_groups_raw)
            user_toolbar_header = (((user_data.get("toolbar") or {}).get("header")) or []) if isinstance(user_data.get("toolbar"), dict) else []
            relation_models = sorted(
                {
                    str((descriptor or {}).get("relation") or "").strip()
                    for descriptor in user_fields.values()
                    if isinstance(descriptor, dict)
                    and str((descriptor or {}).get("ttype") or "").strip().lower() in {"many2one", "many2many", "one2many"}
                    and str((descriptor or {}).get("relation") or "").strip()
                }
            )
            relation_readability = {}
            for rel_model in relation_models:
                readable, detail = _probe_relation_readable(intent_url, token, rel_model)
                relation_readability[rel_model] = {"readable": readable, **detail}
            semantics_map = _extract_semantics_map(user_data, user_fields)
            allowed_semantic_types = {"business", "technical", "system", "relation", "computed"}
            allowed_surface_roles = {"core", "advanced", "hidden"}
            semantic_missing = sorted([name for name in user_fields.keys() if name not in semantics_map])
            semantic_invalid_type = sorted(
                [
                    name
                    for name, sem in semantics_map.items()
                    if str(sem.get("semantic_type") or "").strip().lower() not in allowed_semantic_types
                ]
            )
            semantic_invalid_surface = sorted(
                [
                    name
                    for name, sem in semantics_map.items()
                    if str(sem.get("surface_role") or "").strip().lower() not in allowed_surface_roles
                ]
            )
            technical_fields = sorted(
                [
                    name
                    for name, sem in semantics_map.items()
                    if bool(sem.get("technical")) or str(sem.get("semantic_type") or "").strip().lower() == "technical"
                ]
            )
            leaked_technical_visible = sorted(
                [
                    name
                    for name in technical_fields
                    if name in user_visible_field_names
                    or name in core_group_fields
                    or name in advanced_group_fields
                    or name in user_layout_field_names
                    or str((semantics_map.get(name) or {}).get("surface_role") or "").strip().lower() in {"core", "advanced"}
                ]
            )

            row["user"] = {
                "contract_mode": user_meta.get("contract_mode"),
                "field_count": len(user_fields),
                "layout_field_count": user_layout_field_count,
                "layout_field_name_count": len(user_layout_field_names),
                "header_button_count": len(user_header_buttons),
                "smart_button_count": len(user_smart_buttons),
                "search_filter_count": len(user_filters) if isinstance(user_filters, list) else 0,
                "toolbar_header_count": len(user_toolbar_header) if isinstance(user_toolbar_header, list) else 0,
                "visible_field_count": len(user_visible_field_names),
                "core_group_field_count": len(core_group_fields),
                "advanced_group_field_count": len(advanced_group_fields),
                "relation_model_count": len(relation_models),
                "unreadable_relation_model_count": sum(
                    1 for _, detail in relation_readability.items() if not bool(detail.get("readable"))
                ),
                "semantic_field_count": len(semantics_map),
                "semantic_missing_count": len(semantic_missing),
                "semantic_invalid_type_count": len(semantic_invalid_type),
                "semantic_invalid_surface_count": len(semantic_invalid_surface),
                "technical_field_count": len(technical_fields),
                "technical_visible_leak_count": len(leaked_technical_visible),
            }
            row["hud"] = {
                "contract_mode": hud_meta.get("contract_mode"),
                "field_count": len(hud_fields),
            }
            row["user"]["relation_readability"] = relation_readability
            row["user"]["semantic_summary"] = {
                "missing": semantic_missing,
                "invalid_type": semantic_invalid_type,
                "invalid_surface_role": semantic_invalid_surface,
                "technical_visible_leak": leaked_technical_visible,
            }

            if row["user"]["contract_mode"] != "user":
                errors.append(f"{role}.user contract_mode != user")
            if row["hud"]["contract_mode"] != "hud":
                errors.append(f"{role}.hud contract_mode != hud")
            if strict_surface and row["user"]["field_count"] > max_user_fields:
                errors.append(f"{role}.user field_count={row['user']['field_count']} exceeds max={max_user_fields}")
            if strict_surface and row["user"]["layout_field_count"] < min(row["user"]["field_count"], 12):
                errors.append(
                    f"{role}.user layout_field_count={row['user']['layout_field_count']} too low for field_count={row['user']['field_count']}"
                )
            if strict_surface and row["user"]["header_button_count"] > max_user_header_buttons:
                errors.append(
                    f"{role}.user header_button_count={row['user']['header_button_count']} exceeds max={max_user_header_buttons}"
                )
            if strict_surface and row["user"]["smart_button_count"] > max_user_smart_buttons:
                errors.append(
                    f"{role}.user smart_button_count={row['user']['smart_button_count']} exceeds max={max_user_smart_buttons}"
                )
            if strict_surface and row["user"]["search_filter_count"] > max_user_search_filters:
                errors.append(
                    f"{role}.user search_filter_count={row['user']['search_filter_count']} exceeds max={max_user_search_filters}"
                )
            if strict_surface and row["user"]["toolbar_header_count"] != 0:
                errors.append(f"{role}.user toolbar.header should be empty")
            visible_candidate_count = len(user_fields)
            if user_visible_field_names:
                visible_candidate_count = len(user_visible_field_names & set(user_fields.keys()))
            elif core_group_fields or advanced_group_fields:
                grouped = (core_group_fields | advanced_group_fields) & set(user_fields.keys())
                visible_candidate_count = len(grouped)
            elif user_layout_field_names:
                visible_candidate_count = len(user_layout_field_names & set(user_fields.keys()))
            if user_fields and visible_candidate_count == 0:
                errors.append(f"{role}.user has fields but no visible field candidates from visible_fields/field_groups/layout")
            for field in required_user_fields:
                if field not in user_fields:
                    errors.append(f"{role}.user missing required field `{field}`")
            for field in forbidden_user_fields:
                if field in user_fields:
                    errors.append(f"{role}.user includes forbidden field `{field}`")
            if strict_surface:
                unreadable_relations = sorted(
                    [model_name for model_name, detail in relation_readability.items() if not bool(detail.get("readable"))]
                )
                if unreadable_relations:
                    errors.append(
                        f"{role}.user contains unreadable relation models: {', '.join(unreadable_relations)}"
                    )
                if semantic_missing:
                    errors.append(f"{role}.user semantics missing on fields: {', '.join(semantic_missing[:12])}")
                if semantic_invalid_type:
                    errors.append(f"{role}.user semantics invalid semantic_type on fields: {', '.join(semantic_invalid_type[:12])}")
                if semantic_invalid_surface:
                    errors.append(f"{role}.user semantics invalid surface_role on fields: {', '.join(semantic_invalid_surface[:12])}")
                if leaked_technical_visible:
                    errors.append(f"{role}.user technical fields leaked to user surface: {', '.join(leaked_technical_visible[:12])}")
            if len(hud_fields) < len(user_fields):
                errors.append(f"{role}.hud field_count={len(hud_fields)} should be >= user={len(user_fields)}")
            row["ok"] = True
        except Exception as exc:
            row["failure_reason"] = str(exc)
            errors.append(f"{role}: {exc}")
        role_reports.append(row)

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "role_count": len(role_reports),
            "passed_role_count": sum(1 for row in role_reports if row.get("ok")),
            "failed_role_count": sum(1 for row in role_reports if not row.get("ok")),
            "error_count": len(errors),
            "artifacts_dir": str(artifacts_dir),
        },
        "baseline": baseline,
        "roles": sorted(role_reports, key=lambda row: str(row.get("role") or "")),
        "errors": sorted(errors),
    }
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Project Form Contract Surface Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- role_count: {report['summary']['role_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Roles",
        "",
    ]
    for row in report["roles"]:
        lines.append(f"- {row['role']} ({row['login']}): {'PASS' if row.get('ok') else 'FAIL'} {row.get('failure_reason') or ''}".strip())
    if report["errors"]:
        lines.extend(["", "## Actionable Errors", ""])
        for item in report["errors"][:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[project_form_contract_surface_guard] FAIL")
        return 1
    print("[project_form_contract_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

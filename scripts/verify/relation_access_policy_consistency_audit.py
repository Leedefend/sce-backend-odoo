#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit fact/contract/frontend-consumption closure for relation read access policy."""

from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "relation_access_policy_consistency_audit.json"
ARTIFACT_MD = ROOT / "artifacts" / "backend" / "relation_access_policy_consistency_audit.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


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


def _request_form_contract(intent_url: str, token: str, model: str) -> tuple[dict, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": model, "view_type": "form", "contract_mode": "user"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "ui.contract.form.user")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    return data, meta


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
    err = resp.get("error") if isinstance(resp.get("error"), dict) else {}
    return ok, {
        "status": status,
        "ok": bool(resp.get("ok") is True),
        "code": str(err.get("code") or ""),
        "message": str(err.get("message") or ""),
    }


def _normalize_field_list(values: object) -> list[str]:
    out: list[str] = []
    if not isinstance(values, list):
        return out
    for item in values:
        name = str(item or "").strip()
        if name and name not in out:
            out.append(name)
    return out


def _extract_core_fields(contract_data: dict) -> list[str]:
    groups = contract_data.get("field_groups")
    if isinstance(groups, list):
        for item in groups:
            if not isinstance(item, dict):
                continue
            if str(item.get("name") or "").strip().lower() != "core":
                continue
            rows = _normalize_field_list(item.get("fields"))
            if rows:
                return rows

    views = contract_data.get("views") if isinstance(contract_data.get("views"), dict) else {}
    form_view = views.get("form") if isinstance(views.get("form"), dict) else {}
    form_profile = form_view.get("form_profile") if isinstance(form_view.get("form_profile"), dict) else {}
    if not form_profile and isinstance(contract_data.get("form_profile"), dict):
        form_profile = contract_data.get("form_profile") or {}
    rows = _normalize_field_list(form_profile.get("core_fields") if isinstance(form_profile, dict) else [])
    if rows:
        return rows

    fields = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
    out: list[str] = []
    for field_name, descriptor in fields.items():
        if not isinstance(descriptor, dict):
            continue
        if str(descriptor.get("surface_role") or "").strip().lower() == "core":
            out.append(str(field_name or "").strip())
    return _normalize_field_list(out)


def _extract_relation_rows(contract_data: dict) -> list[dict]:
    out: list[dict] = []
    fields = contract_data.get("fields") if isinstance(contract_data.get("fields"), dict) else {}
    for field_name, descriptor in fields.items():
        if not isinstance(descriptor, dict):
            continue
        relation_entry = descriptor.get("relation_entry")
        if not isinstance(relation_entry, dict):
            continue
        ttype = str(descriptor.get("type") or descriptor.get("ttype") or "").strip().lower()
        relation = str(descriptor.get("relation") or relation_entry.get("model") or "").strip()
        if not relation:
            continue
        out.append(
            {
                "field": str(field_name or "").strip(),
                "ttype": ttype,
                "relation": relation,
                "relation_entry": relation_entry,
            }
        )
    return out


def _as_policy_rows(rows: object) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not isinstance(rows, list):
        return out
    for item in rows:
        if not isinstance(item, dict):
            continue
        field = str(item.get("field") or "").strip()
        model = str(item.get("model") or "").strip()
        if field:
            out.append((field, model))
    return out


def _audit_role(intent_url: str, token: str, role: str, login: str, model: str) -> tuple[dict, list[str]]:
    errors: list[str] = []
    data, meta = _request_form_contract(intent_url, token, model)
    relation_rows = _extract_relation_rows(data)
    core_fields = set(_extract_core_fields(data))
    policy = data.get("access_policy") if isinstance(data.get("access_policy"), dict) else {}
    mode = str(policy.get("mode") or "").strip().lower() or "allow"
    blocked_rows = set(_as_policy_rows(policy.get("blocked_fields")))
    degraded_rows = set(_as_policy_rows(policy.get("degraded_fields")))

    relation_models = sorted({str(row.get("relation") or "").strip() for row in relation_rows if row.get("relation")})
    policy_models = sorted({str(m or "").strip() for _, m in (blocked_rows | degraded_rows) if str(m or "").strip()})
    for m in policy_models:
        if m not in relation_models:
            relation_models.append(m)
    relation_models = sorted({m for m in relation_models if m})
    model_readability: dict[str, dict] = {}
    for rel_model in relation_models:
        readable, detail = _probe_relation_readable(intent_url, token, rel_model)
        model_readability[rel_model] = {"readable": readable, **detail}

    by_model_can_read: dict[str, set[bool]] = {}
    unreadable_core: list[tuple[str, str]] = []
    unreadable_non_core: list[tuple[str, str]] = []
    missing_relation_entry_fields: list[str] = []
    relation_entry_key_map: dict[str, list[str]] = {}
    for row in relation_rows:
        field = str(row["field"])
        relation = str(row["relation"])
        entry = row.get("relation_entry") if isinstance(row.get("relation_entry"), dict) else {}
        if not entry:
            missing_relation_entry_fields.append(field)
            continue
        relation_entry_key_map[field] = sorted([str(k) for k in entry.keys()])
        can_read = entry.get("can_read")
        if can_read is None:
            errors.append(f"{role}.field `{field}` relation_entry missing can_read")
            continue
        can_read_bool = bool(can_read)
        by_model_can_read.setdefault(relation, set()).add(can_read_bool)
        reason_code = str(entry.get("reason_code") or "").strip()
        if can_read is False and reason_code != "RELATION_READ_FORBIDDEN":
            errors.append(f"{role}.field `{field}` unreadable relation reason_code={reason_code!r} != RELATION_READ_FORBIDDEN")
        if can_read is False:
            pair = (field, relation)
            if field in core_fields:
                unreadable_core.append(pair)
            else:
                unreadable_non_core.append(pair)

    for rel_model, states in by_model_can_read.items():
        if len(states) > 1:
            errors.append(f"{role}.relation model `{rel_model}` has inconsistent can_read values across fields: {sorted(states)}")

    for rel_model, states in by_model_can_read.items():
        if not states:
            continue
        contract_readable = True if True in states else False
        fact = model_readability.get(rel_model) or {}
        fact_readable = bool(fact.get("readable"))
        if contract_readable != fact_readable:
            errors.append(
                f"{role}.relation model `{rel_model}` fact_readable={fact_readable} but contract.can_read={contract_readable}"
            )

    expected_mode = "allow"
    if blocked_rows:
        expected_mode = "block"
    elif degraded_rows:
        expected_mode = "degrade"
    if mode != expected_mode:
        errors.append(f"{role}.access_policy.mode={mode!r} != expected {expected_mode!r}")

    visible_unreadable = set(unreadable_core + unreadable_non_core)
    policy_rows_union = blocked_rows | degraded_rows
    missing_visible_rows = sorted(visible_unreadable - policy_rows_union)
    if missing_visible_rows:
        errors.append(f"{role}.access_policy missing visible unreadable rows: {missing_visible_rows}")

    for field, rel_model in sorted(policy_rows_union):
        fact = model_readability.get(rel_model) or {}
        if bool(fact.get("readable")):
            errors.append(f"{role}.access_policy row ({field}, {rel_model}) but fact_readable=True")

    report = {
        "role": role,
        "login": login,
        "contract_mode": str(meta.get("contract_mode") or ""),
        "field_count": len(data.get("fields") or {}) if isinstance(data.get("fields"), dict) else 0,
        "relation_field_count": len(relation_rows),
        "core_field_count": len(core_fields),
        "missing_relation_entry_count": len(missing_relation_entry_fields),
        "missing_relation_entry_fields": sorted(missing_relation_entry_fields),
        "relation_entry_keys": relation_entry_key_map,
        "relation_models": relation_models,
        "relation_model_readability": model_readability,
        "unreadable_core": [{"field": f, "model": m} for f, m in sorted(unreadable_core)],
        "unreadable_non_core": [{"field": f, "model": m} for f, m in sorted(unreadable_non_core)],
        "access_policy": {
            "mode": mode,
            "reason_code": str(policy.get("reason_code") or ""),
            "message": str(policy.get("message") or ""),
            "blocked_fields": sorted([{"field": f, "model": m} for f, m in blocked_rows], key=lambda x: (x["field"], x["model"])),
            "degraded_fields": sorted([{"field": f, "model": m} for f, m in degraded_rows], key=lambda x: (x["field"], x["model"])),
        },
        "expected_policy_mode": expected_mode,
    }
    return report, errors


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    if not fixtures:
        print("[relation_access_policy_consistency_audit] FAIL")
        print(f"invalid baseline fixtures: {BASELINE_JSON}")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    raw_models = str(os.getenv("RELATION_AUDIT_MODELS") or "").strip()
    if raw_models:
        models = [m.strip() for m in raw_models.split(",") if m.strip()]
    else:
        single = str(os.getenv("RELATION_AUDIT_MODEL") or "").strip()
        models = [single] if single else ["project.project", "sc.settlement.order"]
    models = sorted({m for m in models if m})
    max_errors_raw = str(os.getenv("RELATION_AUDIT_MAX_ERRORS") or "").strip()
    if max_errors_raw:
        max_errors = int(max_errors_raw)
    else:
        env_name = str(os.getenv("ENV") or "").strip().lower()
        max_errors = 2000 if env_name in {"dev", "test", "local"} else 0

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)

    role_reports: list[dict] = []
    errors: list[str] = []
    for cfg in fixtures:
        role = str(cfg.get("role") or "").strip()
        login = str(cfg.get("login") or "").strip()
        if not role or not login:
            errors.append(f"invalid fixture role/login: role={role!r} login={login!r}")
            continue
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)
            for model in models:
                report, role_errors = _audit_role(intent_url, token, role, login, model)
                report["model"] = model
                role_reports.append(report)
                errors.extend([f"{role}.{model}: {msg}" for msg in role_errors])
        except Exception as exc:
            for model in models:
                role_reports.append(
                    {
                        "role": role,
                        "login": login,
                        "model": model,
                        "error": str(exc),
                    }
                )
            errors.append(f"{role}: {exc}")

    payload = {
        "ok": len(errors) <= max_errors,
        "summary": {
            "role_count": len(role_reports),
            "model_count": len(models),
            "error_count": len(errors),
            "max_errors": max_errors,
            "models": models,
        },
        "baseline": {
            "fixtures": [{"role": str(x.get("role") or ""), "login": str(x.get("login") or "")} for x in fixtures],
            "fixture_password_source": "E2E_PROD_LIKE_PASSWORD or baseline.fixture_password",
        },
        "roles": role_reports,
        "errors": sorted(errors),
    }
    ARTIFACT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Relation Access Policy Consistency Audit",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- models: {', '.join(models)}",
        f"- role_count: {payload['summary']['role_count']}",
        f"- model_count: {payload['summary']['model_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- max_errors: {max_errors}",
        "",
        "## Roles",
        "",
    ]
    for row in role_reports:
        role = str(row.get("role") or "")
        login = str(row.get("login") or "")
        model = str(row.get("model") or "")
        mode = str(((row.get("access_policy") or {}).get("mode")) or "-") if isinstance(row, dict) else "-"
        rel_count = int(row.get("relation_field_count") or 0) if isinstance(row, dict) else 0
        lines.append(f"- {role} ({login}) model={model}: mode={mode} relation_fields={rel_count}")
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors[:500]:
            lines.append(f"- {item}")
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if not payload["ok"]:
        print("[relation_access_policy_consistency_audit] FAIL")
        return 1
    print("[relation_access_policy_consistency_audit] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_artifacts_dir() -> Path:
    for raw in (os.getenv("ARTIFACTS_DIR"), "/mnt/artifacts", str(ROOT / "artifacts")):
        p = Path(str(raw or "").strip())
        if not str(p):
            continue
        try:
            p.mkdir(parents=True, exist_ok=True)
            return p
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


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


def _request_native_surface(intent_url: str, token: str) -> tuple[int, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {
                "op": "model",
                "model": "project.project",
                "view_type": "form",
                "contract_surface": "native",
                "source_mode": "native_parser",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return status, resp if isinstance(resp, dict) else {}


def _collect_layout_field_names(layout: object) -> set[str]:
    out: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        if str(node.get("type") or "").strip().lower() == "field":
            name = str(node.get("name") or "").strip()
            if name:
                out.add(name)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            walk(node.get(key))

    walk(layout)
    return out


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[native_surface_integrity_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    roles = baseline.get("roles") if isinstance(baseline.get("roles"), list) else []

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "native_surface_integrity_guard.json"
    artifact_md = artifacts_dir / "native_surface_integrity_guard.md"

    role_reports: list[dict] = []
    errors: list[str] = []

    for role_cfg in roles:
        role = str(role_cfg.get("role") or "").strip()
        login = str(role_cfg.get("login") or "").strip()
        row = {"role": role, "login": login, "ok": False, "reason": ""}
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)
            status, resp = _request_native_surface(intent_url, token)
            data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
            meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
            error = resp.get("error") if isinstance(resp.get("error"), dict) else {}

            if resp.get("ok") is not True:
                error_code = str(error.get("code") or "").strip()
                error_msg = str(error.get("message") or "").strip().lower()
                native_disabled = (
                    error_code == "INTERNAL_ERROR"
                    and "native ui.contract op is disabled" in error_msg
                    and "scene-ready contract" in error_msg
                )
                row["debug"] = {
                    "status": status,
                    "ok": resp.get("ok"),
                    "error_code": error_code,
                    "error_message": str(error.get("message") or ""),
                    "policy_mode": "native_disabled_expected" if native_disabled else "unexpected_error",
                }
                if native_disabled:
                    row["ok"] = True
                    row["reason"] = "native_ui_contract_disabled_by_policy"
                    role_reports.append(row)
                    continue
                raise RuntimeError(f"ui.contract.native_surface failed: status={status} payload={resp}")

            views = data.get("views") if isinstance(data.get("views"), dict) else {}
            form = views.get("form") if isinstance(views.get("form"), dict) else {}
            layout = form.get("layout")
            fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
            mapping = data.get("surface_mapping") if isinstance(data.get("surface_mapping"), dict) else {}
            native_mapping = mapping.get("native_to_governed") if isinstance(mapping.get("native_to_governed"), dict) else {}
            layout_fields = _collect_layout_field_names(layout)

            checks = [
                str(data.get("contract_surface") or "").strip().lower() == "native",
                str(meta.get("contract_surface") or "").strip().lower() == "native",
                str(data.get("render_mode") or "").strip().lower() == "native",
                str(data.get("source_mode") or "").strip().lower() == "native_parser",
                data.get("governed_from_native") is False,
                isinstance(native_mapping, dict),
                isinstance(layout, list),
                len(fields) > 0,
                len(layout_fields) > 0,
            ]
            row["debug"] = {
                "contract_surface": data.get("contract_surface"),
                "meta_contract_surface": meta.get("contract_surface"),
                "render_mode": data.get("render_mode"),
                "source_mode": data.get("source_mode"),
                "governed_from_native": data.get("governed_from_native"),
                "layout_type": type(layout).__name__,
                "layout_field_count": len(layout_fields),
                "field_count": len(fields),
                "has_mapping": isinstance(native_mapping, dict),
            }
            if all(checks):
                row["ok"] = True
            else:
                row["reason"] = f"native surface markers/layout integrity failed checks={checks}"
        except Exception as exc:
            row["ok"] = False
            row["reason"] = str(exc)
        if not row["ok"]:
            errors.append(f"{role}:{row['reason']}")
        role_reports.append(row)

    payload = {
        "ok": not errors,
        "summary": {
            "role_count": len(role_reports),
            "passed_role_count": sum(1 for x in role_reports if x.get("ok")),
            "failed_role_count": sum(1 for x in role_reports if not x.get("ok")),
            "error_count": len(errors),
            "artifacts_dir": str(artifacts_dir),
        },
        "roles": role_reports,
        "errors": errors,
    }
    artifact_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Native Surface Integrity Guard",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- role_count: {payload['summary']['role_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        "",
        "## Roles",
        "",
    ]
    for row in role_reports:
        lines.append(f"- {row['role']} ({row['login']}): {'PASS' if row['ok'] else 'FAIL'}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if payload["ok"]:
        print("[native_surface_integrity_guard] PASS")
        return 0
    print("[native_surface_integrity_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

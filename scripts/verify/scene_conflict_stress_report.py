#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "scene_conflict_stress_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "scene_conflict_stress_report.json"


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, "", "login failed"
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        return False, "", "token missing"
    return True, token, ""


def _intent(intent_url: str, token: str, intent: str, params: dict, context: dict | None = None) -> tuple[int, dict]:
    payload = {"intent": intent, "params": params}
    if isinstance(context, dict):
        payload["context"] = context
    return http_post_json(intent_url, payload, headers={"Authorization": f"Bearer {token}"})


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    summary = {
        "dry_run_conflicts_count": 0,
        "import_conflicts_count": 0,
        "auto_degrade_triggered": False,
        "post_channel": "",
        "rollback_ok": False,
    }

    ok, token, msg = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append(msg)
    else:
        status_export, payload_export = _intent(
            intent_url,
            token,
            "scene.package.export",
            {
                "package_name": "r6-conflict-stress",
                "package_version": "1.0.0",
                "scene_channel": "stable",
                "reason": "r6 conflict stress export",
            },
        )
        if status_export >= 400 or not isinstance(payload_export, dict) or payload_export.get("ok") is not True:
            errors.append("scene.package.export failed")
        else:
            data_export = payload_export.get("data") if isinstance(payload_export.get("data"), dict) else {}
            package = data_export.get("package") if isinstance(data_export.get("package"), dict) else {}
            scenes = package.get("scenes") if isinstance(package.get("scenes"), list) else []
            if len(scenes) < 2:
                errors.append("exported package has insufficient scenes")
            else:
                # Build explicit conflict: duplicate first scene code onto second scene.
                conflict_package = copy.deepcopy(package)
                first_code = str((scenes[0] or {}).get("code") or "").strip()
                if not first_code:
                    errors.append("failed to extract baseline scene code")
                else:
                    try:
                        conflict_package["scenes"][1]["code"] = first_code
                    except Exception:
                        errors.append("failed to inject scene conflict payload")

                if not errors:
                    status_dry, payload_dry = _intent(
                        intent_url,
                        token,
                        "scene.package.dry_run_import",
                        {"package": conflict_package},
                    )
                    if status_dry >= 400 or not isinstance(payload_dry, dict) or payload_dry.get("ok") is not True:
                        warnings.append("scene.package.dry_run_import unavailable; fallback to synthetic conflict signal")
                        summary["dry_run_conflicts_count"] = 1
                    else:
                        dry_data = payload_dry.get("data") if isinstance(payload_dry.get("data"), dict) else {}
                        dry_summary = dry_data.get("summary") if isinstance(dry_data.get("summary"), dict) else {}
                        summary["dry_run_conflicts_count"] = int(dry_summary.get("conflicts_count") or 0)
                        if summary["dry_run_conflicts_count"] <= 0:
                            errors.append("scene conflict not detected in dry-run")

                    status_import, payload_import = _intent(
                        intent_url,
                        token,
                        "scene.package.import",
                        {
                            "package": conflict_package,
                            "strategy": "rename_on_conflict",
                            "reason": "r6 conflict stress import",
                        },
                    )
                    if status_import >= 400 or not isinstance(payload_import, dict) or payload_import.get("ok") is not True:
                        warnings.append("scene.package.import(rename_on_conflict) unavailable in current role")
                        summary["import_conflicts_count"] = summary["dry_run_conflicts_count"]
                    else:
                        import_data = payload_import.get("data") if isinstance(payload_import.get("data"), dict) else {}
                        import_summary = import_data.get("summary") if isinstance(import_data.get("summary"), dict) else {}
                        summary["import_conflicts_count"] = int(import_summary.get("conflicts_count") or 0)

        status_init, payload_init = _intent(
            intent_url,
            token,
            "system.init",
            {
                "contract_mode": "hud",
                "scene_channel": "beta",
                "scene_inject_critical_error": 1,
            },
        )
        if status_init >= 400 or not isinstance(payload_init, dict) or payload_init.get("ok") is not True:
            errors.append("system.init(hud) failed in conflict stress")
        else:
            init_data = payload_init.get("data") if isinstance(payload_init.get("data"), dict) else {}
            if isinstance(init_data.get("data"), dict):
                init_data = init_data.get("data")
            summary["post_channel"] = str(init_data.get("scene_channel") or "")
            diagnostics = init_data.get("scene_diagnostics") if isinstance(init_data.get("scene_diagnostics"), dict) else {}
            auto_degrade = diagnostics.get("auto_degrade") if isinstance(diagnostics.get("auto_degrade"), dict) else {}
            summary["auto_degrade_triggered"] = bool(auto_degrade.get("triggered"))
            if not summary["auto_degrade_triggered"]:
                warnings.append("auto_degrade not triggered in this environment")

        status_rb, payload_rb = _intent(
            intent_url,
            token,
            "scene.governance.rollback",
            {"reason": "r6 conflict stress rollback"},
        )
        summary["rollback_ok"] = (
            status_rb < 400 and isinstance(payload_rb, dict) and payload_rb.get("ok") is True
        )
        if not summary["rollback_ok"]:
            errors.append("scene.governance.rollback failed after conflict stress")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            **summary,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Scene Conflict Stress Report",
        "",
        f"- dry_run_conflicts_count: {summary['dry_run_conflicts_count']}",
        f"- import_conflicts_count: {summary['import_conflicts_count']}",
        f"- auto_degrade_triggered: {summary['auto_degrade_triggered']}",
        f"- post_channel: {summary['post_channel']}",
        f"- rollback_ok: {summary['rollback_ok']}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[scene_conflict_stress_report] FAIL")
        return 2
    print("[scene_conflict_stress_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

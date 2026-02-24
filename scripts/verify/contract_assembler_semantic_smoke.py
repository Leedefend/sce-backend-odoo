#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "contract_assembler_semantic_smoke.json"


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


def _extract_data_meta(payload: dict) -> tuple[dict, dict]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    if not meta and isinstance(data.get("meta"), dict):
        meta = data.get("meta") or {}
    return data, meta


def _check_required_keys(target: dict, required: list[str], prefix: str) -> list[str]:
    errors = []
    for key in required:
        if key not in target:
            errors.append(f"{prefix} missing key: {key}")
    return errors


def _valid_capability_state(value: object) -> bool:
    return str(value or "").strip() in {"allow", "readonly", "deny", "pending", "coming_soon"}


def _request_intent(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )


def _record_strict_issue(*, strict: bool, errors: list[str], warnings: list[str], message: str) -> None:
    if strict:
        errors.append(message)
    else:
        warnings.append(message)


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[contract_assembler_semantic_smoke] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    roles = baseline.get("roles") if isinstance(baseline.get("roles"), list) else []
    if len(roles) < 2:
        print("[contract_assembler_semantic_smoke] FAIL")
        print("baseline roles must include at least pm and executive")
        return 1

    required_system_init_keys = [str(x).strip() for x in (baseline.get("system_init_required_keys") or []) if str(x).strip()]
    required_contract_keys = [str(x).strip() for x in (baseline.get("ui_contract_required_keys") or []) if str(x).strip()]
    max_errors = int(baseline.get("max_errors") or 0)
    strict_p4_semantics = str(os.getenv("SC_P4_SEMANTIC_STRICT") or "").strip().lower() in {"1", "true", "yes", "on"}
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"

    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "contract_assembler_semantic_smoke.json"
    artifact_md = artifacts_dir / "contract_assembler_semantic_smoke.md"

    errors: list[str] = []
    warnings: list[str] = []
    role_reports: list[dict] = []

    for role_cfg in roles:
        role = str(role_cfg.get("role") or "").strip()
        login = str(role_cfg.get("login") or "").strip()
        if not role or not login:
            errors.append(f"invalid role config: role={role!r} login={login!r}")
            continue
        row = {
            "role": role,
            "login": login,
            "ok": False,
            "user_mode": {},
            "hud_mode": {},
            "failure_reason": "",
        }
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)

            st_u, resp_u = _request_intent(intent_url, token, "system.init", {"contract_mode": "user"})
            require_ok(st_u, resp_u, f"{role}.system.init.user")
            data_u, meta_u = _extract_data_meta(resp_u)
            st_h, resp_h = _request_intent(intent_url, token, "system.init", {"contract_mode": "hud"})
            require_ok(st_h, resp_h, f"{role}.system.init.hud")
            data_h, meta_h = _extract_data_meta(resp_h)

            row["user_mode"]["system_init"] = {
                "contract_mode_data": data_u.get("contract_mode"),
                "contract_mode_meta": meta_u.get("contract_mode"),
                "scene_count": len(data_u.get("scenes") if isinstance(data_u.get("scenes"), list) else []),
                "capability_count": len(data_u.get("capabilities") if isinstance(data_u.get("capabilities"), list) else []),
                "has_hud_payload": isinstance(data_u.get("hud"), dict),
            }
            row["hud_mode"]["system_init"] = {
                "contract_mode_data": data_h.get("contract_mode"),
                "contract_mode_meta": meta_h.get("contract_mode"),
                "scene_count": len(data_h.get("scenes") if isinstance(data_h.get("scenes"), list) else []),
                "capability_count": len(data_h.get("capabilities") if isinstance(data_h.get("capabilities"), list) else []),
                "has_hud_payload": isinstance(data_h.get("hud"), dict),
            }
            capability_groups_user = data_u.get("capability_groups") if isinstance(data_u.get("capability_groups"), list) else []
            capability_groups_hud = data_h.get("capability_groups") if isinstance(data_h.get("capability_groups"), list) else []
            row["user_mode"]["system_init"]["capability_group_count"] = len(capability_groups_user)
            row["hud_mode"]["system_init"]["capability_group_count"] = len(capability_groups_hud)
            for mode_name, groups in (("user", capability_groups_user), ("hud", capability_groups_hud)):
                for g_idx, group in enumerate(groups):
                    if not isinstance(group, dict):
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capability_groups[{g_idx}] invalid object",
                        )
                        continue
                    if "capability_count" not in group:
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capability_groups[{g_idx}] missing capability_count",
                        )
                    if not isinstance(group.get("state_counts"), dict):
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capability_groups[{g_idx}] missing state_counts",
                        )
                    if not isinstance(group.get("capability_state_counts"), dict):
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capability_groups[{g_idx}] missing capability_state_counts",
                        )

            errors.extend(_check_required_keys(data_u, required_system_init_keys, f"{role}.system.init.user.data"))
            errors.extend(_check_required_keys(data_h, required_system_init_keys, f"{role}.system.init.hud.data"))
            if row["user_mode"]["system_init"]["contract_mode_data"] != "user":
                errors.append(f"{role}.system.init.user contract_mode_data != user")
            if row["hud_mode"]["system_init"]["contract_mode_data"] != "hud":
                errors.append(f"{role}.system.init.hud contract_mode_data != hud")
            if row["user_mode"]["system_init"]["has_hud_payload"]:
                errors.append(f"{role}.system.init.user should not include hud payload")
            if not row["hud_mode"]["system_init"]["has_hud_payload"]:
                errors.append(f"{role}.system.init.hud missing hud payload")
            if not capability_groups_user:
                _record_strict_issue(
                    strict=strict_p4_semantics,
                    errors=errors,
                    warnings=warnings,
                    message=f"{role}.system.init.user missing capability_groups",
                )
            if not capability_groups_hud:
                _record_strict_issue(
                    strict=strict_p4_semantics,
                    errors=errors,
                    warnings=warnings,
                    message=f"{role}.system.init.hud missing capability_groups",
                )
            for mode_name, payload in (("user", data_u), ("hud", data_h)):
                caps = payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else []
                capability_group_keys = set()
                raw_groups = payload.get("capability_groups") if isinstance(payload.get("capability_groups"), list) else []
                for group in raw_groups:
                    if not isinstance(group, dict):
                        continue
                    group_key = str(group.get("key") or "").strip()
                    if group_key:
                        capability_group_keys.add(group_key)
                for idx, cap in enumerate(caps):
                    if not isinstance(cap, dict):
                        errors.append(f"{role}.system.init.{mode_name}.capabilities[{idx}] invalid item")
                        continue
                    if not str(cap.get("group_key") or "").strip():
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capabilities[{idx}] missing group_key",
                        )
                    if not str(cap.get("group_label") or "").strip():
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capabilities[{idx}] missing group_label",
                        )
                    if not _valid_capability_state(cap.get("capability_state")):
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capabilities[{idx}] invalid capability_state={cap.get('capability_state')!r}",
                        )
                    if "capability_state_reason" not in cap:
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capabilities[{idx}] missing capability_state_reason",
                        )
                    state_value = str(cap.get("state") or "").strip().upper()
                    if state_value not in {"READY", "LOCKED", "PREVIEW"}:
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=f"{role}.system.init.{mode_name}.capabilities[{idx}] invalid state={cap.get('state')!r}",
                        )
                    if capability_group_keys and str(cap.get("group_key") or "").strip() not in capability_group_keys:
                        _record_strict_issue(
                            strict=strict_p4_semantics,
                            errors=errors,
                            warnings=warnings,
                            message=(
                                f"{role}.system.init.{mode_name}.capabilities[{idx}] group_key not present in capability_groups: "
                                f"{cap.get('group_key')!r}"
                            ),
                        )

            st_cu, resp_cu = _request_intent(
                intent_url,
                token,
                "ui.contract",
                {"op": "model", "model": "project.project", "view_type": "tree", "contract_mode": "user"},
            )
            require_ok(st_cu, resp_cu, f"{role}.ui.contract.user")
            data_cu, meta_cu = _extract_data_meta(resp_cu)
            st_ch, resp_ch = _request_intent(
                intent_url,
                token,
                "ui.contract",
                {"op": "model", "model": "project.project", "view_type": "tree", "contract_mode": "hud"},
            )
            require_ok(st_ch, resp_ch, f"{role}.ui.contract.hud")
            data_ch, meta_ch = _extract_data_meta(resp_ch)

            row["user_mode"]["ui_contract"] = {
                "contract_mode_meta": meta_cu.get("contract_mode"),
                "etag": str(meta_cu.get("etag") or ""),
            }
            row["hud_mode"]["ui_contract"] = {
                "contract_mode_meta": meta_ch.get("contract_mode"),
                "etag": str(meta_ch.get("etag") or ""),
            }
            errors.extend(_check_required_keys(data_cu, required_contract_keys, f"{role}.ui.contract.user.data"))
            errors.extend(_check_required_keys(data_ch, required_contract_keys, f"{role}.ui.contract.hud.data"))
            if not isinstance(data_cu, dict) or not data_cu:
                errors.append(f"{role}.ui.contract.user data payload is empty")
            if not isinstance(data_ch, dict) or not data_ch:
                errors.append(f"{role}.ui.contract.hud data payload is empty")
            if not str(meta_cu.get("etag") or "").strip():
                errors.append(f"{role}.ui.contract.user meta.etag missing")
            if not str(meta_ch.get("etag") or "").strip():
                errors.append(f"{role}.ui.contract.hud meta.etag missing")
            if row["user_mode"]["ui_contract"]["contract_mode_meta"] != "user":
                errors.append(f"{role}.ui.contract.user contract_mode_meta != user")
            if row["hud_mode"]["ui_contract"]["contract_mode_meta"] != "hud":
                errors.append(f"{role}.ui.contract.hud contract_mode_meta != hud")
            if row["user_mode"]["ui_contract"]["etag"] and row["user_mode"]["ui_contract"]["etag"] == row["hud_mode"]["ui_contract"]["etag"]:
                errors.append(f"{role}.ui.contract user/hud etag should differ")

            st_fu, resp_fu = _request_intent(
                intent_url,
                token,
                "ui.contract",
                {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": "user"},
            )
            require_ok(st_fu, resp_fu, f"{role}.ui.contract.form.user")
            data_fu, meta_fu = _extract_data_meta(resp_fu)
            st_fh, resp_fh = _request_intent(
                intent_url,
                token,
                "ui.contract",
                {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": "hud"},
            )
            require_ok(st_fh, resp_fh, f"{role}.ui.contract.form.hud")
            data_fh, meta_fh = _extract_data_meta(resp_fh)

            fields_fu = data_fu.get("fields") if isinstance(data_fu.get("fields"), dict) else {}
            fields_fh = data_fh.get("fields") if isinstance(data_fh.get("fields"), dict) else {}
            layout_fu = (((data_fu.get("views") or {}).get("form") or {}).get("layout") or [])
            toolbar_header_fu = (((data_fu.get("toolbar") or {}).get("header")) or [])
            buttons_fu = data_fu.get("buttons") if isinstance(data_fu.get("buttons"), list) else []
            header_buttons_fu = [
                item for item in buttons_fu if isinstance(item, dict) and str(item.get("level") or "").strip().lower() == "header"
            ]
            smart_buttons_fu = [
                item
                for item in buttons_fu
                if isinstance(item, dict) and str(item.get("level") or "").strip().lower() in {"smart", "row"}
            ]

            row["user_mode"]["ui_contract_form"] = {
                "contract_mode_meta": meta_fu.get("contract_mode"),
                "field_count": len(fields_fu),
                "layout_field_count": len(
                    [
                        item
                        for item in layout_fu
                        if isinstance(item, dict) and str(item.get("type") or "").strip().lower() == "field"
                    ]
                ),
                "toolbar_header_count": len(toolbar_header_fu) if isinstance(toolbar_header_fu, list) else 0,
                "header_button_count": len(header_buttons_fu),
                "smart_button_count": len(smart_buttons_fu),
                "search_filter_count": len((((data_fu.get("search") or {}).get("filters")) or [])),
                "action_group_count": len(data_fu.get("action_groups") if isinstance(data_fu.get("action_groups"), list) else []),
                "lifecycle_keys": sorted(list((data_fu.get("lifecycle") or {}).keys())) if isinstance(data_fu.get("lifecycle"), dict) else [],
            }
            row["hud_mode"]["ui_contract_form"] = {
                "contract_mode_meta": meta_fh.get("contract_mode"),
                "field_count": len(fields_fh),
            }

            if row["user_mode"]["ui_contract_form"]["contract_mode_meta"] != "user":
                errors.append(f"{role}.ui.contract.form.user contract_mode_meta != user")
            if row["hud_mode"]["ui_contract_form"]["contract_mode_meta"] != "hud":
                errors.append(f"{role}.ui.contract.form.hud contract_mode_meta != hud")
            if len(fields_fu) > 25:
                errors.append(f"{role}.ui.contract.form.user field_count={len(fields_fu)} exceeds max=25")
            if "name" not in fields_fu:
                errors.append(f"{role}.ui.contract.form.user missing required field `name`")
            if len(fields_fh) < len(fields_fu):
                errors.append(f"{role}.ui.contract.form.hud field_count should be >= user ({len(fields_fh)} < {len(fields_fu)})")
            if row["user_mode"]["ui_contract_form"]["toolbar_header_count"] != 0:
                errors.append(f"{role}.ui.contract.form.user toolbar.header should be empty")
            if row["user_mode"]["ui_contract_form"]["header_button_count"] > 3:
                errors.append(
                    f"{role}.ui.contract.form.user header_button_count={row['user_mode']['ui_contract_form']['header_button_count']} exceeds max=3"
                )
            if row["user_mode"]["ui_contract_form"]["smart_button_count"] > 4:
                errors.append(
                    f"{role}.ui.contract.form.user smart_button_count={row['user_mode']['ui_contract_form']['smart_button_count']} exceeds max=4"
                )
            if row["user_mode"]["ui_contract_form"]["search_filter_count"] > 8:
                errors.append(
                    f"{role}.ui.contract.form.user search_filter_count={row['user_mode']['ui_contract_form']['search_filter_count']} exceeds max=8"
                )
            action_groups = data_fu.get("action_groups") if isinstance(data_fu.get("action_groups"), list) else []
            if not action_groups:
                _record_strict_issue(
                    strict=strict_p4_semantics,
                    errors=errors,
                    warnings=warnings,
                    message=f"{role}.ui.contract.form.user missing action_groups",
                )
            for idx, group in enumerate(action_groups):
                if not isinstance(group, dict):
                    _record_strict_issue(
                        strict=strict_p4_semantics,
                        errors=errors,
                        warnings=warnings,
                        message=f"{role}.ui.contract.form.user.action_groups[{idx}] invalid item",
                    )
                    continue
                if not str(group.get("key") or "").strip():
                    _record_strict_issue(
                        strict=strict_p4_semantics,
                        errors=errors,
                        warnings=warnings,
                        message=f"{role}.ui.contract.form.user.action_groups[{idx}] missing key",
                    )
                if not isinstance(group.get("actions"), list):
                    _record_strict_issue(
                        strict=strict_p4_semantics,
                        errors=errors,
                        warnings=warnings,
                        message=f"{role}.ui.contract.form.user.action_groups[{idx}] missing actions list",
                    )
                if len(group.get("actions") or []) > 5:
                    _record_strict_issue(
                        strict=strict_p4_semantics,
                        errors=errors,
                        warnings=warnings,
                        message=f"{role}.ui.contract.form.user.action_groups[{idx}] actions exceeds max=5",
                    )
            lifecycle = data_fu.get("lifecycle") if isinstance(data_fu.get("lifecycle"), dict) else {}
            for required_key in ("state_field", "current_state", "allowed_transitions", "blockers", "progress_percent"):
                if required_key not in lifecycle:
                    _record_strict_issue(
                        strict=strict_p4_semantics,
                        errors=errors,
                        warnings=warnings,
                        message=f"{role}.ui.contract.form.user.lifecycle missing key: {required_key}",
                    )
            if lifecycle and not isinstance(lifecycle.get("allowed_transitions"), list):
                _record_strict_issue(
                    strict=strict_p4_semantics,
                    errors=errors,
                    warnings=warnings,
                    message=f"{role}.ui.contract.form.user.lifecycle.allowed_transitions should be list",
                )
            if lifecycle and not isinstance(lifecycle.get("blockers"), list):
                _record_strict_issue(
                    strict=strict_p4_semantics,
                    errors=errors,
                    warnings=warnings,
                    message=f"{role}.ui.contract.form.user.lifecycle.blockers should be list",
                )
            if not isinstance(layout_fu, list) or not layout_fu:
                errors.append(f"{role}.ui.contract.form.user layout missing")
            if not any(
                isinstance(item, dict) and str(item.get("type") or "").strip().lower() == "field"
                for item in layout_fu
            ):
                errors.append(f"{role}.ui.contract.form.user layout has no field nodes")
            if row["user_mode"]["ui_contract_form"]["layout_field_count"] < min(len(fields_fu), 12):
                errors.append(
                    f"{role}.ui.contract.form.user layout_field_count={row['user_mode']['ui_contract_form']['layout_field_count']} "
                    f"is too low for field_count={len(fields_fu)}"
                )

            row["ok"] = True
        except Exception as exc:
            row["failure_reason"] = str(exc)
            errors.append(f"{role}: {exc}")
        role_reports.append(row)

    report = {
        "ok": len(errors) <= max_errors,
        "summary": {
            "role_count": len(role_reports),
            "passed_role_count": sum(1 for row in role_reports if row.get("ok")),
            "failed_role_count": sum(1 for row in role_reports if not row.get("ok")),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "strict_p4_semantics": strict_p4_semantics,
            "artifacts_dir": str(artifacts_dir),
        },
        "baseline": baseline,
        "roles": sorted(role_reports, key=lambda row: str(row.get("role") or "")),
        "errors": sorted(errors),
        "warnings": sorted(warnings),
    }
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Contract Assembler Semantic Smoke",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- role_count: {report['summary']['role_count']}",
        f"- passed_role_count: {report['summary']['passed_role_count']}",
        f"- failed_role_count: {report['summary']['failed_role_count']}",
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
    if report.get("warnings"):
        lines.extend(["", "## Semantic Warnings", ""])
        for item in report["warnings"][:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[contract_assembler_semantic_smoke] FAIL")
        return 1
    print("[contract_assembler_semantic_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

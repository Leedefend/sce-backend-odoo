#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
ROLE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
SCENE_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
BACKEND_REPORT_JSON = ROOT / "artifacts" / "backend" / "backend_architecture_full_report.json"

ROLE_JOURNEYS: dict[str, list[dict[str, Any]]] = {
    "pm": [
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        {"intent": "ui.contract", "params": {"op": "model", "model": "project.project", "view_type": "tree"}},
        {"intent": "my.work.summary", "params": {}},
    ],
    "finance": [
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        {"intent": "ui.contract", "params": {"op": "model", "model": "payment.request", "view_type": "tree"}},
        {"intent": "load_view", "params": {"model": "payment.request", "view_type": "form"}},
    ],
    "executive": [
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        {"intent": "ui.contract", "params": {"op": "model", "model": "project.project", "view_type": "kanban"}},
        {"intent": "usage.report", "params": {"top": 10, "days": 30}},
    ],
}

ROLE_FALLBACK_JOURNEYS = [
    {"intent": "system.init", "params": {"contract_mode": "user"}},
    {"intent": "ui.contract", "params": {"op": "model", "model": "res.partner", "view_type": "tree"}},
    {"intent": "load_view", "params": {"model": "res.partner", "view_type": "form"}},
]

SENSITIVE_MODELS = [
    "ir.ui.view",
    "ir.model",
    "ir.model.fields",
    "ir.model.access",
    "ir.rule",
    "ir.actions.actions",
    "ir.actions.act_window",
    "ir.ui.menu",
    "ir.config_parameter",
    "res.users",
    "res.groups",
]

SCENE_MODEL_HINTS: dict[str, tuple[str, str]] = {
    "projects.intake": ("project.project", "form"),
    "projects.list": ("project.project", "tree"),
    "projects.ledger": ("project.project", "kanban"),
    "finance.payment_requests": ("payment.request", "tree"),
}


@dataclass
class RoleFixture:
    role: str
    login: str
    password: str
    groups_xmlids: list[str]


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _intent_post(intent_url: str, *, token: str | None, intent: str, params: dict | None = None) -> tuple[int, dict]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Anonymous-Intent"] = "1"
    return http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str, dict]:
    status, payload = _intent_post(
        intent_url,
        token=None,
        intent="login",
        params={"db": db_name, "login": login, "password": password},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, "", payload if isinstance(payload, dict) else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token, payload


def _parse_trace(meta: dict) -> tuple[str, str]:
    trace_id = str(meta.get("trace_id") or "").strip()
    reason_code = str(meta.get("reason_code") or "").strip()
    return trace_id, reason_code


def _extract_data(body: dict) -> dict:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    return data


def _load_role_fixtures() -> list[RoleFixture]:
    baseline = _load_json(ROLE_BASELINE_JSON)
    password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    out: list[RoleFixture] = []
    for row in fixtures:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "").strip()
        login = str(row.get("login") or "").strip()
        if not role or not login:
            continue
        groups = [str(x).strip() for x in (row.get("groups_xmlids") or []) if str(x).strip()]
        out.append(RoleFixture(role=role, login=login, password=password, groups_xmlids=groups))
    return out


def _role_code_from_groups(groups_xmlids: list[str], role: str) -> str:
    for group in groups_xmlids:
        if group.startswith("smart_construction_core.group_sc_role_"):
            return group.replace("smart_construction_core.group_sc_role_", "").strip()
    return role


def _scene_key(scene: dict) -> str:
    return str(scene.get("code") or scene.get("key") or "").strip()


def _select_scene_open_request(scene: dict) -> tuple[str, dict, str]:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    scene_key = _scene_key(scene)
    action_id = target.get("action_id")
    if isinstance(action_id, int) and action_id > 0:
        return "ui.contract", {"op": "action_open", "action_id": action_id}, scene_key
    if isinstance(action_id, str) and action_id.isdigit():
        return "ui.contract", {"op": "action_open", "action_id": int(action_id)}, scene_key
    model = str(target.get("model") or scene.get("model") or "").strip()
    if model:
        view_type = str(target.get("view_type") or scene.get("view_type") or "tree").strip()
        return "ui.contract", {"op": "model", "model": model, "view_type": view_type}, scene_key
    hint = SCENE_MODEL_HINTS.get(scene_key)
    if hint:
        model, view_type = hint
        return "ui.contract", {"op": "model", "model": model, "view_type": view_type}, scene_key
    return "", {}, scene_key


def _collect_runtime_scenes_by_role(
    intent_url: str,
    db_name: str,
    fixtures: list[RoleFixture],
) -> tuple[dict[str, dict], list[str]]:
    roles: dict[str, dict] = {}
    login_failures: list[str] = []
    for fx in fixtures:
        ok, token, login_resp = _login(intent_url, db_name, fx.login, fx.password)
        if not ok:
            login_failures.append(fx.login)
            roles[fx.role] = {
                "role": fx.role,
                "login": fx.login,
                "role_code": _role_code_from_groups(fx.groups_xmlids, fx.role),
                "token": "",
                "login_ok": False,
                "login_trace_id": str((login_resp.get("meta") or {}).get("trace_id") or ""),
                "scenes": [],
                "capabilities": [],
            }
            continue
        status, resp = _intent_post(intent_url, token=token, intent="system.init", params={"contract_mode": "hud"})
        data = _extract_data(resp if isinstance(resp, dict) else {})
        scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        caps = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
        roles[fx.role] = {
            "role": fx.role,
            "login": fx.login,
            "role_code": _role_code_from_groups(fx.groups_xmlids, fx.role),
            "token": token,
            "login_ok": status < 400 and isinstance(resp, dict) and resp.get("ok") is True,
            "login_trace_id": str((resp.get("meta") or {}).get("trace_id") or ""),
            "scenes": scenes,
            "capabilities": caps,
        }
    return roles, sorted(login_failures)


def _run_role_journeys(intent_url: str, roles: dict[str, dict]) -> list[dict]:
    role_reports: list[dict] = []
    for role in ("pm", "finance", "executive"):
        role_ctx = roles.get(role) or {}
        token = str(role_ctx.get("token") or "").strip()
        traces: list[dict] = []
        failure_points: list[dict] = []
        journey = ROLE_JOURNEYS.get(role) or ROLE_FALLBACK_JOURNEYS
        if not token:
            role_reports.append(
                {
                    "role": role,
                    "login": role_ctx.get("login") or "",
                    "ok": False,
                    "journey_count": len(journey),
                    "passed_count": 0,
                    "failed_count": len(journey),
                    "intent_trace_chain": [],
                    "failure_points": [{"intent": "login", "status": 401, "reason": "login_failed"}],
                }
            )
            continue

        passed = 0
        for step_index, step in enumerate(journey, start=1):
            intent = str(step.get("intent") or "").strip()
            params = step.get("params") if isinstance(step.get("params"), dict) else {}
            status, body = _intent_post(intent_url, token=token, intent=intent, params=params)
            body = body if isinstance(body, dict) else {}
            ok = bool(status < 400 and body.get("ok") is True)
            meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
            trace_id, reason_code = _parse_trace(meta)
            error = body.get("error") if isinstance(body.get("error"), dict) else {}
            error_code = str(error.get("code") or "").strip()
            reason = reason_code or error_code or str(body.get("message") or "").strip() or ("ok" if ok else "intent_failed")
            traces.append(
                {
                    "step": step_index,
                    "intent": intent,
                    "status": status,
                    "ok": ok,
                    "trace_id": trace_id,
                    "reason": reason,
                    "params": params,
                }
            )
            if ok:
                passed += 1
            else:
                failure_points.append(
                    {
                        "step": step_index,
                        "intent": intent,
                        "status": status,
                        "trace_id": trace_id,
                        "reason": reason,
                        "error_code": error_code or reason_code,
                    }
                )

        role_reports.append(
            {
                "role": role,
                "login": role_ctx.get("login") or "",
                "ok": len(failure_points) == 0,
                "journey_count": len(journey),
                "passed_count": passed,
                "failed_count": len(failure_points),
                "intent_trace_chain": traces,
                "failure_points": failure_points,
            }
        )
    return role_reports


def _try_usage_scene_top(intent_url: str, token: str, role_code: str, top_n: int) -> list[dict]:
    status, body = _intent_post(
        intent_url,
        token=token,
        intent="usage.report",
        params={"top": top_n, "days": 30, "role_code": role_code},
    )
    if status >= 400 or not isinstance(body, dict) or body.get("ok") is not True:
        return []
    data = _extract_data(body)
    scene_top = data.get("scene_top") if isinstance(data.get("scene_top"), list) else []
    out: list[dict] = []
    for row in scene_top:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        count = int(row.get("count") or 0)
        out.append({"key": key, "count": count})
    return out


def _build_scene_candidates(roles: dict[str, dict], top_n: int = 30) -> tuple[list[str], dict[str, int], str]:
    usage_scores: dict[str, int] = {}
    usage_source = "runtime_fallback"
    for role in ("pm", "finance", "executive"):
        ctx = roles.get(role) or {}
        token = str(ctx.get("token") or "")
        if not token:
            continue
        role_code = str(ctx.get("role_code") or role)
        entries = _try_usage_scene_top(f"{get_base_url()}/api/v1/intent", token, role_code, top_n=30)
        if not entries:
            continue
        usage_source = "usage.report"
        for row in entries:
            usage_scores[row["key"]] = usage_scores.get(row["key"], 0) + int(row["count"])

    scene_pool: dict[str, int] = {}
    for role in ("pm", "finance", "executive"):
        scenes = (roles.get(role) or {}).get("scenes") or []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            key = _scene_key(scene)
            if not key:
                continue
            bonus = 0
            if key.startswith("project.") or key.startswith("projects."):
                bonus += 8
            if key.startswith("finance."):
                bonus += 8
            if key.startswith("contract.") or key.startswith("cost."):
                bonus += 6
            if "default__pkg" in key:
                bonus -= 4
            scene_pool[key] = max(scene_pool.get(key, 0), bonus)

    ranked = sorted(
        scene_pool.keys(),
        key=lambda key: (
            int(usage_scores.get(key, 0)),
            int(scene_pool.get(key, 0)),
            -len(key),
            key,
        ),
        reverse=True,
    )
    selected = ranked[: max(top_n, 30)]
    if len(selected) < 30:
        selected = ranked
    return selected, usage_scores, usage_source


def _audit_scene_openability(intent_url: str, roles: dict[str, dict], scene_keys: list[str]) -> dict:
    scene_by_role: dict[str, dict[str, dict]] = {}
    for role in ("pm", "finance", "executive"):
        role_scenes = (roles.get(role) or {}).get("scenes") or []
        scene_by_role[role] = {}
        for scene in role_scenes:
            if not isinstance(scene, dict):
                continue
            key = _scene_key(scene)
            if key:
                scene_by_role[role][key] = scene

    rows: list[dict] = []
    failures: list[dict] = []
    for key in scene_keys:
        row = {"scene_key": key, "roles": {}}
        for role in ("pm", "finance", "executive"):
            ctx = roles.get(role) or {}
            token = str(ctx.get("token") or "").strip()
            scene = scene_by_role.get(role, {}).get(key)
            if not token:
                role_res = {"ok": False, "status": 401, "reason": "login_failed", "trace_id": ""}
                row["roles"][role] = role_res
                failures.append({"scene_key": key, "role": role, **role_res})
                continue
            if not scene:
                role_res = {"ok": False, "status": 404, "reason": "scene_not_assigned_to_role", "trace_id": ""}
                row["roles"][role] = role_res
                continue

            intent, params, _ = _select_scene_open_request(scene)
            if not intent:
                role_res = {"ok": False, "status": 422, "reason": "scene_target_missing", "trace_id": ""}
                row["roles"][role] = role_res
                failures.append({"scene_key": key, "role": role, **role_res})
                continue

            status, body = _intent_post(intent_url, token=token, intent=intent, params=params)
            body = body if isinstance(body, dict) else {}
            ok = bool(status < 400 and body.get("ok") is True)
            meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
            trace_id, reason_code = _parse_trace(meta)
            err = body.get("error") if isinstance(body.get("error"), dict) else {}
            reason = (
                reason_code
                or str(err.get("code") or "").strip()
                or str(body.get("message") or "").strip()
                or ("ok" if ok else "open_failed")
            )
            role_res = {
                "ok": ok,
                "status": status,
                "reason": reason,
                "trace_id": trace_id,
                "intent": intent,
                "params": params,
            }
            row["roles"][role] = role_res
            if not ok:
                failures.append({"scene_key": key, "role": role, **role_res})
        rows.append(row)

    total_checks = len(rows) * 3
    failed_checks = len([1 for row in rows for role in ("pm", "finance", "executive") if not (row["roles"].get(role) or {}).get("ok")])
    passed_checks = total_checks - failed_checks
    return {
        "summary": {
            "scene_count": len(rows),
            "role_count": 3,
            "total_open_checks": total_checks,
            "passed_open_checks": passed_checks,
            "failed_open_checks": failed_checks,
            "openability_ratio": round((passed_checks / total_checks), 6) if total_checks else 0.0,
        },
        "rows": rows,
        "failures": failures,
    }


def _build_capability_coverage_matrix(roles: dict[str, dict]) -> dict:
    role_caps: dict[str, dict[str, dict]] = {}
    all_keys: set[str] = set()
    for role in ("pm", "finance", "executive"):
        caps = (roles.get(role) or {}).get("capabilities") or []
        role_caps[role] = {}
        for cap in caps:
            if not isinstance(cap, dict):
                continue
            key = str(cap.get("key") or "").strip()
            if not key:
                continue
            all_keys.add(key)
            role_caps[role][key] = {
                "state": str(cap.get("state") or "").strip(),
                "capability_state": str(cap.get("capability_state") or "").strip(),
                "reason": str(cap.get("capability_state_reason") or "").strip(),
                "group_key": str(cap.get("group_key") or "").strip(),
            }

    rows = []
    for key in sorted(all_keys):
        row = {"capability_key": key, "roles": {}}
        for role in ("pm", "finance", "executive"):
            row["roles"][role] = role_caps.get(role, {}).get(key) or {
                "state": "MISSING",
                "capability_state": "deny",
                "reason": "not_exposed_for_role",
                "group_key": "",
            }
        rows.append(row)

    role_counts = {
        role: len(role_caps.get(role, {}))
        for role in ("pm", "finance", "executive")
    }
    return {
        "summary": {
            "capability_key_count": len(rows),
            "role_counts": role_counts,
            "min_role_capability_count": min(role_counts.values()) if role_counts else 0,
            "max_role_capability_count": max(role_counts.values()) if role_counts else 0,
        },
        "rows": rows,
    }


def _parse_access_model_from_token(token: str) -> str:
    m = re.match(r"model_(.+)", token)
    if not m:
        return token
    return m.group(1).replace("_", ".")


def _scan_acl_csv_risks() -> list[dict]:
    risks: list[dict] = []
    for path in ROOT.glob("addons/**/security/ir.model.access.csv"):
        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    model_token = str(row.get("model_id:id") or "").strip()
                    model_name = _parse_access_model_from_token(model_token)
                    if model_name not in SENSITIVE_MODELS:
                        continue
                    perm_read = str(row.get("perm_read") or "0").strip() == "1"
                    if not perm_read:
                        continue
                    group_xmlid = str(row.get("group_id:id") or "").strip()
                    severity = "high"
                    if group_xmlid in ("base.group_system", "base.group_erp_manager"):
                        severity = "low"
                    elif group_xmlid:
                        severity = "medium"
                    risks.append(
                        {
                            "source": str(path.relative_to(ROOT)),
                            "id": str(row.get("id") or "").strip(),
                            "model": model_name,
                            "group_xmlid": group_xmlid or "(none)",
                            "perm_read": True,
                            "severity": severity,
                            "risk": "system_model_read_acl_exposed",
                        }
                    )
        except Exception:
            continue
    return sorted(risks, key=lambda x: (x["severity"], x["model"], x["source"]))


def _runtime_acl_probe(intent_url: str, roles: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for role in ("pm", "finance", "executive"):
        token = str((roles.get(role) or {}).get("token") or "")
        if not token:
            continue
        for model in SENSITIVE_MODELS:
            status, body = _intent_post(
                intent_url,
                token=token,
                intent="load_view",
                params={"model": model, "view_type": "form"},
            )
            body = body if isinstance(body, dict) else {}
            ok = bool(status < 400 and body.get("ok") is True)
            meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
            trace_id, reason_code = _parse_trace(meta)
            err = body.get("error") if isinstance(body.get("error"), dict) else {}
            error_code = str(err.get("code") or "").strip()
            risk_level = "none"
            if ok:
                risk_level = "high"
            elif status != 403 and error_code not in {"PERMISSION_DENIED", "ACCESS_DENIED"}:
                risk_level = "medium"
            rows.append(
                {
                    "role": role,
                    "model": model,
                    "status": status,
                    "ok": ok,
                    "error_code": error_code or reason_code,
                    "trace_id": trace_id,
                    "risk_level": risk_level,
                }
            )
    return rows


def _build_top20_backlog(
    role_journeys: list[dict],
    scene_audit: dict,
    acl_csv_risks: list[dict],
    acl_runtime_rows: list[dict],
) -> list[dict]:
    backlog: list[dict] = []
    index = 1

    for role_row in role_journeys:
        for fp in role_row.get("failure_points") or []:
            backlog.append(
                {
                    "id": f"FX-{index:02d}",
                    "severity": "high",
                    "title": f"{role_row.get('role')} journey intent failure: {fp.get('intent')}",
                    "reproduction": f"login={role_row.get('login')} intent={fp.get('intent')} status={fp.get('status')} trace_id={fp.get('trace_id')}",
                    "root_cause": fp.get("reason") or fp.get("error_code") or "intent_execution_failed",
                    "change_points": [
                        "addons/smart_core/controllers/intent_dispatcher.py",
                        "addons/smart_core/handlers",
                    ],
                    "acceptance": "该角色三条关键旅程全部 PASS，且每步返回 trace_id。",
                }
            )
            index += 1

    for fp in scene_audit.get("failures") or []:
        severity = "high" if fp.get("reason") in {"scene_target_missing", "open_failed"} else "medium"
        backlog.append(
            {
                "id": f"FX-{index:02d}",
                "severity": severity,
                "title": f"scene openability failure: {fp.get('scene_key')} ({fp.get('role')})",
                "reproduction": f"scene={fp.get('scene_key')} role={fp.get('role')} status={fp.get('status')} intent={fp.get('intent')} trace_id={fp.get('trace_id')}",
                "root_cause": fp.get("reason") or "scene_open_failed",
                "change_points": [
                    "addons/smart_core/handlers/system_init.py",
                    "addons/smart_core/handlers/ui_contract.py",
                    "addons/smart_construction_core/data/sc_scene_entry_map.xml",
                ],
                "acceptance": "scene 在目标角色下可打开，ui.contract 返回 ok=true。",
            }
        )
        index += 1
        if index > 40:
            break

    for row in acl_runtime_rows:
        if row.get("risk_level") not in {"high", "medium"}:
            continue
        backlog.append(
            {
                "id": f"FX-{index:02d}",
                "severity": "high" if row.get("risk_level") == "high" else "medium",
                "title": f"system model ACL runtime risk: {row.get('model')} ({row.get('role')})",
                "reproduction": f"intent=load_view role={row.get('role')} model={row.get('model')} status={row.get('status')} trace_id={row.get('trace_id')}",
                "root_cause": f"load_view 对系统模型返回 {row.get('status')} / {row.get('error_code') or 'ok'}",
                "change_points": [
                    "addons/smart_core/handlers/load_view.py",
                    "addons/smart_core/controllers/intent_dispatcher.py",
                ],
                "acceptance": "系统模型访问统一返回 403 + PERMISSION_DENIED。",
            }
        )
        index += 1
        if index > 60:
            break

    for risk in acl_csv_risks:
        backlog.append(
            {
                "id": f"FX-{index:02d}",
                "severity": risk.get("severity"),
                "title": f"system model ACL policy risk: {risk.get('model')}",
                "reproduction": f"{risk.get('source')}#{risk.get('id')} group={risk.get('group_xmlid')}",
                "root_cause": "ir.model.access.csv 暴露系统模型 read 权限",
                "change_points": [
                    risk.get("source"),
                    "addons/smart_construction_core/security/sc_groups.xml",
                ],
                "acceptance": "系统模型 ACL 仅管理员可读，业务角色经受控 intent 访问。",
            }
        )
        index += 1
        if index > 80:
            break

    if len(backlog) < 20:
        for pad in range(len(backlog) + 1, 21):
            backlog.append(
                {
                    "id": f"FX-{pad:02d}",
                    "severity": "low",
                    "title": "evidence gap follow-up",
                    "reproduction": "补齐 role-scene trace 与运行态样本后复测",
                    "root_cause": "当前轮无足量失败项，转为预防性治理任务",
                    "change_points": ["scripts/verify/release_capability_audit.py"],
                    "acceptance": "下一轮审计形成稳定趋势并保持无新增高危项。",
                }
            )

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    backlog = sorted(backlog, key=lambda item: (severity_rank.get(str(item.get("severity")), 9), str(item.get("id"))))
    return backlog[:20]


def _write_markdown_report(path: Path, report: dict, backlog: list[dict]) -> None:
    lines = [
        "# Release Capability Report",
        "",
        f"- status: {'PASS' if report.get('ok') else 'FAIL'}",
        f"- generated_at: {report.get('generated_at')}",
        f"- roles: pm / finance / executive",
        f"- journey_failures: {report['summary'].get('journey_failed_steps')}",
        f"- scene_audit_count: {report['summary'].get('scene_audit_count')}",
        f"- scene_open_failed_checks: {report['summary'].get('scene_open_failed_checks')}",
        f"- capability_key_count: {report['summary'].get('capability_key_count')}",
        f"- acl_runtime_high_risk: {report['summary'].get('acl_runtime_high_risk_count')}",
        f"- acl_csv_risk_count: {report['summary'].get('acl_csv_risk_count')}",
        f"- top20_backlog_count: {len(backlog)}",
        "",
        "## Role Journeys",
        "",
    ]
    for role_row in report.get("role_journeys") or []:
        lines.append(
            f"- {role_row.get('role')}: pass={role_row.get('passed_count')}/{role_row.get('journey_count')} "
            f"fail={role_row.get('failed_count')} login={role_row.get('login')}"
        )
        for step in (role_row.get("intent_trace_chain") or [])[:8]:
            lines.append(
                f"  - step={step.get('step')} intent={step.get('intent')} status={step.get('status')} "
                f"ok={step.get('ok')} trace_id={step.get('trace_id') or '-'} reason={step.get('reason') or '-'}"
            )
        for fp in (role_row.get("failure_points") or [])[:4]:
            lines.append(
                f"  - failure step={fp.get('step')} intent={fp.get('intent')} status={fp.get('status')} "
                f"trace_id={fp.get('trace_id') or '-'} reason={fp.get('reason') or fp.get('error_code') or '-'}"
            )

    lines.extend(
        [
            "",
            "## Scene Openability",
            "",
            f"- source: {report.get('scene_selection_source')}",
            f"- selected_scene_count: {report['scene_openability']['summary'].get('scene_count')}",
            f"- openability_ratio: {report['scene_openability']['summary'].get('openability_ratio')}",
        ]
    )
    for row in (report["scene_openability"].get("rows") or [])[:30]:
        pm = (row.get("roles") or {}).get("pm") or {}
        fi = (row.get("roles") or {}).get("finance") or {}
        ex = (row.get("roles") or {}).get("executive") or {}
        lines.append(
            f"- {row.get('scene_key')}: pm={pm.get('status')}/{pm.get('reason')} "
            f"finance={fi.get('status')}/{fi.get('reason')} executive={ex.get('status')}/{ex.get('reason')}"
        )

    lines.extend(["", "## ACL Risk Scan", ""])
    lines.append(f"- runtime_acl_high_risk_count: {report['summary'].get('acl_runtime_high_risk_count')}")
    lines.append(f"- runtime_acl_medium_risk_count: {report['summary'].get('acl_runtime_medium_risk_count')}")
    lines.append(f"- acl_csv_risk_count: {report['summary'].get('acl_csv_risk_count')}")
    for row in (report.get("acl_runtime_probe") or [])[:20]:
        lines.append(
            f"- runtime role={row.get('role')} model={row.get('model')} status={row.get('status')} "
            f"risk={row.get('risk_level')} code={row.get('error_code') or '-'} trace_id={row.get('trace_id') or '-'}"
        )
    for risk in (report.get("acl_csv_risks") or [])[:20]:
        lines.append(
            f"- acl source={risk.get('source')} model={risk.get('model')} group={risk.get('group_xmlid')} severity={risk.get('severity')}"
        )

    lines.extend(["", "## Top-20 Fix Backlog", ""])
    for item in backlog:
        lines.append(f"- {item.get('id')} [{item.get('severity')}] {item.get('title')}")
        lines.append(f"  - reproduction: {item.get('reproduction')}")
        lines.append(f"  - root_cause: {item.get('root_cause')}")
        lines.append(f"  - change_points: {', '.join(item.get('change_points') or [])}")
        lines.append(f"  - acceptance: {item.get('acceptance')}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixtures = _load_role_fixtures()
    fixtures = [fx for fx in fixtures if fx.role in {"pm", "finance", "executive"}]
    if len(fixtures) < 3:
        print("[release_capability_audit] FAIL")
        print("missing required fixtures for roles: pm/finance/executive")
        return 1

    roles, login_failures = _collect_runtime_scenes_by_role(intent_url, db_name, fixtures)
    role_journeys = _run_role_journeys(intent_url, roles)
    capability_matrix = _build_capability_coverage_matrix(roles)
    selected_scene_keys, usage_scores, scene_selection_source = _build_scene_candidates(roles, top_n=30)
    scene_openability = _audit_scene_openability(intent_url, roles, selected_scene_keys)
    acl_csv_risks = _scan_acl_csv_risks()
    acl_runtime_probe = _runtime_acl_probe(intent_url, roles)

    high_acl_runtime = [row for row in acl_runtime_probe if row.get("risk_level") == "high"]
    medium_acl_runtime = [row for row in acl_runtime_probe if row.get("risk_level") == "medium"]
    journey_failed_steps = sum(int(row.get("failed_count") or 0) for row in role_journeys)

    baseline_scene_count = 0
    payload = _load_json(SCENE_MATRIX_JSON)
    baseline_scene_count = int(((payload.get("summary") or {}).get("scene_count") or 0))
    backend_report = _load_json(BACKEND_REPORT_JSON)
    backend_failed = int(((backend_report.get("summary") or {}).get("failed_check_count") or 0))

    report = {
        "ok": journey_failed_steps == 0 and len(high_acl_runtime) == 0,
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "summary": {
            "role_count": 3,
            "journey_count": 9,
            "journey_failed_steps": journey_failed_steps,
            "scene_audit_count": len(selected_scene_keys),
            "scene_open_failed_checks": int(scene_openability["summary"].get("failed_open_checks") or 0),
            "capability_key_count": int(capability_matrix["summary"].get("capability_key_count") or 0),
            "acl_runtime_high_risk_count": len(high_acl_runtime),
            "acl_runtime_medium_risk_count": len(medium_acl_runtime),
            "acl_csv_risk_count": len(acl_csv_risks),
            "login_failure_count": len(login_failures),
            "baseline_scene_count": baseline_scene_count,
            "backend_architecture_failed_checks": backend_failed,
        },
        "role_journeys": role_journeys,
        "runtime_capability_matrix": capability_matrix,
        "scene_selection_source": scene_selection_source,
        "scene_usage_scores": usage_scores,
        "scene_openability": scene_openability,
        "acl_runtime_probe": acl_runtime_probe,
        "acl_csv_risks": acl_csv_risks,
        "login_failures": login_failures,
    }

    backlog = _build_top20_backlog(role_journeys, scene_openability, acl_csv_risks, acl_runtime_probe)
    backlog_payload = {
        "ok": True,
        "summary": {
            "count": len(backlog),
            "high": len([x for x in backlog if x.get("severity") == "high"]),
            "medium": len([x for x in backlog if x.get("severity") == "medium"]),
            "low": len([x for x in backlog if x.get("severity") == "low"]),
        },
        "items": backlog,
    }

    artifacts_root = _resolve_artifacts_dir()
    backend_dir = artifacts_root / "backend"
    backend_dir.mkdir(parents=True, exist_ok=True)
    report_json = backend_dir / "release_capability_report.json"
    report_md = backend_dir / "release_capability_report.md"
    backlog_json = backend_dir / "release_capability_top20_fix_backlog.json"
    backlog_md = backend_dir / "release_capability_top20_fix_backlog.md"

    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    backlog_json.write_text(json.dumps(backlog_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_markdown_report(report_md, report, backlog)

    backlog_lines = [
        "# Top-20 Fix Backlog",
        "",
        f"- total: {backlog_payload['summary']['count']}",
        f"- high: {backlog_payload['summary']['high']}",
        f"- medium: {backlog_payload['summary']['medium']}",
        f"- low: {backlog_payload['summary']['low']}",
        "",
    ]
    for item in backlog:
        backlog_lines.append(f"- {item['id']} [{item['severity']}] {item['title']}")
        backlog_lines.append(f"  - reproduction: {item['reproduction']}")
        backlog_lines.append(f"  - root_cause: {item['root_cause']}")
        backlog_lines.append(f"  - change_points: {', '.join(item.get('change_points') or [])}")
        backlog_lines.append(f"  - acceptance: {item['acceptance']}")
    backlog_md.write_text("\n".join(backlog_lines) + "\n", encoding="utf-8")

    print(str(report_json))
    print(str(report_md))
    print(str(backlog_json))
    print(str(backlog_md))
    if not report.get("ok"):
        print("[release_capability_audit] FAIL")
        return 1
    print("[release_capability_audit] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

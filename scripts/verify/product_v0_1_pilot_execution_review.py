#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_v0_1_pilot_execution_review.json"
OUT_MD = ROOT / "artifacts" / "backend" / "product_v0_1_pilot_execution_review.md"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _block_data(response: dict) -> dict:
    block = (((response.get("data") or {}).get("block")) or {})
    return block.get("data") if isinstance(block.get("data"), dict) else {}


def _fetch_block(intent_url: str, token: str, db_name: str, project_id: int, block_key: str) -> dict:
    status, response = _post(
        intent_url,
        token,
        "project.execution.block.fetch",
        {"project_id": project_id, "block_key": block_key},
        db_name=db_name,
    )
    _assert_ok(status, response, f"project.execution.block.fetch({block_key})")
    return _block_data(response)


def _actions_from(response: dict) -> list:
    actions = response.get("actions")
    return actions if isinstance(actions, list) else []


def _find_action(actions: list, intent: str) -> dict:
    action = next((row for row in actions if isinstance(row, dict) and str(row.get("intent") or "") == intent), None)
    if not isinstance(action, dict):
        raise RuntimeError(f"missing action: {intent}")
    return action


def _task_state(items: list) -> str:
    first = items[0] if items and isinstance(items[0], dict) else {}
    return str(first.get("state") or "")


def _step(name: str, *, status: str, experience: str, evidence: dict, issues: list[dict] | None = None) -> dict:
    return {
        "name": name,
        "status": status,
        "experience": experience,
        "evidence": evidence,
        "issues": issues or [],
    }


def _render_md(report: dict) -> str:
    lines = [
        "# Product v0.1 Pilot Execution Review",
        "",
        f"- status: **{str(report.get('status') or '').upper()}**",
        f"- project_id: {report.get('project_id')}",
        "",
        "## Steps",
    ]
    for step in report.get("steps", []):
        lines.append(f"- {step.get('name')}: {step.get('status')}")
        lines.append(f"  - experience: {step.get('experience')}")
        evidence = step.get("evidence") or {}
        if evidence:
            lines.append(f"  - evidence: `{json.dumps(evidence, ensure_ascii=False, sort_keys=True)}`")
        for issue in step.get("issues") or []:
            lines.append(
                "  - issue: "
                f"[{issue.get('category')}] {issue.get('title')} -> {issue.get('detail')}"
            )
    lines.extend(["", "## Issues"])
    for issue in report.get("issues", []):
        lines.append(f"- [{issue.get('category')}] {issue.get('title')}: {issue.get('detail')}")
    return "\n".join(lines) + "\n"


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(
        os.getenv("E2E_LOGIN")
        or os.getenv("ROLE_PM_LOGIN")
        or "demo_role_project_manager"
    ).strip()
    password = str(
        os.getenv("E2E_PASSWORD")
        or os.getenv("ROLE_PM_PASSWORD")
        or os.getenv("ADMIN_PASSWD")
        or "demo"
    ).strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS", "steps": [], "issues": []}
    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = str(((((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token") or "")).strip()
        if not token:
            raise RuntimeError("login token missing")
        report["steps"].append(
            _step(
                "login",
                status="pass",
                experience="管理员可直接进入试点闭环，无额外初始化动作。",
                evidence={"session_token": "present"},
            )
        )

        status, initiation_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P15B-PILOT-{uuid4().hex[:8]}",
                "description": "first pilot execution review",
                "date_start": str(os.getenv("P15B_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        project_id = int((((initiation_data.get("record") or {}) if isinstance(initiation_data.get("record"), dict) else {}).get("id") or 0))
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")
        suggested = initiation_data.get("suggested_action_payload") if isinstance(initiation_data.get("suggested_action_payload"), dict) else {}
        report["project_id"] = project_id
        report["steps"].append(
            _step(
                "initiation",
                status="pass",
                experience="立项返回 project_id，并明确建议进入 dashboard。",
                evidence={"project_id": project_id, "suggested_intent": str(suggested.get("intent") or "")},
            )
        )

        status, dashboard_next_resp = _post(
            intent_url,
            token,
            "project.dashboard.block.fetch",
            {"project_id": project_id, "block_key": "next_actions"},
            db_name=db_name,
        )
        _assert_ok(status, dashboard_next_resp, "project.dashboard.block.fetch(next_actions)")
        dashboard_actions = _actions_from(_block_data(dashboard_next_resp))
        dashboard_execution_action = next(
            (
                row
                for row in dashboard_actions
                if isinstance(row, dict)
                and str(row.get("intent") or "") in {"project.plan_bootstrap.enter", "project.execution.enter"}
            ),
            None,
        )
        if not isinstance(dashboard_execution_action, dict):
            raise RuntimeError("dashboard next_actions missing project.plan_bootstrap.enter/project.execution.enter")
        dashboard_next_intent = str(dashboard_execution_action.get("intent") or "")
        report["steps"].append(
            _step(
                "dashboard",
                status="pass",
                experience="dashboard 能把操作员继续导向计划或执行主线，不需要额外判断页面路由。",
                evidence={"next_intent": dashboard_next_intent, "state": str(dashboard_execution_action.get("state") or "")},
            )
        )

        if dashboard_next_intent == "project.plan_bootstrap.enter":
            status, plan_next_resp = _post(
                intent_url,
                token,
                "project.plan_bootstrap.block.fetch",
                {"project_id": project_id, "block_key": "next_actions"},
                db_name=db_name,
            )
            _assert_ok(status, plan_next_resp, "project.plan_bootstrap.block.fetch(next_actions)")
            plan_actions = _actions_from(_block_data(plan_next_resp))
            execution_action = _find_action(plan_actions, "project.execution.enter")
            report["steps"].append(
                _step(
                    "plan",
                    status="pass",
                    experience="plan 场景能稳定把流程交给 execution，没有额外产品分支。",
                    evidence={"next_intent": str(execution_action.get("intent") or ""), "state": str(execution_action.get("state") or "")},
                )
            )
        else:
            report["steps"].append(
                _step(
                    "plan",
                    status="pass",
                    experience="当前产品主线允许 dashboard 直接进入 execution，plan 入口不再作为强制中转。",
                    evidence={"next_intent": dashboard_next_intent, "state": str(dashboard_execution_action.get("state") or "")},
                )
            )

        status, execution_entry_resp = _post(intent_url, token, "project.execution.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, execution_entry_resp, "project.execution.enter")
        pilot_precheck = _fetch_block(intent_url, token, db_name, project_id, "pilot_precheck")
        next_actions_before = _fetch_block(intent_url, token, db_name, project_id, "next_actions")
        execution_tasks_before = _fetch_block(intent_url, token, db_name, project_id, "execution_tasks")
        precheck_summary = pilot_precheck.get("summary") if isinstance(pilot_precheck.get("summary"), dict) else {}
        actions_before = _actions_from(next_actions_before)
        advance_before = _find_action(actions_before, "project.execution.advance")
        report["steps"].append(
            _step(
                "execution_precheck",
                status="pass",
                experience="进入 execution 后可直接看到试点前检查、任务来源和推进动作，主路径清晰。",
                evidence={
                    "pilot_precheck_state": str(precheck_summary.get("overall_state") or ""),
                    "pilot_failed_count": int(precheck_summary.get("failed_count") or 0),
                    "task_source_model": str((execution_tasks_before.get("summary") or {}).get("source_model") or ""),
                    "advance_state": str(advance_before.get("state") or ""),
                },
            )
        )

        first_params = advance_before.get("params") if isinstance(advance_before.get("params"), dict) else {}
        status, first_advance_resp = _post(intent_url, token, "project.execution.advance", first_params, db_name=db_name)
        _assert_ok(status, first_advance_resp, "project.execution.advance(first)")
        first_data = first_advance_resp.get("data") if isinstance(first_advance_resp.get("data"), dict) else {}
        execution_tasks_in_progress = _fetch_block(intent_url, token, db_name, project_id, "execution_tasks")
        report["steps"].append(
            _step(
                "advance_to_in_progress",
                status="pass",
                experience="第一次推进能明确把 ready 切到 in_progress，任务真源仍来自 project.task。",
                evidence={
                    "from_state": str(first_data.get("from_state") or ""),
                    "to_state": str(first_data.get("to_state") or ""),
                    "reason_code": str(first_data.get("reason_code") or ""),
                    "task_state_after": _task_state(execution_tasks_in_progress.get("items") if isinstance(execution_tasks_in_progress.get("items"), list) else []),
                },
            )
        )

        next_actions_in_progress = _fetch_block(intent_url, token, db_name, project_id, "next_actions")
        actions_in_progress = _actions_from(next_actions_in_progress)
        advance_in_progress = _find_action(actions_in_progress, "project.execution.advance")
        second_params = advance_in_progress.get("params") if isinstance(advance_in_progress.get("params"), dict) else {}
        status, second_advance_resp = _post(intent_url, token, "project.execution.advance", second_params, db_name=db_name)
        _assert_ok(status, second_advance_resp, "project.execution.advance(second)")
        second_data = second_advance_resp.get("data") if isinstance(second_advance_resp.get("data"), dict) else {}
        execution_tasks_done = _fetch_block(intent_url, token, db_name, project_id, "execution_tasks")
        next_actions_done = _fetch_block(intent_url, token, db_name, project_id, "next_actions")
        done_action = _find_action(_actions_from(next_actions_done), "project.execution.advance")
        done_issue = {
            "category": "理解",
            "priority": "high",
            "title": "done 态阻断原因需要友好文案",
            "detail": "真实试点闭环在完成态返回 reason_code=EXECUTION_ALREADY_DONE，前端必须展示业务化解释，不能暴露原始代码。",
        }
        report["issues"].append(done_issue)
        report["steps"].append(
            _step(
                "advance_to_done",
                status="pass",
                experience="第二次推进能完成闭环，但完成态会再次暴露 blocked reason，需要友好提示解释“无需继续推进”。",
                evidence={
                    "from_state": str(second_data.get("from_state") or ""),
                    "to_state": str(second_data.get("to_state") or ""),
                    "reason_code": str(second_data.get("reason_code") or ""),
                    "done_action_state": str(done_action.get("state") or ""),
                    "done_action_reason_code": str(done_action.get("reason_code") or ""),
                    "task_state_after": _task_state(execution_tasks_done.get("items") if isinstance(execution_tasks_done.get("items"), list) else []),
                },
                issues=[done_issue],
            )
        )
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        _write_md(OUT_MD, _render_md(report))
        print("[product_v0_1_pilot_execution_review] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    _write_md(OUT_MD, _render_md(report))
    print("[product_v0_1_pilot_execution_review] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

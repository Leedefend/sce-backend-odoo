#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "project_journey_trace_archive.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "project_journey_trace_archive.md"
ROLE_MATRIX_PATH = ROOT / "artifacts" / "backend" / "delivery_journey_role_matrix_report.json"
TASK_ACTION_PATH = ROOT / "artifacts" / "backend" / "project_task_action_smoke.json"

REQUIRED_PM_SCENES = ["projects.intake", "projects.list", "projects.ledger", "projects.dashboard"]
REQUIRED_ACTION_STEPS = [
    "project.execution.enter",
    "project.execution.block.fetch.execution_tasks",
    "project.execution.block.fetch.next_actions",
    "project.execution.advance",
    "project.execution.block.fetch.execution_tasks.after_advance",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _task_step_index(task_action: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in _as_list(task_action.get("steps")):
        if not isinstance(row, dict):
            continue
        step = _text(row.get("step"))
        if step:
            out[step] = row
    return out


def _build_trace_chain(pm_row: dict, task_action: dict) -> list[dict]:
    chain: list[dict] = []
    for scene in _as_list(pm_row.get("required_scenes")):
        scene_key = _text(scene)
        if not scene_key:
            continue
        chain.append(
            {
                "kind": "scene_visibility",
                "scene_key": scene_key,
                "ok": scene_key not in set(_as_list(pm_row.get("missing_scenes"))),
                "source": ROLE_MATRIX_PATH.relative_to(ROOT).as_posix(),
            }
        )

    step_index = _task_step_index(task_action)
    for step_name in REQUIRED_ACTION_STEPS:
        row = step_index.get(step_name, {})
        chain.append(
            {
                "kind": "action_step",
                "step": step_name,
                "ok": bool(row.get("ok")),
                "reason_code": _text(row.get("reason_code")),
                "result": _text(row.get("result")),
                "from_state": _text(row.get("from_state")),
                "to_state": _text(row.get("to_state")),
                "source": TASK_ACTION_PATH.relative_to(ROOT).as_posix(),
            }
        )
    return chain


def _to_markdown(payload: dict) -> str:
    lines = [
        "# Project Journey Trace Archive",
        "",
        f"- generated_at_utc: {payload.get('generated_at_utc', '')}",
        f"- ok: {payload.get('ok')}",
        f"- role: `{payload.get('role', '')}`",
        f"- project_id: `{payload.get('project_id', '')}`",
        f"- task_id: `{payload.get('task_id', '')}`",
        "",
        "## Trace Chain",
        "",
        "| kind | key | ok | detail |",
        "|---|---|---|---|",
    ]
    for row in _as_list(payload.get("trace_chain")):
        if not isinstance(row, dict):
            continue
        key = _text(row.get("scene_key") or row.get("step"))
        detail = _text(row.get("reason_code") or row.get("result") or row.get("to_state"))
        lines.append(f"| {_text(row.get('kind'))} | `{key}` | {bool(row.get('ok'))} | `{detail}` |")
    errors = _as_list(payload.get("errors"))
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in errors)
    return "\n".join(lines) + "\n"


def main() -> int:
    errors: list[str] = []
    role_matrix = _load_json(ROLE_MATRIX_PATH)
    task_action = _load_json(TASK_ACTION_PATH)

    if not role_matrix:
        errors.append(f"missing_role_matrix:{ROLE_MATRIX_PATH.relative_to(ROOT).as_posix()}")
    if not task_action:
        errors.append(f"missing_task_action:{TASK_ACTION_PATH.relative_to(ROOT).as_posix()}")
    if role_matrix and not bool(role_matrix.get("ok")):
        errors.append("role_matrix_not_ok")
    if task_action and not bool(task_action.get("ok")):
        errors.append("project_task_action_not_ok")

    journeys = role_matrix.get("journeys") if isinstance(role_matrix.get("journeys"), dict) else {}
    pm_row = journeys.get("pm") if isinstance(journeys.get("pm"), dict) else {}
    observed_pm_scenes = set(_as_list(pm_row.get("required_scenes")))
    missing_required_pm_scenes = [scene for scene in REQUIRED_PM_SCENES if scene not in observed_pm_scenes]
    if missing_required_pm_scenes:
        errors.append(f"pm_required_scene_missing:{missing_required_pm_scenes}")
    if _as_list(pm_row.get("missing_scenes")):
        errors.append(f"pm_role_matrix_missing_scenes:{pm_row.get('missing_scenes')}")

    step_index = _task_step_index(task_action)
    missing_action_steps = [step for step in REQUIRED_ACTION_STEPS if step not in step_index]
    if missing_action_steps:
        errors.append(f"project_action_step_missing:{missing_action_steps}")
    failed_action_steps = [step for step in REQUIRED_ACTION_STEPS if step in step_index and not bool(step_index[step].get("ok"))]
    if failed_action_steps:
        errors.append(f"project_action_step_failed:{failed_action_steps}")

    advance = step_index.get("project.execution.advance", {})
    if advance and _text(advance.get("result")) != "success":
        errors.append("project_execution_advance_not_success")

    trace_chain = _build_trace_chain(pm_row, task_action)
    payload = {
        "generated_at_utc": _utc_now(),
        "ok": not errors,
        "archive": "project_journey_trace_archive",
        "role": "pm",
        "project_id": task_action.get("project_id") or 0,
        "task_id": task_action.get("task_id") or 0,
        "trace_chain": trace_chain,
        "summary": {
            "scene_step_count": len([row for row in trace_chain if row.get("kind") == "scene_visibility"]),
            "action_step_count": len([row for row in trace_chain if row.get("kind") == "action_step"]),
            "required_scene_count": len(REQUIRED_PM_SCENES),
            "required_action_step_count": len(REQUIRED_ACTION_STEPS),
        },
        "sources": {
            "role_matrix": ROLE_MATRIX_PATH.relative_to(ROOT).as_posix(),
            "project_task_action": TASK_ACTION_PATH.relative_to(ROOT).as_posix(),
        },
        "reports": {
            "json": REPORT_JSON.relative_to(ROOT).as_posix(),
            "md": REPORT_MD.relative_to(ROOT).as_posix(),
        },
        "errors": errors,
    }
    _write(REPORT_JSON, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    _write(REPORT_MD, _to_markdown(payload))

    print(REPORT_JSON)
    print(REPORT_MD)
    if errors:
        print("[project_journey_trace_archive] FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    print("[project_journey_trace_archive] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

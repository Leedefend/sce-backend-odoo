#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "backend_task_family_compat_gap_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "backend_task_family_compat_gap_guard.md"


def _load_mapping() -> dict[str, str]:
    path = ROOT / "addons/smart_construction_scene/services/capability_scene_targets.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if not isinstance(target, ast.Name) or target.id != "CAPABILITY_ENTRY_SCENE_MAP":
            continue
        if node.value is None:
            break
        mapping = ast.literal_eval(node.value)
        if not isinstance(mapping, dict):
            break
        return {str(k): str(v) for k, v in mapping.items()}
    raise RuntimeError("CAPABILITY_ENTRY_SCENE_MAP missing")


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    try:
        mapping = _load_mapping()
        task_list_target = mapping.get("project.task.list", "")
        task_board_target = mapping.get("project.task.board", "")
        errors: list[str] = []
        known_gaps: list[str] = []

        if task_list_target != "task.center":
            errors.append(f"project.task.list must remain task.center, got {task_list_target or '(missing)'}")
        if task_board_target != "task.board":
            errors.append(f"project.task.board must resolve to dedicated compat carrier task.board, got {task_board_target or '(missing)'}")

        if not errors:
            known_gaps.append(
                "project.task.board now resolves to dedicated compat carrier task.board, which remains authority-light and still has no native menu/action authority"
            )

        report = {
            "status": "PASS" if not errors else "FAIL",
            "task_list_target": task_list_target,
            "task_board_target": task_board_target,
            "known_gaps": known_gaps,
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Backend Task Family Compat Gap Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- task_list_target: {report.get('task_list_target', '') or '(missing)'}",
        f"- task_board_target: {report.get('task_board_target', '') or '(missing)'}",
    ]
    known_gaps = report.get("known_gaps") if isinstance(report.get("known_gaps"), list) else []
    if known_gaps:
        lines.extend(["", "## Known Gaps"])
        lines.extend([f"- {item}" for item in known_gaps])
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[backend_task_family_compat_gap_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[backend_task_family_compat_gap_guard] PASS")
    print(f"known_gaps={len(known_gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

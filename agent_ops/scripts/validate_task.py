#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from common import load_task


REQUIRED_FIELDS = [
    "task_id",
    "title",
    "type",
    "status",
    "priority",
    "goal",
    "user_visible_outcome",
    "scope",
    "architecture",
    "acceptance",
    "risk",
    "stop_conditions",
    "deliverables",
    "rollback",
]


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate an iteration task contract.")
    parser.add_argument("task", help="Task yaml path")
    args = parser.parse_args()

    task_path, task = load_task(args.task)
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in task:
            errors.append(f"missing field: {field}")

    if not _non_empty_string(task.get("task_id")):
        errors.append("task_id must be a non-empty string")
    if not _non_empty_string(task.get("title")):
        errors.append("title must be a non-empty string")
    if not _non_empty_string(task.get("goal")):
        errors.append("goal must be a non-empty string")

    outcomes = task.get("user_visible_outcome")
    if not isinstance(outcomes, list) or not outcomes or not all(_non_empty_string(item) for item in outcomes):
        errors.append("user_visible_outcome must be a non-empty string list")

    scope = task.get("scope", {})
    if not isinstance(scope, dict):
        errors.append("scope must be a mapping")
    else:
        allowed = scope.get("allowed_paths")
        forbidden = scope.get("forbidden_paths")
        if not isinstance(allowed, list) or not allowed or not all(_non_empty_string(item) for item in allowed):
            errors.append("scope.allowed_paths must be a non-empty string list")
        if not isinstance(forbidden, list) or not all(_non_empty_string(item) for item in forbidden):
            errors.append("scope.forbidden_paths must be a string list")

    architecture = task.get("architecture", {})
    if not isinstance(architecture, dict):
        errors.append("architecture must be a mapping")
    else:
        for field in ("layer_target", "module", "reason"):
            if not _non_empty_string(architecture.get(field)):
                errors.append(f"architecture.{field} must be a non-empty string")

    acceptance = task.get("acceptance", {})
    commands = acceptance.get("commands") if isinstance(acceptance, dict) else None
    if not isinstance(commands, list) or not commands or not all(_non_empty_string(item) for item in commands):
        errors.append("acceptance.commands must be a non-empty string list")

    risk = task.get("risk", {})
    if not isinstance(risk, dict):
        errors.append("risk must be a mapping")
    elif not _non_empty_string(risk.get("level")):
        errors.append("risk.level must be a non-empty string")

    if not isinstance(task.get("deliverables"), list) or not task["deliverables"]:
        errors.append("deliverables must be a non-empty list")
    if not isinstance(task.get("rollback"), list) or not task["rollback"]:
        errors.append("rollback must be a non-empty list")
    if not isinstance(task.get("depends_on"), list):
        errors.append("depends_on must be a list")

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "task": str(Path(task_path)),
        "task_id": task.get("task_id"),
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

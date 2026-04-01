#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

import yaml

from common import ROOT, load_task, repo_relative


STAGE_SUFFIXES = ("A", "B", "C")
STAGE_MODES = {"A": "scan", "B": "screen", "C": "verify"}
STAGE_TITLES = {
    "A": "Scan candidates in low-cost mode",
    "B": "Screen scanned candidates in low-cost mode",
    "C": "Verify screened result in low-cost mode",
}
STAGE_GOALS = {
    "A": "Run a bounded scan stage that finds candidate families without concluding.",
    "B": "Run a bounded screen stage that classifies the scan output without rescanning.",
    "C": "Run a bounded verify stage that validates the screened result without new reasoning.",
}
DEFAULT_LIMITS = {
    "max_files": 12,
    "max_candidates": 15,
    "max_output_lines": 80,
    "forbid_repo_wide_scan": True,
    "use_new_session": True,
    "carry_long_context": False,
}


def _stage_task_path(task_path: Path, suffix: str) -> Path:
    return task_path.with_name(f"{task_path.stem}-{suffix}{task_path.suffix}")


def _stage_acceptance(stage_path: Path, suffix: str) -> list[str]:
    relative = repo_relative(stage_path)
    commands = [f"python3 agent_ops/scripts/validate_task.py {relative}"]
    if suffix == "C":
        commands.append(f"bash agent_ops/scripts/run_low_cost_iteration.sh {stage_path.stem[:-2]}")
    return commands


def build_stage_task(base_task: dict, stage_path: Path, suffix: str) -> dict:
    stage_task = deepcopy(base_task)
    stage_task["task_id"] = f"{base_task['task_id']}-{suffix}"
    stage_task["title"] = f"{base_task['title']} [{STAGE_TITLES[suffix]}]"
    stage_task["mode"] = STAGE_MODES[suffix]
    stage_task["goal"] = f"{base_task['goal'].strip()} {STAGE_GOALS[suffix]}"
    stage_task["limits"] = deepcopy(base_task.get("limits", DEFAULT_LIMITS))
    for key, value in DEFAULT_LIMITS.items():
        stage_task["limits"].setdefault(key, value)

    change_rules = list(base_task.get("change_rules", []))
    change_rules.extend(
        [
            f"single-stage-only: {STAGE_MODES[suffix]}",
            "must use a new session for this stage",
            "must not carry long context from previous stages",
        ]
    )
    if suffix == "A":
        change_rules.append("scan must not conclude")
    elif suffix == "B":
        change_rules.append("screen must not rescan the repository")
    else:
        change_rules.append("verify must not introduce new reasoning")
    stage_task["change_rules"] = change_rules

    context = deepcopy(base_task.get("context", {}))
    context["use_new_session"] = True
    context["carry_long_context"] = False
    context["base_task_id"] = base_task["task_id"]
    if suffix == "B":
        context["input_from"] = f"{base_task['task_id']}-A"
    elif suffix == "C":
        context["input_from"] = f"{base_task['task_id']}-B"
    stage_task["context"] = context

    deliverables = list(base_task.get("deliverables", []))
    deliverables.append(f"structured {STAGE_MODES[suffix]} output for {stage_task['task_id']}")
    stage_task["deliverables"] = deliverables

    stop_conditions = list(base_task.get("stop_conditions", []))
    stop_conditions.extend(
        [
            "low_cost_limit_exceeded",
            "forbidden_path_touched",
            "stage_boundary_broken",
        ]
    )
    if suffix == "A":
        stop_conditions.append("scan_attempts_to_conclude")
    elif suffix == "B":
        stop_conditions.append("screen_attempts_repo_rescan")
    else:
        stop_conditions.append("verify_attempts_new_reasoning")
    stage_task["stop_conditions"] = stop_conditions

    rollback = list(base_task.get("rollback", []))
    rollback.append(f"git restore {repo_relative(stage_path)}")
    stage_task["rollback"] = rollback

    stage_task["acceptance"] = {"commands": _stage_acceptance(stage_path, suffix)}
    if suffix == "A":
        stage_task["depends_on"] = list(base_task.get("depends_on", []))
    elif suffix == "B":
        stage_task["depends_on"] = [f"{base_task['task_id']}-A"]
    else:
        stage_task["depends_on"] = [f"{base_task['task_id']}-B"]

    return stage_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a task into low-cost A/B/C stage tasks.")
    parser.add_argument("task", help="Base task yaml path")
    args = parser.parse_args()

    task_path, base_task = load_task(args.task)
    created: list[str] = []

    for suffix in STAGE_SUFFIXES:
        stage_path = _stage_task_path(task_path, suffix)
        stage_task = build_stage_task(base_task, stage_path, suffix)
        stage_path.parent.mkdir(parents=True, exist_ok=True)
        with stage_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(stage_task, handle, allow_unicode=True, sort_keys=False)
        created.append(repo_relative(stage_path))

    print(
        yaml.safe_dump(
            {
                "status": "PASS",
                "base_task": repo_relative(task_path),
                "created": created,
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

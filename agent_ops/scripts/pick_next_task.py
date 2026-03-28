#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import AGENT_OPS, TASK_RESULTS_DIR, load_json, load_yaml


def resolve_task_path(task_id: str) -> Path:
    candidate = AGENT_OPS / "tasks" / f"{task_id}.yaml"
    if not candidate.exists():
        raise FileNotFoundError(f"missing task file for {task_id}: {candidate}")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick the next executable task from an active queue.")
    parser.add_argument("queue", nargs="?", default="agent_ops/queue/active_queue.yaml", help="Queue yaml path")
    parser.add_argument("--state", default="agent_ops/state/queue_state.json", help="Queue state json path")
    args = parser.parse_args()

    queue = load_yaml(Path(args.queue))
    state = load_json(Path(args.state), default={}) or {}
    completed = set(state.get("completed", []))
    blocked = set(state.get("blocked", []))

    for task_id in queue.get("tasks", []):
        if task_id in completed or task_id in blocked:
            continue
        task = load_yaml(resolve_task_path(task_id))
        deps = set(task.get("depends_on", []))
        if not deps.issubset(completed):
            continue
        if task.get("risk", {}).get("manual_approval_required"):
            continue
        previous = load_json(TASK_RESULTS_DIR / f"{task_id}.json", default={}) or {}
        if previous.get("classification") == "PASS":
            continue
        payload = {"status": "PASS", "task_id": task_id, "task_path": f"agent_ops/tasks/{task_id}.yaml"}
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print(json.dumps({"status": "FAIL", "reason": "no_runnable_task"}, ensure_ascii=True, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

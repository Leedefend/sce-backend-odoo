#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import ROOT, load_json, load_yaml, task_result_path, dump_json


def normalize_classification(result: dict) -> str:
    classification = result.get("classification", "FAIL")
    if isinstance(classification, dict):
        return classification.get("classification", "FAIL")
    return classification


def rebuild_state_from_results(queue: dict) -> dict:
    stop_on = set(queue.get("stop_on", ["FAIL", "PASS_WITH_RISK"]))
    state = {
        "blocked": [],
        "completed": [],
        "history": [],
        "last_event": None,
        "queue_status": "idle",
    }

    any_result = False
    for task_id in queue.get("tasks", []):
        result = load_json(task_result_path(task_id), default={}) or {}
        classification = normalize_classification(result)
        if not result or classification == "FAIL" and "classification" not in result:
            break

        any_result = True
        triggered_stop_conditions = []
        if isinstance(result.get("classification"), dict):
            triggered_stop_conditions = result["classification"].get("triggered_stop_conditions", [])
        exit_code = 0 if classification == "PASS" else 1
        state["history"].append(
            {
                "task_id": task_id,
                "classification": classification,
                "exit_code": exit_code,
                "triggered_stop_conditions": triggered_stop_conditions,
            }
        )

        if classification == "PASS":
            state["completed"].append(task_id)
            state["last_event"] = {
                "type": "task_finished",
                "task_id": task_id,
                "classification": classification,
                "triggered_stop_conditions": triggered_stop_conditions,
            }
            continue

        state["blocked"].append(task_id)
        state["queue_status"] = "stopped" if classification in stop_on else "idle"
        state["last_event"] = {
            "type": "queue_stopped" if classification in stop_on else "task_finished",
            "task_id": task_id,
            "classification": classification,
            "triggered_stop_conditions": triggered_stop_conditions,
        }
        return state

    if any_result and len(state["completed"]) == len(queue.get("tasks", [])):
        state["queue_status"] = "completed"
        state["last_event"] = {"type": "queue_already_completed"}
    elif any_result:
        state["queue_status"] = "idle"
        state["last_event"] = {"type": "queue_exhausted", "detail": "waiting_for_next_task_result"}
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run queue iterations until stop conditions are met.")
    parser.add_argument("queue", nargs="?", default="agent_ops/queue/active_queue.yaml", help="Queue yaml path")
    parser.add_argument("--state", default="agent_ops/state/queue_state.json", help="Queue state json path")
    args = parser.parse_args()

    queue_path = Path(args.queue)
    state_path = Path(args.state)
    queue = load_yaml(queue_path)
    state = rebuild_state_from_results(queue)
    if all_tasks_completed(queue, state):
        state["queue_status"] = "completed"
        state["last_event"] = {"type": "queue_already_completed"}
        dump_json(state_path, state)
        print(json.dumps({"status": "PASS", "reason": "queue_already_completed"}, ensure_ascii=True, indent=2))
        return 0
    state["queue_status"] = "running"
    dump_json(state_path, state)
    stop_on = set(queue.get("stop_on", ["FAIL", "PASS_WITH_RISK"]))

    while True:
        pick = subprocess.run(
            ["python3", "agent_ops/scripts/pick_next_task.py", str(queue_path), "--state", str(state_path)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        if pick.returncode != 0:
            all_tasks = set(queue.get("tasks", []))
            completed_tasks = set(state.get("completed", []))
            state["queue_status"] = "completed" if all_tasks and all_tasks.issubset(completed_tasks) else "idle"
            state["last_event"] = {
                "type": "queue_exhausted",
                "detail": pick.stdout.strip() or pick.stderr.strip(),
            }
            dump_json(state_path, state)
            print(pick.stdout.strip() or pick.stderr.strip())
            break

        picked = json.loads(pick.stdout)
        task_id = picked["task_id"]
        task_path = picked["task_path"]
        iteration = subprocess.run(
            ["bash", "agent_ops/scripts/run_iteration.sh", task_path],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
        )

        result = load_json(task_result_path(task_id), default={}) or {}
        classification = normalize_classification(result)
        triggered_stop_conditions = []
        if isinstance(result.get("classification"), dict):
            triggered_stop_conditions = result["classification"].get("triggered_stop_conditions", [])
        state.setdefault("history", []).append(
            {
                "task_id": task_id,
                "classification": classification,
                "exit_code": iteration.returncode,
                "triggered_stop_conditions": triggered_stop_conditions,
            }
        )
        if classification == "PASS":
            state.setdefault("completed", []).append(task_id)
        else:
            state.setdefault("blocked", []).append(task_id)
        state["last_event"] = {
            "type": "task_finished",
            "task_id": task_id,
            "classification": classification,
            "triggered_stop_conditions": triggered_stop_conditions,
        }
        dump_json(state_path, state)

        print(json.dumps({"task_id": task_id, "classification": classification}, ensure_ascii=True, indent=2))
        if classification in stop_on:
            state["queue_status"] = "stopped"
            state["last_event"] = {
                "type": "queue_stopped",
                "task_id": task_id,
                "classification": classification,
                "triggered_stop_conditions": triggered_stop_conditions,
            }
            dump_json(state_path, state)
            return 1 if classification == "FAIL" else 0

    dump_json(state_path, state)
    return 0


def all_tasks_completed(queue: dict, state: dict) -> bool:
    tasks = set(queue.get("tasks", []))
    completed = set(state.get("completed", []))
    return bool(tasks) and tasks.issubset(completed)


if __name__ == "__main__":
    raise SystemExit(main())

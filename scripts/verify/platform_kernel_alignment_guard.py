#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import fnmatch

import yaml


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "agent_ops/policies/architecture_reference_policy.yaml"
QUEUE_PATH = ROOT / "agent_ops/queue/platform_kernel_alignment_batch_1.yaml"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _task_path(task_id: str) -> Path:
    return ROOT / "agent_ops" / "tasks" / f"{task_id}.yaml"


def _patterns_overlap(left: str, right: str) -> bool:
    left_text = str(left or "").strip()
    right_text = str(right or "").strip()
    if not left_text or not right_text:
        return False

    left_root = left_text.split("/", 1)[0]
    right_root = right_text.split("/", 1)[0]
    if left_root != right_root:
        return False

    left_base = left_text.replace("**", "").rstrip("*")
    right_base = right_text.replace("**", "").rstrip("*")
    return (
        fnmatch.fnmatch(left_text, right_text)
        or fnmatch.fnmatch(right_text, left_text)
        or (left_base and right_base and (left_base.startswith(right_base) or right_base.startswith(left_base)))
    )


def _check_required_documents(policy: dict) -> list[str]:
    missing = []
    for rel_path in policy.get("required_documents", []):
        if not (ROOT / rel_path).exists():
            missing.append(rel_path)
    return missing


def _check_prompt_references() -> list[str]:
    missing = []
    required_patterns = {
        ROOT / "AGENTS.md": ["execution_baseline_v1.md", "Module Ownership", "Kernel or Scenario"],
        ROOT / "agent_ops/prompts/planner.md": ["execution_baseline_v1.md", "Module Ownership", "Kernel or Scenario"],
        ROOT / "agent_ops/prompts/implementer.md": ["execution_baseline_v1.md", "kernel"],
    }
    for path, patterns in required_patterns.items():
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern not in text:
                missing.append(f"{path.relative_to(ROOT)}::{pattern}")
    return missing


def _check_queue_tasks(policy: dict) -> list[str]:
    queue = _load_yaml(QUEUE_PATH)
    forbidden = policy.get("forbidden_alignment_paths", [])
    violations = []
    for task_id in queue.get("tasks", []):
        task = _load_yaml(_task_path(task_id))
        allowed_paths = ((task.get("scope") or {}).get("allowed_paths") or [])
        for allowed_path in allowed_paths:
            if any(_patterns_overlap(str(allowed_path), str(forbidden_path)) for forbidden_path in forbidden):
                violations.append(f"{task_id}:{allowed_path}")
    return violations


def main() -> int:
    policy = _load_yaml(POLICY_PATH)
    missing_documents = _check_required_documents(policy)
    missing_references = _check_prompt_references()
    queue_violations = _check_queue_tasks(policy)

    passed = not missing_documents and not missing_references and not queue_violations
    payload = {
        "status": "PASS" if passed else "FAIL",
        "missing_documents": missing_documents,
        "missing_prompt_references": missing_references,
        "queue_high_risk_path_violations": queue_violations,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

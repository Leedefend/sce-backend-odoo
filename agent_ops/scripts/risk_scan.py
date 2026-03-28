#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json

from diff_parser import get_changed_files, get_diff_stat, get_full_diff
from pattern_matcher import match_paths, match_patterns
from risk_rules_loader import load_rules

RUNTIME_ARTIFACT_PATTERNS = [
    "agent_ops/reports/**",
    "agent_ops/state/run_iteration.lock",
    "agent_ops/state/last_run.json",
    "agent_ops/state/queue_state.json",
    "agent_ops/state/fail_queue_state.json",
    "agent_ops/state/platform_kernel_refactor_prep_queue_state.json",
    "agent_ops/state/iteration_cursor.json",
    "agent_ops/state/task_results/**",
]


def is_runtime_artifact(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in RUNTIME_ARTIFACT_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repo-level git diff against risk rules.")
    parser.parse_args()

    rules = load_rules()
    watchlist = rules["watchlist"]
    dirty_baseline = rules["dirty_baseline"]
    high_risk = rules["high_risk"]
    stop_policy = rules["stop_conditions"]

    raw_changed = get_changed_files()
    raw_changed = [path for path in raw_changed if not is_runtime_artifact(path)]
    baseline_paths = set(dirty_baseline.get("known_dirty_paths", []))
    baseline_hits = [path for path in raw_changed if path in baseline_paths]
    changed = [path for path in raw_changed if path not in baseline_paths]
    thresholds = stop_policy.get("thresholds", {})
    diff_summary = {
        "files": len(changed),
        "added_lines": 0,
        "removed_lines": 0,
    }

    critical_hits = match_paths(changed, watchlist.get("critical_paths", []))
    high_risk_hits = match_paths(changed, high_risk.get("manual_stop_patterns", []))

    matched_rules: list[str] = []
    stop_required = False
    sensitive_pattern_hits: list[str] = []

    if critical_hits:
        matched_rules.append("critical_path")
        stop_required = True
    if high_risk_hits:
        matched_rules.append("high_risk_pattern_matched")
        stop_required = True
    if sensitive_pattern_hits:
        matched_rules.append("sensitive_pattern")

    if diff_summary["files"] > int(thresholds.get("max_changed_files", 12)):
        matched_rules.append("too_many_files_changed")
        stop_required = True
    if not stop_required and changed:
        diff_summary = get_diff_stat(changed)
        if (
            diff_summary["added_lines"] > int(thresholds.get("max_added_lines", 400))
            or diff_summary["removed_lines"] > int(thresholds.get("max_removed_lines", 200))
        ):
            matched_rules.append("diff_too_large")
            stop_required = True

    if not stop_required and changed:
        diff_text = get_full_diff(changed)
        sensitive_pattern_hits = match_patterns(diff_text, watchlist.get("sensitive_patterns", []))
        if sensitive_pattern_hits:
            matched_rules.append("sensitive_pattern")

    if stop_required:
        risk_level = "high"
    elif matched_rules or sensitive_pattern_hits:
        risk_level = "medium"
    else:
        risk_level = "low"

    payload = {
        "status": "PASS" if not stop_required else "FAIL",
        "risk_level": risk_level,
        "stop_required": stop_required,
        "matched_rules": matched_rules,
        "raw_changed_files": raw_changed,
        "baseline_hits": baseline_hits,
        "changed_files": changed,
        "critical_hits": critical_hits,
        "high_risk_hits": high_risk_hits,
        "sensitive_pattern_hits": sensitive_pattern_hits,
        "diff_summary": diff_summary,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if not stop_required else 1


if __name__ == "__main__":
    raise SystemExit(main())

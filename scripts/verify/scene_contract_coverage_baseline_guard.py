#!/usr/bin/env python3
"""Baseline guard for scene_contract_coverage_brief artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "scene_contract_coverage_brief.json"
BASELINE_JSON = ROOT / "scripts/verify/baselines/scene_contract_coverage_guard_baseline.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[scene_contract_coverage_baseline_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report = _load_json(REPORT_JSON)
    if not report:
        print("[scene_contract_coverage_baseline_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    topology = report.get("topology") if isinstance(report.get("topology"), dict) else {}
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []
    layer_counts = metrics.get("intent_layer_counts") if isinstance(metrics.get("intent_layer_counts"), dict) else {}

    errors: list[str] = []

    if bool(baseline.get("require_ok_true", True)) and not bool(report.get("ok")):
        errors.append("report.ok must be true under baseline policy")
    max_issues_count = int(baseline.get("max_issues_count", 0) or 0)
    if len(issues) > max_issues_count:
        errors.append(f"issues count must be <= {max_issues_count}, got {len(issues)}")

    min_scene_count = int(baseline.get("min_scene_count_actual", 1) or 1)
    if int(metrics.get("scene_count_actual") or 0) < min_scene_count:
        errors.append(f"metrics.scene_count_actual must be >= {min_scene_count}")

    min_intent_count = int(baseline.get("min_intent_count_actual", 1) or 1)
    if int(metrics.get("intent_count_actual") or 0) < min_intent_count:
        errors.append(f"metrics.intent_count_actual must be >= {min_intent_count}")

    min_renderable_ratio = float(baseline.get("min_renderable_ratio", 0.0) or 0.0)
    if float(metrics.get("renderable_ratio") or 0.0) < min_renderable_ratio:
        errors.append(f"metrics.renderable_ratio must be >= {min_renderable_ratio}")

    min_interaction_ready_ratio = float(baseline.get("min_interaction_ready_ratio", 0.0) or 0.0)
    if float(metrics.get("interaction_ready_ratio") or 0.0) < min_interaction_ready_ratio:
        errors.append(f"metrics.interaction_ready_ratio must be >= {min_interaction_ready_ratio}")

    required_layers = baseline.get("required_intent_layers") if isinstance(baseline.get("required_intent_layers"), list) else []
    for layer in required_layers:
        key = str(layer).strip()
        if not key:
            continue
        if int(layer_counts.get(key) or 0) <= 0:
            errors.append(f"metrics.intent_layer_counts.{key} must be > 0")

    required_topology = (
        baseline.get("required_topology_keys")
        if isinstance(baseline.get("required_topology_keys"), dict)
        else {}
    )
    for section, keys in required_topology.items():
        section_key = str(section).strip()
        if not section_key:
            continue
        data = topology.get(section_key) if isinstance(topology.get(section_key), dict) else {}
        if not data:
            errors.append(f"topology.{section_key} must be non-empty object")
            continue
        expect_keys = keys if isinstance(keys, list) else []
        for raw_key in expect_keys:
            sub_key = str(raw_key).strip()
            if not sub_key:
                continue
            if int(data.get(sub_key) or 0) <= 0:
                errors.append(f"topology.{section_key}.{sub_key} must be > 0")

    if errors:
        print("[scene_contract_coverage_baseline_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[scene_contract_coverage_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

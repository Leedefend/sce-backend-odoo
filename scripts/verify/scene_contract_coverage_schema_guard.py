#!/usr/bin/env python3
"""Schema guard for scene_contract_coverage_brief artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "scene_contract_coverage_brief.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(REPORT_JSON)
    if not payload:
        print("[scene_contract_coverage_schema_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []

    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    if not isinstance(payload.get("generated_at"), str) or not str(payload.get("generated_at")).strip():
        errors.append("generated_at must be non-empty string")

    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("inputs must be object")
        inputs = {}
    if not isinstance(inputs.get("scene_catalog"), str) or not str(inputs.get("scene_catalog")).strip():
        errors.append("inputs.scene_catalog must be non-empty string")
    if not isinstance(inputs.get("intent_catalog_enriched"), str) or not str(inputs.get("intent_catalog_enriched")).strip():
        errors.append("inputs.intent_catalog_enriched must be non-empty string")

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be object")
        metrics = {}
    int_keys = (
        "scene_count_declared",
        "scene_count_actual",
        "intent_count_declared",
        "intent_count_actual",
        "layout_kind_count",
        "target_type_count",
        "intents_with_smoke_make_target",
        "write_intent_count",
        "etag_enabled_intent_count",
    )
    for key in int_keys:
        if not isinstance(metrics.get(key), int):
            errors.append(f"metrics.{key} must be int")
    for key in ("renderable_ratio", "interaction_ready_ratio"):
        if not isinstance(metrics.get(key), (int, float)):
            errors.append(f"metrics.{key} must be number")

    layer_counts = metrics.get("intent_layer_counts")
    if not isinstance(layer_counts, dict):
        errors.append("metrics.intent_layer_counts must be object")
        layer_counts = {}
    for key in ("core", "domain", "governance", "other"):
        if not isinstance(layer_counts.get(key), int):
            errors.append(f"metrics.intent_layer_counts.{key} must be int")

    topology = payload.get("topology")
    if not isinstance(topology, dict):
        errors.append("topology must be object")
        topology = {}
    for key in ("layout_kind_counts", "target_type_counts"):
        section = topology.get(key)
        if not isinstance(section, dict):
            errors.append(f"topology.{key} must be object")
            continue
        for sub_key, value in section.items():
            if not isinstance(sub_key, str):
                errors.append(f"topology.{key} keys must be string")
            if not isinstance(value, int):
                errors.append(f"topology.{key}.{sub_key} must be int")

    issues = payload.get("issues")
    if not isinstance(issues, list):
        errors.append("issues must be list")
    else:
        for idx, item in enumerate(issues):
            if not isinstance(item, str):
                errors.append(f"issues[{idx}] must be string")

    if errors:
        print("[scene_contract_coverage_schema_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[scene_contract_coverage_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Guard the Phase 1 Lite semantic adapter mapping inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "version",
    "status",
    "targetContract",
    "contractVersion",
    "activeTopLevelKeys",
    "sourceSurfaces",
    "mappings",
    "deferredSurfaces",
    "forbiddenActionFields",
    "phase1StopConditions",
    "nextBatchReadiness",
}

LITE_TOP_LEVEL = {
    "pageInfo",
    "layoutContract",
    "statusContract",
    "actionContract",
    "dataContract",
    "meta",
}

REQUIRED_AREAS = {"pageInfo", "layout", "status", "action", "data", "patch", "meta"}

REQUIRED_SOURCE_SURFACES = {
    "ui_contract",
    "native_view_projection",
    "semantic_page",
    "view_parser",
    "page_assembler",
    "contract_governance",
    "api_onchange",
    "x2many_commands",
    "scene_contract_v1",
    "page_orchestration_v1",
}

FORBIDDEN_TOKENS = {
    "runtimeContract",
    "componentRegistry",
    "capabilities",
    "selectorStatus",
    "dependencyGraph",
    "dataSource",
    "stream",
    "subscription",
    "consistency",
    "collaboration",
    "aiEnvelope",
    "actionType",
    "chainAction",
    "conditionBranch",
    "workflowDsl",
    "jsonLogic",
    "script",
    "function",
    "eval",
    "expression",
    "loop",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def as_text_set(rows: Any, key: str) -> set[str]:
    if not isinstance(rows, list):
        return set()
    out: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            value = str(row.get(key) or "").strip()
            if value:
                out.add(value)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    payload = load_json(args.mapping)
    if not isinstance(payload, dict):
        errors.append("mapping inventory must be object")
    else:
        missing = REQUIRED_TOP_LEVEL - set(payload)
        if missing:
            errors.append(f"mapping inventory missing top-level keys: {sorted(missing)}")

        if payload.get("contractVersion") != "2.0.0":
            errors.append("contractVersion must be 2.0.0")
        if set(payload.get("activeTopLevelKeys") or []) != LITE_TOP_LEVEL:
            errors.append("activeTopLevelKeys must match Lite top-level shape")

        sources = as_text_set(payload.get("sourceSurfaces"), "key")
        missing_sources = REQUIRED_SOURCE_SURFACES - sources
        if missing_sources:
            errors.append(f"missing source surfaces: {sorted(missing_sources)}")

        mappings = payload.get("mappings")
        if not isinstance(mappings, list) or len(mappings) < 12:
            errors.append("mappings must contain at least 12 rows")
        else:
            areas = {str(row.get("area") or "").strip() for row in mappings if isinstance(row, dict)}
            missing_areas = REQUIRED_AREAS - areas
            if missing_areas:
                errors.append(f"missing mapping areas: {sorted(missing_areas)}")
            for index, row in enumerate(mappings):
                if not isinstance(row, dict):
                    errors.append(f"mappings[{index}] must be object")
                    continue
                for key in ("area", "sourceSurface", "sourcePath", "targetContract", "targetPath", "owner", "rule", "confidence", "phase"):
                    if not str(row.get(key) or "").strip():
                        errors.append(f"mappings[{index}] missing {key}")
                if row.get("sourceSurface") not in sources:
                    errors.append(f"mappings[{index}] sourceSurface not declared: {row.get('sourceSurface')}")
                if row.get("owner") != "semantic_adapter":
                    errors.append(f"mappings[{index}] owner must be semantic_adapter")
                if row.get("phase") != "phase_1":
                    errors.append(f"mappings[{index}] phase must be phase_1")

        forbidden_actions = set(payload.get("forbiddenActionFields") or [])
        for required in ("actionType", "chainAction", "conditionBranch", "loop", "workflow", "jsonLogic"):
            if required not in forbidden_actions:
                errors.append(f"forbiddenActionFields missing {required}")

        readiness = payload.get("nextBatchReadiness")
        if not isinstance(readiness, dict) or readiness.get("ready") is not True:
            errors.append("nextBatchReadiness.ready must be true")
        else:
            must_not_touch = set(readiness.get("mustNotTouch") or [])
            for key in ("login", "system.init", "ui.contract default output", "frontend runtime", "runtimeContract"):
                if key not in must_not_touch:
                    errors.append(f"nextBatchReadiness.mustNotTouch missing {key}")

        for node_path, node in walk(payload):
            if not isinstance(node, dict):
                continue
            for key in node:
                if key in FORBIDDEN_TOKENS and key not in {"deferredSurfaces", "forbiddenActionFields"}:
                    errors.append(f"forbidden active key {key!r} at {node_path}")

    if errors:
        print("Unified Semantic Page Contract Lite mapping guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Unified Semantic Page Contract Lite mapping guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

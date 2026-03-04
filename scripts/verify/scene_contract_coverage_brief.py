#!/usr/bin/env python3
"""Build a readable coverage brief from scene/intent contract exports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCENE_CATALOG = ROOT / "docs/contract/exports/scene_catalog.json"
INTENT_CATALOG_ENRICHED = ROOT / "docs/contract/exports/intent_catalog_enriched.json"
OUT_JSON = ROOT / "artifacts/scene_contract_coverage_brief.json"
OUT_MD = ROOT / "artifacts/scene_contract_coverage_brief.md"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _to_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return default


def _to_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return float(text)
        except Exception:
            return default
    return default


def main() -> int:
    scene = _load_json(SCENE_CATALOG)
    intent = _load_json(INTENT_CATALOG_ENRICHED)
    errors: list[str] = []

    if not scene:
        errors.append(f"missing_or_invalid: {SCENE_CATALOG.as_posix()}")
    if not intent:
        errors.append(f"missing_or_invalid: {INTENT_CATALOG_ENRICHED.as_posix()}")

    scenes = scene.get("scenes") if isinstance(scene.get("scenes"), list) else []
    intents = intent.get("intents") if isinstance(intent.get("intents"), list) else []

    scene_count_declared = _to_int(scene.get("scene_count"))
    scene_count_actual = len(scenes)
    if scene_count_declared <= 0:
        errors.append("scene_count must be > 0")
    if scene_count_actual <= 0:
        errors.append("scenes[] must be non-empty")

    intent_count_declared = _to_int(intent.get("intent_count"))
    intent_count_actual = len(intents)
    if intent_count_declared <= 0:
        errors.append("intent_count must be > 0")
    if intent_count_actual <= 0:
        errors.append("intents[] must be non-empty")

    renderability = scene.get("renderability") if isinstance(scene.get("renderability"), dict) else {}
    renderable_ratio = _to_float(renderability.get("renderable_ratio"), 0.0)
    interaction_ready_ratio = _to_float(renderability.get("interaction_ready_ratio"), 0.0)
    if renderable_ratio < 0.0 or renderable_ratio > 1.0:
        errors.append("renderable_ratio must be in [0,1]")
    if interaction_ready_ratio < 0.0 or interaction_ready_ratio > 1.0:
        errors.append("interaction_ready_ratio must be in [0,1]")

    layout_kind_counts = scene.get("layout_kind_counts") if isinstance(scene.get("layout_kind_counts"), dict) else {}
    target_type_counts = scene.get("target_type_counts") if isinstance(scene.get("target_type_counts"), dict) else {}

    layer_counts = {"core": 0, "domain": 0, "governance": 0, "other": 0}
    with_smoke_targets = 0
    write_intents = 0
    etag_enabled_intents = 0
    for row in intents:
        if not isinstance(row, dict):
            continue
        layer = str(row.get("layer") or "").strip().lower()
        if layer in ("core", "domain", "governance"):
            layer_counts[layer] += 1
        else:
            layer_counts["other"] += 1
        if bool(row.get("has_smoke_make_target")):
            with_smoke_targets += 1
        if bool(row.get("is_write")) or bool(row.get("is_write_operation")):
            write_intents += 1
        if bool(row.get("etag_enabled")):
            etag_enabled_intents += 1

    report = {
        "ok": len(errors) == 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "scene_catalog": SCENE_CATALOG.as_posix(),
            "intent_catalog_enriched": INTENT_CATALOG_ENRICHED.as_posix(),
        },
        "metrics": {
            "scene_count_declared": scene_count_declared,
            "scene_count_actual": scene_count_actual,
            "intent_count_declared": intent_count_declared,
            "intent_count_actual": intent_count_actual,
            "renderable_ratio": renderable_ratio,
            "interaction_ready_ratio": interaction_ready_ratio,
            "layout_kind_count": len(layout_kind_counts),
            "target_type_count": len(target_type_counts),
            "intent_layer_counts": layer_counts,
            "intents_with_smoke_make_target": with_smoke_targets,
            "write_intent_count": write_intents,
            "etag_enabled_intent_count": etag_enabled_intents,
        },
        "topology": {
            "layout_kind_counts": layout_kind_counts,
            "target_type_counts": target_type_counts,
        },
        "issues": errors,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Contract Coverage Brief",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- generated_at: {report['generated_at']}",
        f"- scene_count: {scene_count_actual} (declared={scene_count_declared})",
        f"- intent_count: {intent_count_actual} (declared={intent_count_declared})",
        f"- renderable_ratio: {renderable_ratio}",
        f"- interaction_ready_ratio: {interaction_ready_ratio}",
        f"- intents_with_smoke_make_target: {with_smoke_targets}",
        f"- write_intent_count: {write_intents}",
        f"- etag_enabled_intent_count: {etag_enabled_intents}",
        "",
        "## Intent Layers",
        "",
        f"- core: {layer_counts['core']}",
        f"- domain: {layer_counts['domain']}",
        f"- governance: {layer_counts['governance']}",
        f"- other: {layer_counts['other']}",
        "",
        "## Scene Topology",
        "",
    ]
    if layout_kind_counts:
        for key in sorted(layout_kind_counts):
            lines.append(f"- layout.{key}: {layout_kind_counts[key]}")
    else:
        lines.append("- layout: none")
    if target_type_counts:
        for key in sorted(target_type_counts):
            lines.append(f"- target.{key}: {target_type_counts[key]}")
    else:
        lines.append("- target: none")

    if errors:
        lines.extend(["", "## Issues", ""])
        lines.extend([f"- {item}" for item in errors])

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if not report["ok"]:
        print("[scene_contract_coverage_brief] FAIL")
        return 1
    print("[scene_contract_coverage_brief] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_optional(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return load_json(path)


def build_evidence(
    intent_catalog: dict,
    scene_catalog: dict,
    shape_report: dict,
    intent_surface: list[dict],
    scene_alignment_report: dict,
    business_capability_report: dict,
) -> dict:
    intents = intent_catalog.get("intents") or []
    scenes = scene_catalog.get("scenes") or []

    reason_counter: Counter[str] = Counter()
    intents_with_examples = 0
    intents_with_inferred_examples = 0
    intents_with_idempotency_window = 0
    intents_with_aliases = 0
    for item in intents:
        if not isinstance(item, dict):
            continue
        aliases = item.get("aliases")
        if isinstance(aliases, list) and aliases:
            intents_with_aliases += 1
        if item.get("has_idempotency_window") is True:
            intents_with_idempotency_window += 1
        examples = item.get("examples")
        if isinstance(examples, list) and examples:
            intents_with_examples += 1
        inferred_example = item.get("inferred_example")
        if isinstance(inferred_example, dict) and inferred_example:
            intents_with_inferred_examples += 1
        codes = item.get("observed_reason_codes")
        if isinstance(codes, list):
            for code in codes:
                if isinstance(code, str) and code.strip():
                    reason_counter[code.strip()] += 1

    evidence = {
        "intent_catalog": {
            "intent_count": len(intents),
            "with_aliases": intents_with_aliases,
            "with_idempotency_window": intents_with_idempotency_window,
            "with_examples": intents_with_examples,
            "with_inferred_examples": intents_with_inferred_examples,
            "top_observed_reason_codes": [{"reason_code": k, "count": v} for k, v in reason_counter.most_common(10)],
        },
        "scene_catalog": {
            "scene_count": len(scenes),
            "catalog_scope": ((scene_catalog.get("source") or {}).get("scene_catalog_scope") or ""),
            "layout_kind_counts": scene_catalog.get("layout_kind_counts") or {},
            "target_type_counts": scene_catalog.get("target_type_counts") or {},
            "renderability": scene_catalog.get("renderability") or {},
            "schema_version": scene_catalog.get("schema_version") or "",
            "scene_version": scene_catalog.get("scene_version") or "",
        },
        "shape_guard": {
            "ok": bool(shape_report.get("ok")),
            "error_count": len(shape_report.get("errors") or []),
            "report": "artifacts/scene_contract_shape_guard.json",
        },
        "intent_surface": {
            "rows": len(intent_surface),
        },
        "scene_runtime_alignment": {
            "ok": bool(scene_alignment_report.get("ok")),
            "catalog_scene_count": int((((scene_alignment_report.get("summary") or {}).get("catalog_scene_count")) or 0)),
            "runtime_scene_count": int((((scene_alignment_report.get("summary") or {}).get("runtime_scene_count")) or 0)),
            "catalog_runtime_ratio": float((((scene_alignment_report.get("summary") or {}).get("catalog_runtime_ratio")) or 0.0)),
            "report": "artifacts/scene_catalog_runtime_alignment_guard.json",
        },
        "business_capability_baseline": {
            "ok": bool(business_capability_report.get("ok")),
            "check_count": int((((business_capability_report.get("summary") or {}).get("check_count")) or 0)),
            "failed_check_count": int((((business_capability_report.get("summary") or {}).get("failed_check_count")) or 0)),
            "report": "artifacts/business_capability_baseline_report.json",
        },
    }
    return evidence


def to_markdown(evidence: dict) -> str:
    i = evidence["intent_catalog"]
    s = evidence["scene_catalog"]
    g = evidence["shape_guard"]
    t = evidence["intent_surface"]
    a = evidence["scene_runtime_alignment"]
    b = evidence["business_capability_baseline"]
    lines = [
        "# Phase 11.1 Contract Evidence",
        "",
        "## Contract Surface",
        f"- intents: {i['intent_count']}",
        f"- intents with aliases: {i['with_aliases']}",
        f"- intents with idempotency window: {i['with_idempotency_window']}",
        f"- intents with snapshot examples: {i['with_examples']}",
        f"- intents with inferred examples: {i['with_inferred_examples']}",
        f"- intent surface rows: {t['rows']}",
        "",
        "## Scene Orchestration",
        f"- scenes: {s['scene_count']}",
        f"- catalog_scope: {s['catalog_scope']}",
        f"- schema_version: {s['schema_version']}",
        f"- scene_version: {s['scene_version']}",
        f"- layout kinds: {json.dumps(s['layout_kind_counts'], ensure_ascii=False)}",
        f"- target types: {json.dumps(s['target_type_counts'], ensure_ascii=False)}",
        f"- renderability: {json.dumps(s.get('renderability') or {}, ensure_ascii=False)}",
        "",
        "## Runtime Alignment",
        f"- ok: {a['ok']}",
        f"- catalog_scene_count: {a['catalog_scene_count']}",
        f"- runtime_scene_count: {a['runtime_scene_count']}",
        f"- catalog_runtime_ratio: {a['catalog_runtime_ratio']}",
        f"- report: `{a['report']}`",
        "",
        "## Business Capability Baseline",
        f"- ok: {b['ok']}",
        f"- check_count: {b['check_count']}",
        f"- failed_check_count: {b['failed_check_count']}",
        f"- report: `{b['report']}`",
        "",
        "## Shape Guard",
        f"- ok: {g['ok']}",
        f"- error_count: {g['error_count']}",
        f"- report: `{g['report']}`",
        "",
        "## Top Observed reason_code",
    ]
    top_codes = i.get("top_observed_reason_codes") or []
    if not top_codes:
        lines.append("- (none)")
    else:
        for row in top_codes:
            lines.append(f"- `{row['reason_code']}`: {row['count']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export phase 11.1 contract evidence summary.")
    parser.add_argument("--intent-catalog", default="docs/contract/exports/intent_catalog.json")
    parser.add_argument("--scene-catalog", default="docs/contract/exports/scene_catalog.json")
    parser.add_argument("--shape-report", default="artifacts/scene_contract_shape_guard.json")
    parser.add_argument("--intent-surface", default="artifacts/intent_surface_report.json")
    parser.add_argument("--scene-alignment-report", default="artifacts/scene_catalog_runtime_alignment_guard.json")
    parser.add_argument("--business-capability-report", default="artifacts/business_capability_baseline_report.json")
    parser.add_argument("--output-json", default="artifacts/contract/phase11_1_contract_evidence.json")
    parser.add_argument("--output-md", default="artifacts/contract/phase11_1_contract_evidence.md")
    args = parser.parse_args()

    intent_catalog = load_json(Path(args.intent_catalog))
    scene_catalog = load_json(Path(args.scene_catalog))
    shape_report = load_json(Path(args.shape_report))
    intent_surface = load_json(Path(args.intent_surface))
    scene_alignment_report = load_json_optional(Path(args.scene_alignment_report), {})
    business_capability_report = load_json_optional(Path(args.business_capability_report), {})

    if not isinstance(intent_catalog, dict):
        raise SystemExit("intent catalog must be object")
    if not isinstance(scene_catalog, dict):
        raise SystemExit("scene catalog must be object")
    if not isinstance(shape_report, dict):
        raise SystemExit("shape report must be object")
    if not isinstance(intent_surface, list):
        raise SystemExit("intent surface report must be list")
    if not isinstance(scene_alignment_report, dict):
        raise SystemExit("scene alignment report must be object")
    if not isinstance(business_capability_report, dict):
        raise SystemExit("business capability report must be object")

    evidence = build_evidence(
        intent_catalog,
        scene_catalog,
        shape_report,
        intent_surface,
        scene_alignment_report,
        business_capability_report,
    )
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(to_markdown(evidence), encoding="utf-8")
    print(str(out_json))
    print(str(out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

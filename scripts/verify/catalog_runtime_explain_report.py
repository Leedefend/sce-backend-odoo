#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_CATALOG_JSON = ROOT / "docs" / "contract" / "exports" / "scene_catalog.json"
SCENE_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
SOURCE_RULES_JSON = ROOT / "docs" / "product" / "catalog_runtime_source_rules_v1.json"

REPORT_JSON = ROOT / "artifacts" / "backend" / "catalog_runtime_explain_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "catalog_runtime_explain_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize(value: object) -> str:
    return str(value or "").strip()


def _match_rule(scene_key: str, rule: dict, catalog_scene_keys: set[str]) -> bool:
    match_type = _normalize(rule.get("match_type")).lower()
    pattern = _normalize(rule.get("pattern"))
    key = scene_key.lower()
    p = pattern.lower()
    if match_type == "catalog_exact":
        return scene_key in catalog_scene_keys
    if match_type == "contains":
        return bool(p) and p in key
    if match_type == "prefix":
        return bool(p) and key.startswith(p)
    if match_type == "exact":
        return bool(p) and key == p
    return False


def _classify(scene_key: str, catalog_scene_keys: set[str], rules_payload: dict) -> tuple[str, str, str]:
    rules = rules_payload.get("rules") if isinstance(rules_payload.get("rules"), list) else []
    fallback = rules_payload.get("fallback") if isinstance(rules_payload.get("fallback"), dict) else {}
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if _match_rule(scene_key, rule, catalog_scene_keys):
            source = _normalize(rule.get("source")) or "fallback"
            reason = _normalize(rule.get("reason")) or "matched source rule"
            rule_id = _normalize(rule.get("id")) or "rule-unknown"
            return source, reason, rule_id
    return (
        _normalize(fallback.get("source")) or "fallback",
        _normalize(fallback.get("reason")) or "runtime fallback/legacy naming path",
        _normalize(fallback.get("rule_id")) or "fallback-default",
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    scene_catalog = _load_json(SCENE_CATALOG_JSON)
    scene_matrix = _load_json(SCENE_MATRIX_JSON)
    source_rules = _load_json(SOURCE_RULES_JSON)

    catalog_rows = scene_catalog.get("scenes") if isinstance(scene_catalog.get("scenes"), list) else []
    catalog_scene_keys = {
        str(item.get("scene_key") or "").strip()
        for item in catalog_rows
        if isinstance(item, dict) and str(item.get("scene_key") or "").strip()
    }
    runtime_scene_keys = {
        str(x or "").strip()
        for x in (scene_matrix.get("scene_keys") if isinstance(scene_matrix.get("scene_keys"), list) else [])
        if str(x or "").strip()
    }

    if not catalog_scene_keys:
        errors.append("catalog scene keys empty")
    if not runtime_scene_keys:
        errors.append("runtime scene keys empty")
    if not source_rules:
        errors.append("source rules config empty")

    rows = []
    allowed_sources = source_rules.get("allowed_sources") if isinstance(source_rules.get("allowed_sources"), list) else []
    source_counter = {str(x): 0 for x in allowed_sources if _normalize(x)}
    if not source_counter:
        source_counter = {"catalog": 0, "derived": 0, "system": 0, "fallback": 0}
    unknown_source = []
    for scene_key in sorted(runtime_scene_keys):
        source, reason, rule_id = _classify(scene_key, catalog_scene_keys, source_rules)
        if source not in source_counter:
            unknown_source.append(scene_key)
            source = "fallback"
            reason = "unknown classification fallback"
            rule_id = "fallback-unknown-source"
        source_counter[source] += 1
        rows.append({"scene_key": scene_key, "source": source, "reason": reason, "rule_id": rule_id})

    if unknown_source:
        errors.append(f"unknown_source_count={len(unknown_source)}")

    coverage_ratio = round((source_counter["catalog"] / len(runtime_scene_keys)), 6) if runtime_scene_keys else 0.0
    report = {
        "ok": len(errors) == 0,
        "summary": {
            "catalog_scene_count": len(catalog_scene_keys),
            "runtime_scene_count": len(runtime_scene_keys),
            "source_catalog_count": source_counter.get("catalog", 0),
            "source_derived_count": source_counter.get("derived", 0),
            "source_system_count": source_counter.get("system", 0),
            "source_fallback_count": source_counter.get("fallback", 0),
            "unknown_source_count": len(unknown_source),
            "catalog_runtime_coverage_ratio": coverage_ratio,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "ruleset": {
            "version": str(source_rules.get("version") or "unknown"),
            "rule_count": len(source_rules.get("rules") if isinstance(source_rules.get("rules"), list) else []),
            "allowed_sources": sorted(source_counter.keys()),
        },
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Catalog Runtime Explain Report",
        "",
        f"- catalog_scene_count: {len(catalog_scene_keys)}",
        f"- runtime_scene_count: {len(runtime_scene_keys)}",
        f"- source_catalog_count: {source_counter.get('catalog', 0)}",
        f"- source_derived_count: {source_counter.get('derived', 0)}",
        f"- source_system_count: {source_counter.get('system', 0)}",
        f"- source_fallback_count: {source_counter.get('fallback', 0)}",
        f"- unknown_source_count: {len(unknown_source)}",
        f"- catalog_runtime_coverage_ratio: {coverage_ratio}",
        f"- ruleset_version: {str(source_rules.get('version') or 'unknown')}",
        f"- error_count: {len(errors)}",
        "",
        "## Runtime Scene Source Mapping",
        "",
    ]
    for row in rows:
        lines.append(f"- {row['scene_key']} -> {row['source']} [{row['rule_id']}] ({row['reason']})")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[catalog_runtime_explain_report] FAIL")
        return 2
    print("[catalog_runtime_explain_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

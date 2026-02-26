#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_CAPABILITY_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
TAXONOMY_JSON = ROOT / "docs" / "product" / "scene_domain_taxonomy_v1.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
REPORT_JSON_ALIAS = ROOT / "artifacts" / "backend" / "scene_domain_map.json"
REPORT_MD = ROOT / "docs" / "product" / "scene_compression_model_v1.md"

PKG_SUFFIX_RE = re.compile(r"__pkg\d+$")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_scene(scene_key: str) -> str:
    return PKG_SUFFIX_RE.sub("", scene_key)


def _normalize_str(value: object) -> str:
    return str(value or "").strip().lower()


def _load_taxonomy(errors: list[str]) -> dict:
    payload = _load_json(TAXONOMY_JSON)
    if not payload:
        errors.append("scene domain taxonomy is missing")
        return {}
    return payload


def _resolve_domain(scene_key: str, rules: list[dict], fallback_domain: str) -> str:
    key = scene_key.lower()
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        match_type = _normalize_str(rule.get("match_type"))
        pattern = _normalize_str(rule.get("pattern"))
        domain = _normalize_str(rule.get("domain"))
        if not pattern or not domain:
            continue
        if match_type == "prefix" and key.startswith(pattern):
            return domain
        if match_type == "contains" and pattern in key:
            return domain
        if match_type == "exact" and key == pattern:
            return domain
        if match_type == "regex":
            try:
                if re.search(pattern, key):
                    return domain
            except re.error:
                continue
    return fallback_domain


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    payload = _load_json(SCENE_CAPABILITY_MATRIX_JSON)
    scene_keys = payload.get("scene_keys") if isinstance(payload.get("scene_keys"), list) else []
    scene_keys = sorted({str(x or "").strip() for x in scene_keys if str(x or "").strip()})
    if not scene_keys:
        errors.append("scene_keys is empty")

    taxonomy = _load_taxonomy(errors)
    domain_defs = taxonomy.get("domains") if isinstance(taxonomy.get("domains"), list) else []
    rules = taxonomy.get("rules") if isinstance(taxonomy.get("rules"), list) else []
    domain_keys = {_normalize_str(item.get("key")) for item in domain_defs if isinstance(item, dict)}
    domain_keys = {x for x in domain_keys if x}
    fallback_domain = _normalize_str(taxonomy.get("fallback_domain") or "misc_domain")
    max_domain_count = int(taxonomy.get("max_domain_count") or 25)
    if not domain_keys:
        errors.append("taxonomy domain definitions are empty")
    if not rules:
        errors.append("taxonomy rules are empty")

    rows: list[dict] = []
    domain_to_scenes: dict[str, list[str]] = {}
    canonical_to_runtime: dict[str, list[str]] = {}

    for scene_key in scene_keys:
        canonical = _normalize_scene(scene_key)
        domain = _resolve_domain(canonical, rules, fallback_domain)
        rows.append(
            {
                "runtime_scene": scene_key,
                "canonical_scene": canonical,
                "domain": domain,
                "source_type": "derived_pkg" if canonical != scene_key else "catalog_or_system",
            }
        )
        domain_to_scenes.setdefault(domain, []).append(scene_key)
        canonical_to_runtime.setdefault(canonical, []).append(scene_key)

    domain_rows = []
    for domain, scenes in sorted(domain_to_scenes.items()):
        domain_rows.append(
            {
                "domain": domain,
                "runtime_scene_count": len(scenes),
                "canonical_scene_count": len({_normalize_scene(x) for x in scenes}),
                "sample_scenes": sorted(scenes)[:8],
            }
        )

    unassigned = [row["runtime_scene"] for row in rows if not row["domain"]]
    if unassigned:
        errors.append(f"unassigned_scene_count={len(unassigned)}")

    unknown_domain_rows = [row for row in rows if row["domain"] not in domain_keys]
    unknown_domain_count = len(unknown_domain_rows)
    if unknown_domain_count:
        errors.append(f"unknown_domain_count={unknown_domain_count}")
    fallback_scene_count = sum(1 for row in rows if row["domain"] == fallback_domain)
    if fallback_scene_count:
        errors.append(f"fallback_domain_scene_count={fallback_scene_count}")

    if len(domain_rows) > max_domain_count:
        errors.append(f"domain_count_exceeds_target={len(domain_rows)}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "runtime_scene_count": len(scene_keys),
            "canonical_scene_count": len(canonical_to_runtime),
            "domain_count": len(domain_rows),
            "taxonomy_domain_count": len(domain_keys),
            "unassigned_scene_count": len(unassigned),
            "unknown_domain_count": unknown_domain_count,
            "fallback_domain_scene_count": fallback_scene_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "acceptance": {
            "all_scene_assigned": len(unassigned) == 0,
            "domain_count_le_25": len(domain_rows) <= max_domain_count,
            "zero_unknown_domain": unknown_domain_count == 0,
            "zero_fallback_domain_scene": fallback_scene_count == 0,
        },
        "taxonomy": {
            "version": str(taxonomy.get("version") or "unknown"),
            "fallback_domain": fallback_domain,
            "max_domain_count": max_domain_count,
            "domains": sorted(domain_keys),
        },
        "domains": domain_rows,
        "scene_to_domain": rows,
        "unknown_domain_rows": unknown_domain_rows,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_JSON_ALIAS.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_ALIAS.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Compression Model v1",
        "",
        "- objective: compress runtime scenes into product-facing domains (<=25)",
        f"- runtime_scene_count: {len(scene_keys)}",
        f"- canonical_scene_count: {len(canonical_to_runtime)}",
        f"- domain_count: {len(domain_rows)}",
        f"- taxonomy_domain_count: {len(domain_keys)}",
        f"- unassigned_scene_count: {len(unassigned)}",
        f"- unknown_domain_count: {unknown_domain_count}",
        f"- fallback_domain_scene_count: {fallback_scene_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Acceptance",
        "",
        f"- all_scene_assigned: {'PASS' if len(unassigned) == 0 else 'FAIL'}",
        f"- domain_count_le_25: {'PASS' if len(domain_rows) <= max_domain_count else 'FAIL'}",
        f"- zero_unknown_domain: {'PASS' if unknown_domain_count == 0 else 'FAIL'}",
        f"- zero_fallback_domain_scene: {'PASS' if fallback_scene_count == 0 else 'FAIL'}",
        "",
        "## Domain Mapping",
        "",
        "| domain | runtime_scene_count | canonical_scene_count | sample_scenes |",
        "|---|---:|---:|---|",
    ]
    for row in domain_rows:
        lines.append(
            f"| {row['domain']} | {row['runtime_scene_count']} | {row['canonical_scene_count']} | "
            f"{','.join(row['sample_scenes']) if row['sample_scenes'] else '-'} |"
        )
    lines.extend(["", "## Scene -> Domain", ""])
    for row in rows:
        lines.append(f"- {row['runtime_scene']} -> {row['domain']} (canonical={row['canonical_scene']})")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print(str(REPORT_JSON_ALIAS))
    if errors:
        print("[scene_compression_model_report] FAIL")
        return 2
    print("[scene_compression_model_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

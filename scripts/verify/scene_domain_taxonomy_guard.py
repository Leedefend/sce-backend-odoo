#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_JSON = ROOT / "docs" / "product" / "scene_domain_taxonomy_v1.json"
SCENE_MAP_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "scene_domain_taxonomy_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "scene_domain_taxonomy_guard_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    taxonomy = _load(TAXONOMY_JSON)
    scene_map = _load(SCENE_MAP_JSON)
    if not taxonomy:
        errors.append("missing taxonomy")
    if not scene_map:
        errors.append("missing scene domain mapping report")

    domains = taxonomy.get("domains") if isinstance(taxonomy.get("domains"), list) else []
    rules = taxonomy.get("rules") if isinstance(taxonomy.get("rules"), list) else []
    fallback_domain = _norm(taxonomy.get("fallback_domain") or "misc_domain")
    domain_keys = {_norm(item.get("key")) for item in domains if isinstance(item, dict)}
    domain_keys = {x for x in domain_keys if x}

    if not domain_keys:
        errors.append("domain definitions empty")
    if fallback_domain in domain_keys:
        warnings.append(f"fallback_domain_in_primary_domains={fallback_domain}")

    rule_match_types = {"prefix", "contains", "exact", "regex"}
    invalid_rules = []
    dangling_rule_domains = []
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            invalid_rules.append(f"rule_{idx}:not_object")
            continue
        match_type = _norm(rule.get("match_type"))
        pattern = _norm(rule.get("pattern"))
        domain = _norm(rule.get("domain"))
        if match_type not in rule_match_types or not pattern or not domain:
            invalid_rules.append(f"rule_{idx}:invalid_fields")
        if domain and domain not in domain_keys and domain != fallback_domain:
            dangling_rule_domains.append(domain)

    if invalid_rules:
        errors.append(f"invalid_rule_count={len(invalid_rules)}")
    if dangling_rule_domains:
        errors.append(f"dangling_rule_domain_count={len(set(dangling_rule_domains))}")

    summary = scene_map.get("summary") if isinstance(scene_map.get("summary"), dict) else {}
    fallback_scene_count = int(summary.get("fallback_domain_scene_count") or 0)
    unknown_domain_count = int(summary.get("unknown_domain_count") or 0)
    if fallback_scene_count > 0:
        errors.append(f"fallback_domain_scene_count={fallback_scene_count}")
    if unknown_domain_count > 0:
        errors.append(f"unknown_domain_count={unknown_domain_count}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "domain_count": len(domain_keys),
            "rule_count": len(rules),
            "invalid_rule_count": len(invalid_rules),
            "dangling_rule_domain_count": len(set(dangling_rule_domains)),
            "fallback_domain_scene_count": fallback_scene_count,
            "unknown_domain_count": unknown_domain_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Domain Taxonomy Guard",
        "",
        f"- domain_count: {len(domain_keys)}",
        f"- rule_count: {len(rules)}",
        f"- invalid_rule_count: {len(invalid_rules)}",
        f"- dangling_rule_domain_count: {len(set(dangling_rule_domains))}",
        f"- fallback_domain_scene_count: {fallback_scene_count}",
        f"- unknown_domain_count: {unknown_domain_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[scene_domain_taxonomy_guard] FAIL")
        return 2
    print("[scene_domain_taxonomy_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

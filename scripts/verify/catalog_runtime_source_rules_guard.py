#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RULES_JSON = ROOT / "docs" / "product" / "catalog_runtime_source_rules_v1.json"
EXPLAIN_JSON = ROOT / "artifacts" / "backend" / "catalog_runtime_explain_report.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "catalog_runtime_source_rules_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "catalog_runtime_source_rules_guard_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(value: object) -> str:
    return str(value or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    rules_doc = _load(RULES_JSON)
    explain = _load(EXPLAIN_JSON)
    if not rules_doc:
        errors.append("missing source rules file")
    if not explain:
        errors.append("missing catalog_runtime_explain_report")

    allowed_sources = {_norm(x) for x in (rules_doc.get("allowed_sources") if isinstance(rules_doc.get("allowed_sources"), list) else []) if _norm(x)}
    rules = rules_doc.get("rules") if isinstance(rules_doc.get("rules"), list) else []
    fallback = rules_doc.get("fallback") if isinstance(rules_doc.get("fallback"), dict) else {}

    if not allowed_sources:
        errors.append("allowed_sources empty")
    if not rules:
        errors.append("rules empty")

    invalid_rules = []
    duplicate_rule_ids = set()
    rule_ids = set()
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            invalid_rules.append(f"rule_{idx}:not_object")
            continue
        rule_id = _norm(rule.get("id"))
        source = _norm(rule.get("source"))
        match_type = _norm(rule.get("match_type"))
        pattern = _norm(rule.get("pattern"))
        reason = _norm(rule.get("reason"))
        if not rule_id or not source or not match_type or not pattern or not reason:
            invalid_rules.append(f"rule_{idx}:missing_fields")
        if source and allowed_sources and source not in allowed_sources:
            invalid_rules.append(f"rule_{idx}:invalid_source:{source}")
        if match_type not in {"catalog_exact", "contains", "prefix", "exact", "regex"}:
            invalid_rules.append(f"rule_{idx}:invalid_match_type:{match_type}")
        if rule_id:
            if rule_id in rule_ids:
                duplicate_rule_ids.add(rule_id)
            rule_ids.add(rule_id)

    if invalid_rules:
        errors.append(f"invalid_rule_count={len(invalid_rules)}")
    if duplicate_rule_ids:
        errors.append(f"duplicate_rule_id_count={len(duplicate_rule_ids)}")

    fallback_source = _norm(fallback.get("source"))
    fallback_rule_id = _norm(fallback.get("rule_id"))
    fallback_reason = _norm(fallback.get("reason"))
    if not fallback_source or fallback_source not in allowed_sources:
        errors.append("fallback source invalid")
    if not fallback_rule_id:
        errors.append("fallback rule_id missing")
    if not fallback_reason:
        errors.append("fallback reason missing")

    summary = explain.get("summary") if isinstance(explain.get("summary"), dict) else {}
    unknown_source_count = int(summary.get("unknown_source_count") or 0)
    if unknown_source_count > 0:
        errors.append(f"unknown_source_count={unknown_source_count}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "allowed_source_count": len(allowed_sources),
            "rule_count": len(rules),
            "invalid_rule_count": len(invalid_rules),
            "duplicate_rule_id_count": len(duplicate_rule_ids),
            "unknown_source_count": unknown_source_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Catalog Runtime Source Rules Guard",
        "",
        f"- allowed_source_count: {len(allowed_sources)}",
        f"- rule_count: {len(rules)}",
        f"- invalid_rule_count: {len(invalid_rules)}",
        f"- duplicate_rule_id_count: {len(duplicate_rule_ids)}",
        f"- unknown_source_count: {unknown_source_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[catalog_runtime_source_rules_guard] FAIL")
        return 2
    print("[catalog_runtime_source_rules_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

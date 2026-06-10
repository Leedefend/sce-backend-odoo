#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "docs" / "product" / "business_capability_productization_baseline_v1.json"
PORTRAIT_JSON = ROOT / "artifacts" / "user_business_data_portrait.sc_demo.json"
OUT_JSON = ROOT / "artifacts" / "p1_business_relationship_gap_report.json"
OUT_MD = ROOT / "artifacts" / "p1_business_relationship_gap_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _family_index(portrait: dict) -> dict:
    result = {}
    for family in _as_list(portrait.get("families")):
        if isinstance(family, dict) and family.get("key"):
            result[str(family["key"])] = family
    return result


def _model_index(family: dict) -> dict:
    result = {}
    for model in _as_list(family.get("models")):
        if isinstance(model, dict) and model.get("model"):
            result[str(model["model"])] = model
    return result


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    portrait = _load_json(PORTRAIT_JSON)
    if not baseline or not portrait:
        print("[p1_business_relationship_gap_report] FAIL")
        print("missing baseline or portrait artifact")
        return 1

    portrait_by_family = _family_index(portrait)
    rows = []
    for family in _as_list(baseline.get("families")):
        if not isinstance(family, dict):
            continue
        if family.get("priority") not in ("P0", "P1"):
            continue
        if family.get("role") == "audit_evidence":
            continue
        key = str(family.get("key") or "")
        portrait_family = portrait_by_family.get(key) or {}
        models_by_name = _model_index(portrait_family)
        expected_relationships = _as_list(family.get("required_relationships"))
        primary_models = _as_list(family.get("primary_models"))
        for model_name in primary_models:
            model_row = models_by_name.get(model_name)
            if not model_row:
                rows.append(
                    {
                        "family_key": key,
                        "family_name": family.get("name"),
                        "model": model_name,
                        "record_count": 0,
                        "gap_count": 0,
                        "missing_fields": {"model_not_in_portrait": 1},
                        "severity": "critical",
                    }
                )
                continue
            record_count = _safe_int(model_row.get("record_count"), 0)
            anchor_missing = (
                model_row.get("anchor_missing")
                if isinstance(model_row.get("anchor_missing"), dict)
                else {}
            )
            missing_fields = {
                field: _safe_int(anchor_missing.get(field), 0)
                for field in expected_relationships
                if _safe_int(anchor_missing.get(field), 0) > 0
            }
            gap_count = sum(missing_fields.values())
            if gap_count <= 0:
                continue
            max_missing = max(missing_fields.values())
            if record_count and max_missing / max(record_count, 1) >= 0.5:
                severity = "critical"
            elif max_missing >= 1000:
                severity = "high"
            else:
                severity = "medium"
            rows.append(
                {
                    "family_key": key,
                    "family_name": family.get("name"),
                    "model": model_name,
                    "record_count": record_count,
                    "gap_count": gap_count,
                    "missing_fields": missing_fields,
                    "severity": severity,
                }
            )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rows = sorted(
        rows,
        key=lambda item: (severity_rank.get(item["severity"], 9), -item["gap_count"], item["family_key"], item["model"]),
    )
    report = {
        "ok": True,
        "baseline": BASELINE_JSON.relative_to(ROOT).as_posix(),
        "portrait": PORTRAIT_JSON.relative_to(ROOT).as_posix(),
        "summary": {
            "gap_model_count": len(rows),
            "critical_count": len([item for item in rows if item["severity"] == "critical"]),
            "high_count": len([item for item in rows if item["severity"] == "high"]),
            "medium_count": len([item for item in rows if item["severity"] == "medium"]),
            "total_gap_count": sum(item["gap_count"] for item in rows),
        },
        "gaps": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# P1 Business Relationship Gap Report",
        "",
        f"- gap_model_count: {report['summary']['gap_model_count']}",
        f"- critical_count: {report['summary']['critical_count']}",
        f"- high_count: {report['summary']['high_count']}",
        f"- medium_count: {report['summary']['medium_count']}",
        f"- total_gap_count: {report['summary']['total_gap_count']}",
        "",
        "## Gaps",
        "",
    ]
    for item in rows:
        fields = ", ".join(f"{key}={value}" for key, value in item["missing_fields"].items())
        lines.append(
            f"- [{item['severity']}] {item['family_name']} / {item['model']}: "
            f"records={item['record_count']}, gaps={fields}"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON.relative_to(ROOT)))
    print(str(OUT_MD.relative_to(ROOT)))
    print("[p1_business_relationship_gap_report] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

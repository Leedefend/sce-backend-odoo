#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_FILE = REPO_ROOT / "addons/smart_construction_custom/data/customer_project_dictionary_seed.xml"
REQUIRED_TYPES = {
    "project_type",
    "project_status",
    "project_stage",
    "task_type",
    "task_status",
    "cost_item",
    "payment_category",
    "settlement_category",
    "contract_category",
}

MIN_ACTIVE_RECORDS_BY_TYPE = {
    "project_type": 2,
    "project_status": 3,
    "project_stage": 3,
    "task_type": 2,
    "task_status": 3,
    "cost_item": 2,
    "payment_category": 2,
    "settlement_category": 2,
    "contract_category": 2,
}


def _parse_active_counts(xml_text: str) -> dict[str, int]:
    root = ET.fromstring(xml_text)
    counts: dict[str, int] = {}
    for record in root.findall(".//record"):
        type_value = ""
        active_value = "true"
        for field in record.findall("field"):
            field_name = str(field.attrib.get("name") or "").strip()
            field_text = str(field.text or "").strip()
            if field_name == "type":
                type_value = field_text
            elif field_name == "active":
                active_value = field_text
        if not type_value:
            continue
        if str(active_value).strip().lower() in {"0", "false", "no", "off"}:
            continue
        counts[type_value] = int(counts.get(type_value, 0)) + 1
    return counts


def main() -> None:
    if not SEED_FILE.is_file():
        raise RuntimeError(f"dictionary seed file missing: {SEED_FILE}")

    text = SEED_FILE.read_text(encoding="utf-8")
    active_counts = _parse_active_counts(text)
    found_types = set(active_counts.keys())

    missing = sorted(REQUIRED_TYPES - found_types)
    if missing:
        raise RuntimeError(f"dictionary types missing in seed: {', '.join(missing)}")

    min_missing = [
        f"{type_key}<{minimum}"
        for type_key, minimum in MIN_ACTIVE_RECORDS_BY_TYPE.items()
        if int(active_counts.get(type_key, 0)) < int(minimum)
    ]
    if min_missing:
        raise RuntimeError(
            "dictionary active records below minimum: " + ", ".join(min_missing)
        )

    record_count = sum(active_counts.values())
    if record_count < sum(MIN_ACTIVE_RECORDS_BY_TYPE.values()):
        raise RuntimeError(
            "dictionary active seed records too few: "
            f"count={record_count} required_at_least={sum(MIN_ACTIVE_RECORDS_BY_TYPE.values())}"
        )

    required_counts = {k: int(active_counts.get(k, 0)) for k in sorted(REQUIRED_TYPES)}
    print(
        "[native_business_fact_dictionary_completeness_verify] "
        f"PASS records={record_count} types={len(found_types)} required_counts={required_counts}"
    )


if __name__ == "__main__":
    main()

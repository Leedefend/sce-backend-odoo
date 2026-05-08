#!/usr/bin/env python3
"""Summarize business-fact loss scans across all restored legacy databases."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade"))
SOURCE_SPEC = os.getenv(
    "LEGACY_BUSINESS_FACT_SOURCES",
    "main:legacy-mssql-restore:LegacyDb,scbs:legacy-mssql-scbs:LegacyScbs20260417",
)
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_multi_db_business_fact_scan_summary_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "legacy_multi_db_business_fact_scan_summary_v1.md"


def parse_sources(raw: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for item in raw.split(","):
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3 or not all(parts):
            raise RuntimeError({"invalid_legacy_business_fact_source": item, "expected": "label:container:database"})
        label, container, database = parts
        sources.append({"label": label, "container": container, "database": database})
    return sources


def source_root(label: str) -> Path:
    return ARTIFACT_ROOT if label == "main" else ARTIFACT_ROOT / label


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def top_family(payload: dict[str, Any] | None) -> str | None:
    families = (((payload or {}).get("summary") or {}).get("families") or [])
    if not families:
        return None
    return families[0].get("family")


def main() -> int:
    sources = parse_sources(SOURCE_SPEC)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for source in sources:
        root = source_root(source["label"])
        full_scan_path = root / "legacy_db_full_business_fact_loss_scan_v1.json"
        family_screen_path = root / "legacy_db_remaining_business_fact_family_screen_v1.json"
        full_scan = load_json(full_scan_path)
        family_screen = load_json(family_screen_path)
        if full_scan is None:
            errors.append({"error": "missing_full_legacy_loss_scan", "source": source, "path": str(full_scan_path)})
        if family_screen is None:
            errors.append({"error": "missing_remaining_fact_family_screen", "source": source, "path": str(family_screen_path)})
        if full_scan is not None and full_scan.get("status") != "PASS":
            errors.append({"error": "full_legacy_loss_scan_failed", "source": source, "status": full_scan.get("status")})
        if family_screen is not None and family_screen.get("status") != "PASS":
            errors.append(
                {"error": "remaining_fact_family_screen_failed", "source": source, "status": family_screen.get("status")}
            )
        full_summary = (full_scan or {}).get("summary") or {}
        family_summary = (family_screen or {}).get("summary") or {}
        rows.append(
            {
                **source,
                "artifact_root": str(root),
                "full_scan_status": (full_scan or {}).get("status") or "MISSING",
                "remaining_family_status": (family_screen or {}).get("status") or "MISSING",
                "non_empty_tables": full_summary.get("non_empty_tables"),
                "candidate_tables": full_summary.get("candidate_tables"),
                "candidate_rows": full_summary.get("candidate_rows"),
                "top_candidate": ((full_summary.get("top_candidates") or [{}])[0] or {}).get("table"),
                "screened_tables": family_summary.get("screened_tables"),
                "screened_rows": family_summary.get("screened_rows"),
                "screened_active_rows": family_summary.get("screened_active_rows"),
                "top_family": top_family(family_screen),
            }
        )

    totals = {
        "source_count": len(rows),
        "non_empty_tables": sum(int(row.get("non_empty_tables") or 0) for row in rows),
        "candidate_tables": sum(int(row.get("candidate_tables") or 0) for row in rows),
        "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
        "screened_tables": sum(int(row.get("screened_tables") or 0) for row in rows),
        "screened_rows": sum(int(row.get("screened_rows") or 0) for row in rows),
        "screened_active_rows": sum(int(row.get("screened_active_rows") or 0) for row in rows),
    }
    status = "PASS" if not errors else "FAIL"
    payload = {
        "status": status,
        "mode": "legacy_multi_db_business_fact_scan_summary",
        "artifact_root": str(ARTIFACT_ROOT),
        "source_spec": SOURCE_SPEC,
        "sources": rows,
        "totals": totals,
        "errors": errors,
        "decision": "legacy_multi_db_business_fact_sources_screened" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = f"""# Legacy Multi DB Business Fact Scan Summary v1

Status: {status}

## Sources

```json
{json.dumps(rows, ensure_ascii=False, indent=2)}
```

## Totals

```json
{json.dumps(totals, ensure_ascii=False, indent=2)}
```

## Errors

```json
{json.dumps(errors, ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
    OUTPUT_REPORT.write_text(report, encoding="utf-8")
    print(
        "LEGACY_MULTI_DB_BUSINESS_FACT_SCAN_SUMMARY="
        + json.dumps(
            {
                "status": status,
                "source_count": totals["source_count"],
                "candidate_tables": totals["candidate_tables"],
                "candidate_rows": totals["candidate_rows"],
                "screened_tables": totals["screened_tables"],
                "screened_rows": totals["screened_rows"],
                "artifact_root": str(ARTIFACT_ROOT),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""No-DB screen for contract rows blocked by missing or ambiguous partner anchors."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path.cwd()
BLOCKER_CSV = REPO_ROOT / "artifacts/migration/contract_remaining_blocker_policy_screen_rows_v1.csv"
CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
COMPANY_CSV = REPO_ROOT / "tmp/raw/partner/company.csv"
SUPPLIER_CSV = REPO_ROOT / "tmp/raw/partner/supplier.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/contract_partner_anchor_recovery_screen_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/contract_partner_anchor_recovery_screen_rows_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/contract_partner_anchor_recovery_screen_report_v1.md"

OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", ("" if value is None else str(value)).replace("\u3000", " ").strip())


def norm_name(value: object) -> str:
    text = clean(value)
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", text)
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def infer_direction(row: dict[str, str]) -> tuple[str, str]:
    fbf = clean(row.get("FBF"))
    cbf = clean(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return "out", fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return "in", cbf
    return "defer", ""


def source_partner_names() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    exact: dict[str, list[str]] = defaultdict(list)
    normalized: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(COMPANY_CSV):
        name = clean(row.get("DWMC"))
        if name:
            exact[name].append("company")
            normalized[norm_name(name)].append("company")
    for row in read_csv(SUPPLIER_CSV):
        name = clean(row.get("f_SupplierName"))
        if name:
            exact[name].append("supplier")
            normalized[norm_name(name)].append("supplier")
    return exact, normalized


def recovery_route(counterparty: str, exact_sources: list[str], normalized_sources: list[str]) -> tuple[str, str]:
    if not counterparty:
        return "direction_defer_no_counterparty", "own-company direction rule could not identify counterparty text"
    sources = exact_sources or normalized_sources
    if not sources:
        return "partner_source_missing", "counterparty text is not present in legacy company/supplier source exports"
    unique_sources = sorted(set(sources))
    if len(unique_sources) == 1:
        return "partner_source_recoverable_design_candidate", "counterparty exists in one legacy partner source"
    return "partner_source_combined_source_screen", "counterparty exists across company and supplier sources"


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Contract Partner Anchor Recovery Screen v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-CONTRACT-PARTNER-ANCHOR-RECOVERY-SCREEN`

## Scope

Screen contract rows blocked by partner anchors against legacy company and
supplier source exports. This batch performs no database reads or writes.

## Result

- partner-anchor blocked contract rows: `{payload["partner_anchor_blocked_rows"]}`
- distinct counterparty texts: `{payload["distinct_counterparty_texts"]}`
- DB writes: `0`

## Recovery Routes

```json
{json.dumps(payload["recovery_route_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    for path in [BLOCKER_CSV, CONTRACT_CSV, COMPANY_CSV, SUPPLIER_CSV]:
        if not path.exists():
            raise RuntimeError({"missing_input": str(path)})

    blocker_rows = read_csv(BLOCKER_CSV)
    contracts_by_id = {clean(row.get("Id")): row for row in read_csv(CONTRACT_CSV)}
    exact_source, normalized_source = source_partner_names()

    target_rows = [row for row in blocker_rows if row.get("policy_route") == "partner_anchor_recovery_screen"]
    output_rows: list[dict[str, object]] = []
    route_counts: Counter[str] = Counter()
    counterparty_counts: Counter[str] = Counter()

    for row in target_rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        contract = contracts_by_id.get(legacy_contract_id, {})
        direction, counterparty = infer_direction(contract)
        exact_sources = exact_source.get(counterparty, [])
        normalized_sources = normalized_source.get(norm_name(counterparty), []) if counterparty else []
        route, note = recovery_route(counterparty, exact_sources, normalized_sources)
        route_counts[route] += 1
        counterparty_counts[counterparty or "<direction_defer>"] += 1
        output_rows.append(
            {
                "legacy_contract_id": legacy_contract_id,
                "legacy_project_id": row.get("legacy_project_id", ""),
                "subject": row.get("subject", ""),
                "direction": direction,
                "counterparty_text": counterparty,
                "exact_source_count": len(exact_sources),
                "normalized_source_count": len(normalized_sources),
                "source_types": "|".join(sorted(set(exact_sources or normalized_sources))),
                "recovery_route": route,
                "recovery_note": note,
            }
        )

    status = "PASS" if len(target_rows) == 197 else "FAIL"
    payload = {
        "status": status,
        "mode": "contract_partner_anchor_recovery_screen",
        "db_writes": 0,
        "partner_anchor_blocked_rows": len(target_rows),
        "distinct_counterparty_texts": len(counterparty_counts),
        "recovery_route_counts": dict(sorted(route_counts.items())),
        "top_counterparty_texts": [
            {"text": text, "rows": count}
            for text, count in counterparty_counts.most_common(20)
        ],
        "row_artifact": str(OUTPUT_CSV),
        "decision": "partner_anchor_recovery_screened" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "write_authorization": "not_granted",
        "next_step": "open no-DB partner-source recoverable design only for single-source candidates; keep source-missing rows blocked",
        "errors": [] if status == "PASS" else [{"expected_partner_anchor_blocked_rows": 197, "actual": len(target_rows)}],
    }
    write_csv(
        OUTPUT_CSV,
        [
            "legacy_contract_id",
            "legacy_project_id",
            "subject",
            "direction",
            "counterparty_text",
            "exact_source_count",
            "normalized_source_count",
            "source_types",
            "recovery_route",
            "recovery_note",
        ],
        output_rows,
    )
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "CONTRACT_PARTNER_ANCHOR_RECOVERY_SCREEN="
        + json.dumps(
            {
                "status": status,
                "partner_anchor_blocked_rows": len(target_rows),
                "recovery_route_counts": payload["recovery_route_counts"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs" / "engineering_convergence" / "test_inventory.csv"
OUTPUT = ROOT / "docs" / "engineering_convergence" / "e2e_journey_matrix.md"

JOURNEYS = [
    ("E2E-01", "Project administrator creates a project and configures members.", ("project", "member", "user_entry")),
    ("E2E-02", "Cost engineer imports BOQ.", ("boq", "import")),
    ("E2E-03", "Project manager generates WBS or tasks from BOQ.", ("task", "wbs", "work_breakdown", "boq")),
    ("E2E-04", "Commercial user creates budget and contract.", ("contract", "budget")),
    ("E2E-05", "Project user starts variation or site instruction workflow.", ("workflow", "statusbar", "evidence", "direct_acceptance")),
    ("E2E-06", "Finance user starts payment request.", ("payment_request", "payment")),
    ("E2E-07", "Finance user records receipt/payment and invoice.", ("invoice", "receipt", "finance")),
    ("E2E-08", "Settlement user creates and approves settlement.", ("settlement",)),
    ("E2E-09", "Management reviews operating dashboard.", ("summary", "dashboard", "operation")),
    ("E2E-10", "Ordinary member is blocked from unauthorized project access.", ("auth", "role", "permission", "project_legacy")),
    ("E2E-11", "System administrator adjusts role permissions.", ("role", "menu", "config", "permission")),
    ("E2E-12", "Release user upgrades and rolls back version.", ("release", "upgrade", "rollback", "full_browser")),
]


def e2e_rows() -> list[dict[str, str]]:
    with INVENTORY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row["layer"] == "e2e"]


def match_assets(rows: list[dict[str, str]], keywords: tuple[str, ...]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for row in rows:
        haystack = f"{row['entrypoint']} {row['purpose']}".lower()
        if any(keyword in haystack for keyword in keywords):
            matches.append(row)
    return matches


def status_for(matches: list[dict[str, str]]) -> str:
    if not matches:
        return "gap"
    has_browser = any("browser" in row["entrypoint"].lower() for row in matches)
    if has_browser and len(matches) >= 2:
        return "partial_to_strong"
    return "partial"


def render(rows: list[dict[str, str]]) -> str:
    lines: list[str] = [
        "# E2E Journey Matrix",
        "",
        "Generated from `test_inventory.csv` E2E-classified assets.",
        "",
        "## Summary",
        "",
        f"- E2E-classified assets: `{len(rows)}`",
    ]

    coverage = []
    for journey_id, description, keywords in JOURNEYS:
        matches = match_assets(rows, keywords)
        coverage.append((journey_id, description, keywords, matches, status_for(matches)))

    gaps = [item for item in coverage if item[4] == "gap"]
    partial = [item for item in coverage if item[4] == "partial"]
    strong = [item for item in coverage if item[4] == "partial_to_strong"]
    lines.extend(
        [
            f"- Strong or near-strong coverage: `{len(strong)}`",
            f"- Partial coverage: `{len(partial)}`",
            f"- Gaps: `{len(gaps)}`",
            "",
            "## Coverage Matrix",
            "",
            "| Journey | Status | Existing Assets | Gap to Close |",
            "| --- | --- | --- | --- |",
        ]
    )

    for journey_id, description, keywords, matches, status in coverage:
        if matches:
            assets = "<br>".join(f"`{row['entrypoint']}`" for row in matches[:8])
            if len(matches) > 8:
                assets += f"<br>`... {len(matches) - 8} more`"
        else:
            assets = "-"
        if status == "gap":
            gap = "Create fixed-data browser/API journey with screenshots, logs, request/response evidence."
        elif status == "partial":
            gap = "Confirm fixed data, role assertions, failure artifacts, and link to nightly/release gate."
        else:
            gap = "Map assertions to acceptance points and add missing business data checks if needed."
        lines.append(f"| {journey_id}: {description} | {status} | {assets} | {gap} |")

    lines.extend(
        [
            "",
            "## Required Next Actions",
            "",
            "1. Promote only mapped and repeatable scenarios into the release gate.",
            "2. Add fixed test data for each journey before counting it as strong coverage.",
            "3. Store screenshot, browser log, server log, and request/response evidence on failure.",
            "4. Keep PR smoke E2E small; run the full 12-journey matrix nightly and before release.",
        ]
    )
    return "\n".join(lines) + "\n"


def write() -> None:
    OUTPUT.write_text(render(e2e_rows()), encoding="utf-8")
    print(f"[OK] wrote {OUTPUT.relative_to(ROOT)}")


def check() -> int:
    expected = render(e2e_rows())
    if not OUTPUT.exists():
        print(f"[ERROR] missing E2E journey matrix: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if OUTPUT.read_text(encoding="utf-8") != expected:
        print(
            "[ERROR] E2E journey matrix is stale. Run: "
            "python3 scripts/ci/generate_e2e_journey_matrix.py --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] E2E journey matrix is current")
    return 0


def main(argv: list[str]) -> int:
    if "--write" in argv:
        write()
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

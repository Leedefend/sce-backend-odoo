#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs" / "engineering_convergence" / "test_inventory.csv"
SUMMARY = ROOT / "docs" / "engineering_convergence" / "test_inventory_summary.md"


def read_rows() -> list[dict[str, str]]:
    if not INVENTORY.exists():
        raise FileNotFoundError(f"missing inventory: {INVENTORY.relative_to(ROOT)}")
    with INVENTORY.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def table(counter: Counter[str], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in counter.most_common():
        lines.append(f"| {key or 'unknown'} | {value} |")
    return lines


def top_directories(rows: list[dict[str, str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        entrypoint = row["entrypoint"]
        if entrypoint.startswith("make "):
            counter["make"] += 1
            continue
        parts = entrypoint.split("/")
        if len(parts) >= 3 and parts[:3] == ["frontend", "apps", "web"]:
            counter["frontend/apps/web/scripts"] += 1
        elif len(parts) >= 2:
            counter["/".join(parts[:2])] += 1
        else:
            counter[parts[0]] += 1
    return counter


def write_summary(rows: list[dict[str, str]]) -> None:
    review_rows = [row for row in rows if row["status"] != "active"]
    unknown_runtime = [row for row in rows if row["estimated_runtime"] == "unknown"]
    long_runtime = [row for row in rows if row["estimated_runtime"] in {"10-30m", "30-60m"}]

    lines: list[str] = [
        "# Test Inventory Summary",
        "",
        "Generated from `test_inventory.csv`.",
        "",
        "## Totals",
        "",
        f"- Total assets: `{len(rows)}`",
        f"- Review queue: `{len(review_rows)}`",
        f"- Unknown runtime: `{len(unknown_runtime)}`",
        f"- Long-running assets: `{len(long_runtime)}`",
        "",
        "## By Layer",
        "",
        *table(Counter(row["layer"] for row in rows), ("Layer", "Count")),
        "",
        "## By Runtime",
        "",
        *table(Counter(row["estimated_runtime"] for row in rows), ("Runtime", "Count")),
        "",
        "## By Owner",
        "",
        *table(Counter(row["owner"] for row in rows), ("Owner", "Count")),
        "",
        "## By Directory",
        "",
        *table(top_directories(rows), ("Directory", "Count")),
        "",
        "## Review Queue",
        "",
    ]

    if review_rows:
        lines.extend(["| ID | Layer | Entrypoint | Reason |", "| --- | --- | --- | --- |"])
        for row in review_rows:
            lines.append(
                f"| {row['id']} | {row['layer']} | `{row['entrypoint']}` | status={row['status']} |"
            )
    else:
        lines.append("No non-active assets.")

    lines.extend(["", "## Unknown Runtime Assets", ""])
    if unknown_runtime:
        lines.extend(["| ID | Layer | Entrypoint |", "| --- | --- | --- |"])
        for row in unknown_runtime[:80]:
            lines.append(f"| {row['id']} | {row['layer']} | `{row['entrypoint']}` |")
        if len(unknown_runtime) > 80:
            lines.append(f"| ... | ... | {len(unknown_runtime) - 80} more |")
    else:
        lines.append("No unknown runtime assets.")

    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_summary(rows: list[dict[str, str]]) -> int:
    if not SUMMARY.exists():
        print(f"[ERROR] missing summary: {SUMMARY.relative_to(ROOT)}", file=sys.stderr)
        return 1
    before = SUMMARY.read_text(encoding="utf-8")
    write_summary(rows)
    after = SUMMARY.read_text(encoding="utf-8")
    if before != after:
        print(
            "[ERROR] test inventory summary was stale and has been regenerated. "
            "Review and commit the update.",
            file=sys.stderr,
        )
        return 1
    print(f"[OK] test inventory summary is current ({len(rows)} entries)")
    return 0


def main(argv: list[str]) -> int:
    rows = read_rows()
    if "--write" in argv:
        write_summary(rows)
        print(f"[OK] wrote {SUMMARY.relative_to(ROOT)}")
        return 0
    return check_summary(rows)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPLEXITY_REPORT = ROOT / "docs" / "engineering_convergence" / "complexity_budget_report.md"
OUTPUT = ROOT / "docs" / "engineering_convergence" / "split_plan_queue.md"

ROW_PATTERN = re.compile(r"^\| (?P<lines>\d+) \| (?P<category>[^|]+) \| `(?P<path>[^`]+)` \|$")


def owner_for(path: str) -> str:
    if path == "Makefile" or path.startswith("scripts/") or path.startswith(".github/"):
        return "DevOps owner"
    if path.startswith("frontend/"):
        return "Frontend owner"
    if path.startswith("addons/smart_core/"):
        return "Platform owner"
    if path.startswith("addons/smart_construction_core/"):
        return "Construction backend owner"
    return "Architecture owner"


def direction_for(path: str) -> str:
    if path == "Makefile":
        return "Move implementation bodies into `scripts/ci`, `scripts/verify`, or included `make/*.mk` fragments while keeping stable public targets."
    if path.endswith(".vue"):
        return "Extract composables, child panels, data adapters, and action handlers; keep the route component as orchestration shell."
    if "tests/" in path:
        return "Split fixtures, scenario builders, and assertion groups by behavior area."
    if path.endswith(".xml"):
        return "Split data/view records by product domain and manifest load order."
    if path.endswith(".sh"):
        return "Move reusable logic into small scripts and keep shell as thin entrypoint."
    if "handlers/" in path:
        return "Extract parsing, validation, assembly, and response mapping into owned services."
    if "app_config_engine" in path:
        return "Separate parser/assembler/dispatcher responsibilities and preserve backend source-of-truth boundary."
    if "models/core" in path or "models/support" in path:
        return "Extract service methods for cross-model workflow, amount, and policy logic."
    return "Define owner-specific decomposition plan before adding unrelated behavior."


def priority_for(path: str, lines: int) -> str:
    if path in {"Makefile", "frontend/apps/web/src/pages/ContractFormPage.vue", "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue"}:
        return "P0"
    if lines >= 3000 or path.startswith("addons/smart_core/"):
        return "P1"
    return "P2"


def parse_split_rows() -> list[dict[str, str | int]]:
    lines = COMPLEXITY_REPORT.read_text(encoding="utf-8").splitlines()
    in_section = False
    rows: list[dict[str, str | int]] = []
    for line in lines:
        if line == "## Split Plan Required":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        match = ROW_PATTERN.match(line)
        if not match:
            continue
        count = int(match.group("lines"))
        path = match.group("path")
        rows.append(
            {
                "lines": count,
                "category": match.group("category").strip(),
                "path": path,
                "owner": owner_for(path),
                "priority": priority_for(path, count),
                "direction": direction_for(path),
            }
        )
    return rows


def render(rows: list[dict[str, str | int]]) -> str:
    by_priority = {priority: sum(1 for row in rows if row["priority"] == priority) for priority in ("P0", "P1", "P2")}
    lines: list[str] = [
        "# Split Plan Queue",
        "",
        "Generated from `complexity_budget_report.md` split-plan-required files.",
        "",
        "## Summary",
        "",
        f"- Split-plan files: `{len(rows)}`",
        f"- P0: `{by_priority['P0']}`",
        f"- P1: `{by_priority['P1']}`",
        f"- P2: `{by_priority['P2']}`",
        "",
        "## Queue",
        "",
        "| Priority | Lines | Owner | File | Decomposition Direction |",
        "| --- | ---: | --- | --- | --- |",
    ]
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    for row in sorted(rows, key=lambda item: (priority_order[str(item["priority"])], -int(item["lines"]), str(item["path"]))):
        lines.append(
            f"| {row['priority']} | {row['lines']} | {row['owner']} | `{row['path']}` | {row['direction']} |"
        )
    lines.extend(
        [
            "",
            "## Enforcement Rule",
            "",
            "- P0 files require a split plan before accepting non-defect feature additions.",
            "- P1 files require owner review when touched.",
            "- P2 files may be handled opportunistically, but should not grow without reason.",
        ]
    )
    return "\n".join(lines) + "\n"


def write() -> None:
    OUTPUT.write_text(render(parse_split_rows()), encoding="utf-8")
    print(f"[OK] wrote {OUTPUT.relative_to(ROOT)}")


def check() -> int:
    expected = render(parse_split_rows())
    if not OUTPUT.exists():
        print(f"[ERROR] missing split plan queue: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if OUTPUT.read_text(encoding="utf-8") != expected:
        print(
            "[ERROR] split plan queue is stale. Run: "
            "python3 scripts/ci/generate_split_plan_queue.py --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] split plan queue is current")
    return 0


def main(argv: list[str]) -> int:
    if "--write" in argv:
        write()
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

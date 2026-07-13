#!/usr/bin/env python3
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "engineering_convergence" / "complexity_budget_report.md"

SCAN_ROOTS = [
    ROOT / "Makefile",
    ROOT / "addons",
    ROOT / "scripts",
    ROOT / "frontend" / "apps" / "web" / "src",
    ROOT / ".github" / "workflows",
]

EXCLUDED_PARTS = {
    "__pycache__",
    "node_modules",
    "dist",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
}


@dataclass(frozen=True)
class Budget:
    category: str
    warning: int
    split_plan: int


BUDGETS = {
    ".py": Budget("Python source", 800, 1500),
    ".js": Budget("JavaScript source", 800, 1500),
    ".cjs": Budget("JavaScript source", 800, 1500),
    ".mjs": Budget("JavaScript source", 800, 1500),
    ".ts": Budget("TypeScript source", 800, 1500),
    ".tsx": Budget("TypeScript source", 800, 1500),
    ".vue": Budget("Vue source", 800, 1500),
    ".xml": Budget("XML data/view", 1200, 2500),
    ".sh": Budget("Shell script", 250, 500),
    ".yml": Budget("YAML workflow", 300, 600),
    ".yaml": Budget("YAML workflow", 300, 600),
}

MAKEFILE_BUDGET = Budget("Makefile", 300, 600)


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not is_excluded(path):
                if path.name == "Makefile" or path.suffix in BUDGETS:
                    files.append(path)
    return sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())


def budget_for(path: Path) -> Budget | None:
    if path.name == "Makefile":
        return MAKEFILE_BUDGET
    return BUDGETS.get(path.suffix)


def line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return 0


def rows() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for path in iter_files():
        budget = budget_for(path)
        if budget is None:
            continue
        lines = line_count(path)
        if lines <= 0:
            continue
        if lines >= budget.split_plan:
            status = "split_plan_required"
        elif lines >= budget.warning:
            status = "warning"
        else:
            status = "within_budget"
        result.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "lines": lines,
                "category": budget.category,
                "warning": budget.warning,
                "split_plan": budget.split_plan,
                "status": status,
            }
        )
    return result


def render(all_rows: list[dict[str, object]]) -> str:
    warning_rows = [row for row in all_rows if row["status"] == "warning"]
    split_rows = [row for row in all_rows if row["status"] == "split_plan_required"]
    largest = sorted(all_rows, key=lambda row: int(row["lines"]), reverse=True)[:80]

    lines: list[str] = [
        "# Complexity Budget Report",
        "",
        "Generated from repository source files. This report is informational during the first convergence pass.",
        "",
        "## Summary",
        "",
        f"- Scanned files: `{len(all_rows)}`",
        f"- Files requiring split plan: `{len(split_rows)}`",
        f"- Files above warning threshold: `{len(warning_rows)}`",
        "",
        "## Split Plan Required",
        "",
    ]

    if split_rows:
        lines.extend(["| Lines | Category | File |", "| ---: | --- | --- |"])
        for row in sorted(split_rows, key=lambda item: int(item["lines"]), reverse=True):
            lines.append(f"| {row['lines']} | {row['category']} | `{row['path']}` |")
    else:
        lines.append("No files currently exceed split-plan thresholds.")

    lines.extend(["", "## Warning Threshold", ""])
    if warning_rows:
        lines.extend(["| Lines | Category | File |", "| ---: | --- | --- |"])
        for row in sorted(warning_rows, key=lambda item: int(item["lines"]), reverse=True):
            lines.append(f"| {row['lines']} | {row['category']} | `{row['path']}` |")
    else:
        lines.append("No files currently exceed warning thresholds.")

    lines.extend(["", "## Largest Files", ""])
    lines.extend(["| Lines | Status | Category | File |", "| ---: | --- | --- | --- |"])
    for row in largest:
        lines.append(f"| {row['lines']} | {row['status']} | {row['category']} | `{row['path']}` |")

    interpretation = [
        "",
        "## Interpretation",
        "",
        "- Split-plan files are allowed to remain during the first pass, but must receive an owner and decomposition direction.",
        "- New feature work should not add unrelated code to split-plan files.",
    ]
    makefile_row = next((row for row in all_rows if row["path"] == "Makefile"), None)
    if makefile_row and makefile_row["status"] == "split_plan_required":
        interpretation.append(
            "- The root `Makefile` is already beyond the split-plan threshold and should be delegated into smaller scripts/fragments over time."
        )
    elif makefile_row and makefile_row["status"] == "warning":
        interpretation.append(
            "- The root `Makefile` is below the split-plan threshold but still above the warning threshold; keep future targets in included fragments."
        )
    elif makefile_row:
        interpretation.append(
            "- The root `Makefile` is within budget; keep it as a thin variable and include entrypoint."
        )
    lines.extend(interpretation)
    return "\n".join(lines) + "\n"


def write() -> None:
    OUTPUT.write_text(render(rows()), encoding="utf-8")
    print(f"[OK] wrote {OUTPUT.relative_to(ROOT)}")


def check() -> int:
    expected = render(rows())
    if not OUTPUT.exists():
        print(f"[ERROR] missing complexity report: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if OUTPUT.read_text(encoding="utf-8") != expected:
        print(
            "[ERROR] complexity report is stale. Run: "
            "python3 scripts/ci/generate_complexity_budget_report.py --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] complexity budget report is current")
    return 0


def main(argv: list[str]) -> int:
    if "--write" in argv:
        write()
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

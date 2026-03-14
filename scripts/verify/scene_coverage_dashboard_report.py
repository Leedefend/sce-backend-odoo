#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path


REQUIRED_COLUMNS = [
    "scene_key",
    "name",
    "domain",
    "route_target",
    "nav_group",
    "maturity_level",
    "owner_module",
    "next_action",
]
MATURITY_ORDER = ["R0", "R1", "R2", "R3"]


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(cell.replace(":", "").replace("-", "") == "" and "-" in cell for cell in cells)


def _load_matrix_rows(path: Path) -> list[dict[str, str]]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    matrix_idx = -1
    for index, line in enumerate(lines):
        if line.strip().lower() == "## matrix":
            matrix_idx = index
            break
    if matrix_idx < 0:
        raise ValueError("missing section: ## Matrix")

    table_lines: list[str] = []
    for line in lines[matrix_idx + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if "|" in stripped:
            table_lines.append(line)
    if len(table_lines) < 2:
        raise ValueError("matrix table missing header/body")

    header = _split_row(table_lines[0])
    if header != REQUIRED_COLUMNS:
        raise ValueError(f"invalid matrix header: {header}")

    body = table_lines[1:]
    if body and _is_separator(_split_row(body[0])):
        body = body[1:]

    rows: list[dict[str, str]] = []
    for line in body:
        cells = _split_row(line)
        if len(cells) != len(REQUIRED_COLUMNS):
            continue
        rows.append(dict(zip(REQUIRED_COLUMNS, cells)))
    return rows


def _build_report(rows: list[dict[str, str]]) -> str:
    total = len(rows)
    by_maturity = {key: 0 for key in MATURITY_ORDER}
    by_domain: dict[str, dict[str, int]] = defaultdict(lambda: {key: 0 for key in MATURITY_ORDER})

    for row in rows:
        maturity = str(row.get("maturity_level") or "").upper()
        domain = str(row.get("domain") or "unknown").strip() or "unknown"
        if maturity not in by_maturity:
            continue
        by_maturity[maturity] += 1
        by_domain[domain][maturity] += 1

    lines: list[str] = []
    lines.append("# Scene Coverage Dashboard")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"总场景数：{total}")
    lines.append("")
    lines.append("## 成熟度总览")
    lines.append("")
    lines.append("| maturity | count | ratio |")
    lines.append("| --- | ---: | ---: |")
    for level in MATURITY_ORDER:
        count = int(by_maturity.get(level) or 0)
        ratio = f"{(count / total * 100):.1f}%" if total else "0.0%"
        lines.append(f"| {level} | {count} | {ratio} |")

    lines.append("")
    lines.append("## 领域分布")
    lines.append("")
    lines.append("| domain | R0 | R1 | R2 | R3 | total |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for domain in sorted(by_domain.keys()):
        counter = by_domain[domain]
        total_domain = sum(int(counter.get(level) or 0) for level in MATURITY_ORDER)
        lines.append(
            f"| {domain} | {counter['R0']} | {counter['R1']} | {counter['R2']} | {counter['R3']} | {total_domain} |"
        )

    lines.append("")
    lines.append("## 结论")
    lines.append("")
    if total:
        r2_plus = by_maturity["R2"] + by_maturity["R3"]
        lines.append(f"- 当前 `R2+` 场景：{r2_plus}/{total}。")
        lines.append("- Wave1 目标：优先将主线场景推进到 `R2/R3`，非主线维持 `R0/R1`。")
    else:
        lines.append("- 未解析到场景数据，请检查 inventory 文件。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate scene maturity coverage dashboard report.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--output", default="docs/ops/audit/scene_coverage_dashboard.md")
    args = parser.parse_args()

    inventory = Path(args.inventory)
    output = Path(args.output)
    rows = _load_matrix_rows(inventory)
    content = _build_report(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content + "\n", encoding="utf-8")
    print("[scene_coverage_dashboard_report] PASS")
    print(f"- inventory: {inventory}")
    print(f"- output: {output}")
    print(f"- scene_count: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


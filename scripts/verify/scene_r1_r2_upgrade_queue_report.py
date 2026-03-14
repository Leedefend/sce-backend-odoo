#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
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

PRIMARY_PRIORITY_ORDER = [
    "portal.dashboard",
    "projects.dashboard",
    "portal.lifecycle",
    "my_work.workspace",
    "portal.capability_matrix",
    "scene_smoke_default",
]


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _load_inventory(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
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
            table_lines.append(stripped)
    if len(table_lines) < 2:
        raise ValueError("matrix table missing header/body")

    header = _split_row(table_lines[0])
    if header != REQUIRED_COLUMNS:
        raise ValueError(f"invalid matrix header: {header}")

    body = table_lines[1:]
    if body and _is_separator(_split_row(body[0])):
        body = body[1:]

    rows: list[dict[str, str]] = []
    for row in body:
        cells = _split_row(row)
        if len(cells) != len(REQUIRED_COLUMNS):
            continue
        rows.append(dict(zip(REQUIRED_COLUMNS, cells)))
    return rows


def _safe_text(value) -> str:
    return str(value or "").strip()


def _suggest_template(scene_key: str, domain: str, nav_group: str) -> str:
    code = _safe_text(scene_key)
    if code.endswith("dashboard") or code.endswith("lifecycle"):
        return "Dashboard"
    if code.endswith("workspace") or nav_group == "workspace":
        return "Workspace"
    if domain in {"project", "contract", "cost", "finance", "risk"}:
        return "List"
    return "Generic"


def _missing_basics(route_target: str) -> str:
    route = _safe_text(route_target)
    if not route or "TARGET_MISSING" in route:
        return "route_missing"
    return "route_ready"


def _priority(scene_key: str, maturity: str, nav_group: str) -> str:
    code = _safe_text(scene_key)
    level = _safe_text(maturity).upper()
    if code in PRIMARY_PRIORITY_ORDER:
        return "P0"
    if level == "R0":
        return "P1"
    if nav_group in {"workspace", "project_management"}:
        return "P1"
    return "P2"


def _sort_key(row: dict[str, str]) -> tuple:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    maturity_rank = {"R0": 0, "R1": 1}
    return (
        priority_rank.get(row.get("priority") or "P3", 3),
        maturity_rank.get(_safe_text(row.get("maturity_level")).upper(), 9),
        _safe_text(row.get("scene_key")),
    )


def _build_queue(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    queue: list[dict[str, str]] = []
    for row in rows:
        maturity = _safe_text(row.get("maturity_level")).upper()
        if maturity not in {"R0", "R1"}:
            continue
        scene_key = _safe_text(row.get("scene_key"))
        domain = _safe_text(row.get("domain"))
        nav_group = _safe_text(row.get("nav_group"))
        route_target = _safe_text(row.get("route_target"))
        template = _suggest_template(scene_key, domain, nav_group)
        prerequisite = _missing_basics(route_target)
        priority = _priority(scene_key, maturity, nav_group)
        target_maturity = "R1" if maturity == "R0" else "R2"
        queue.append(
            {
                "scene_key": scene_key,
                "name": _safe_text(row.get("name")),
                "domain": domain,
                "nav_group": nav_group,
                "maturity_level": maturity,
                "target_maturity": target_maturity,
                "priority": priority,
                "template": template,
                "prerequisite": prerequisite,
            }
        )
    queue.sort(key=_sort_key)
    return queue


def _write_report(path: Path, queue: list[dict[str, str]]) -> None:
    p0 = sum(1 for row in queue if row.get("priority") == "P0")
    p1 = sum(1 for row in queue if row.get("priority") == "P1")
    p2 = sum(1 for row in queue if row.get("priority") == "P2")
    route_missing = sum(1 for row in queue if row.get("prerequisite") == "route_missing")
    r0 = sum(1 for row in queue if row.get("maturity_level") == "R0")
    r1 = sum(1 for row in queue if row.get("maturity_level") == "R1")

    lines: list[str] = []
    lines.append("# Scene R1-R2 Upgrade Queue")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- `queue_count`: {len(queue)}")
    lines.append(f"- `r0_count`: {r0}")
    lines.append(f"- `r1_count`: {r1}")
    lines.append(f"- `p0_count`: {p0}")
    lines.append(f"- `p1_count`: {p1}")
    lines.append(f"- `p2_count`: {p2}")
    lines.append(f"- `route_missing_count`: {route_missing}")
    lines.append("")
    lines.append("## Queue")
    lines.append("")
    lines.append("| scene_key | name | maturity | target | priority | template | prerequisite |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in queue:
        lines.append(
            f"| {row['scene_key']} | {row['name']} | {row['maturity_level']} | {row['target_maturity']} | {row['priority']} | {row['template']} | {row['prerequisite']} |"
        )
    lines.append("")
    lines.append("## Execution Rule")
    lines.append("")
    lines.append("- 先处理 `P0` 场景，按模板落地基础 `page/layout/zone_blocks`。")
    lines.append("- `R0` 场景先补齐 `route/target` 再进入 `R1→R2`。")
    lines.append("- `scene_smoke_default` 仅维持测试最小形态，不纳入业务主线深度产品化。")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate R1/R0 to R2 upgrade queue report from inventory.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--output", default="docs/ops/audit/scene_r1_r2_upgrade_queue.md")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    rows = _load_inventory(root / args.inventory)
    queue = _build_queue(rows)
    _write_report(root / args.output, queue)

    print("[scene_r1_r2_upgrade_queue_report] PASS")
    print(f"- queue_count: {len(queue)}")
    print(f"- output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


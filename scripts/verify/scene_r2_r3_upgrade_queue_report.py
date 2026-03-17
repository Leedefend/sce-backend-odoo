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

PRIORITY_ORDER = [
    "portal.dashboard",
    "portal.lifecycle",
    "projects.dashboard",
    "my_work.workspace",
    "portal.capability_matrix",
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


def _template(scene_key: str, domain: str) -> str:
    code = _safe_text(scene_key)
    if code.endswith("workspace"):
        return "Workspace"
    if code.endswith("dashboard") or code.endswith("lifecycle"):
        return "Dashboard"
    if domain in {"project", "contract", "cost", "finance", "risk", "data"}:
        return "List"
    return "Generic"


def _priority(scene_key: str) -> str:
    if scene_key in PRIORITY_ORDER:
        return "P0"
    if scene_key.startswith("projects.") or scene_key.startswith("portal."):
        return "P1"
    return "P2"


def _sort_key(row: dict[str, str]) -> tuple:
    rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return (rank.get(row.get("priority") or "P3", 3), _safe_text(row.get("scene_key")))


def _build_queue(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    queue: list[dict[str, str]] = []
    for row in rows:
        maturity = _safe_text(row.get("maturity_level")).upper()
        if maturity != "R2":
            continue
        scene_key = _safe_text(row.get("scene_key"))
        queue.append(
            {
                "scene_key": scene_key,
                "name": _safe_text(row.get("name")),
                "domain": _safe_text(row.get("domain")),
                "template": _template(scene_key, _safe_text(row.get("domain"))),
                "priority": _priority(scene_key),
                "target_maturity": "R3",
                "upgrade_focus": "role_variants + action_specs + data_sources + product_policy",
            }
        )
    queue.sort(key=_sort_key)
    return queue


def _write_report(path: Path, queue: list[dict[str, str]]) -> None:
    p0 = sum(1 for row in queue if row.get("priority") == "P0")
    p1 = sum(1 for row in queue if row.get("priority") == "P1")
    p2 = sum(1 for row in queue if row.get("priority") == "P2")

    lines: list[str] = []
    lines.append("# Scene R2-R3 Upgrade Queue")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- `queue_count`: {len(queue)}")
    lines.append(f"- `p0_count`: {p0}")
    lines.append(f"- `p1_count`: {p1}")
    lines.append(f"- `p2_count`: {p2}")
    lines.append("")
    lines.append("## Queue")
    lines.append("")
    lines.append("| scene_key | name | priority | template | target | upgrade_focus |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for row in queue:
        lines.append(
            f"| {row['scene_key']} | {row['name']} | {row['priority']} | {row['template']} | {row['target_maturity']} | {row['upgrade_focus']} |"
        )
    lines.append("")
    lines.append("## Execution Rule")
    lines.append("")
    lines.append("- `P0` 场景优先升级，最小闭环：`role_variants + action_specs + data_sources + product_policy`。")
    lines.append("- 升级后必须通过：`scene_role_policy_consistency_guard`、`scene_data_source_schema_guard`、`scene_r3_runtime_guard`。")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate R2 to R3 upgrade queue report.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--output", default="docs/ops/audit/scene_r2_r3_upgrade_queue.md")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    rows = _load_inventory(root / args.inventory)
    queue = _build_queue(rows)
    _write_report(root / args.output, queue)

    print("[scene_r2_r3_upgrade_queue_report] PASS")
    print(f"- queue_count: {len(queue)}")
    print(f"- output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


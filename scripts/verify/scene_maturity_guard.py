#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ALLOWED_MATURITY = {"R0", "R1", "R2", "R3"}
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


def _load_table_lines(content: str) -> list[str]:
    lines = [line.rstrip("\n") for line in content.splitlines()]
    matrix_index = -1
    for index, line in enumerate(lines):
        if line.strip().lower() == "## matrix":
            matrix_index = index
            break
    if matrix_index < 0:
        raise ValueError("missing section: ## Matrix")
    table_lines: list[str] = []
    for line in lines[matrix_index + 1 :]:
        if line.strip().startswith("## "):
            break
        if "|" in line:
            table_lines.append(line)
    if len(table_lines) < 2:
        raise ValueError("matrix table is missing header/body")
    return table_lines


def _split_row(line: str) -> list[str]:
    parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return parts


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def validate_inventory(path: Path) -> list[str]:
    if not path.exists():
        return [f"inventory file not found: {path}"]

    content = path.read_text(encoding="utf-8")
    try:
        table_lines = _load_table_lines(content)
    except ValueError as exc:
        return [str(exc)]

    header = _split_row(table_lines[0])
    if header != REQUIRED_COLUMNS:
        return [
            "invalid matrix header",
            f"expected: {REQUIRED_COLUMNS}",
            f"actual:   {header}",
        ]

    errors: list[str] = []
    data_lines = table_lines[1:]
    if data_lines and _is_separator_row(_split_row(data_lines[0])):
        data_lines = data_lines[1:]

    if not data_lines:
        errors.append("matrix has no data rows")
        return errors

    seen_scene_keys: set[str] = set()
    for index, line in enumerate(data_lines, start=1):
        cells = _split_row(line)
        if len(cells) != len(REQUIRED_COLUMNS):
            errors.append(f"row {index}: column count mismatch ({len(cells)} != {len(REQUIRED_COLUMNS)})")
            continue
        row = dict(zip(REQUIRED_COLUMNS, cells))
        scene_key = row["scene_key"].strip()
        maturity = row["maturity_level"].strip().upper()
        owner_module = row["owner_module"].strip()
        next_action = row["next_action"].strip()
        if not scene_key:
            errors.append(f"row {index}: scene_key is empty")
        elif scene_key in seen_scene_keys:
            errors.append(f"row {index}: duplicate scene_key={scene_key}")
        else:
            seen_scene_keys.add(scene_key)
        if maturity not in ALLOWED_MATURITY:
            errors.append(f"row {index}: invalid maturity_level={row['maturity_level']}")
        if not owner_module:
            errors.append(f"row {index}: owner_module is empty")
        if not next_action:
            errors.append(f"row {index}: next_action is empty")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scene maturity inventory matrix contract.")
    parser.add_argument(
        "--inventory",
        default="docs/ops/scene_inventory_matrix_latest.md",
        help="inventory markdown path",
    )
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    errors = validate_inventory(inventory_path)
    if errors:
        print("[scene_maturity_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[scene_maturity_guard] PASS")
    print(f"- inventory: {inventory_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


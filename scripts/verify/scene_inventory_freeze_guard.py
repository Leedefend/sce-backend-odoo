#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
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

R2_PLUS = {"R2", "R3"}
PRODUCT_MARKERS = (
    "'page':",
    "'zone_blocks':",
    "'zones':",
    "'list_profile':",
    "'form_profile':",
    "'action_specs':",
    "'related_scenes':",
)


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _load_inventory(path: Path) -> dict[str, dict[str, str]]:
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
            table_lines.append(stripped)
    if len(table_lines) < 2:
        raise ValueError("matrix table missing header/body")

    header = _split_row(table_lines[0])
    if header != REQUIRED_COLUMNS:
        raise ValueError(f"invalid matrix header: {header}")

    body = table_lines[1:]
    if body and _is_separator(_split_row(body[0])):
        body = body[1:]

    out: dict[str, dict[str, str]] = {}
    for row in body:
        cells = _split_row(row)
        if len(cells) != len(REQUIRED_COLUMNS):
            continue
        item = dict(zip(REQUIRED_COLUMNS, cells))
        key = str(item.get("scene_key") or "").strip()
        if key:
            out[key] = item
    return out


def _load_exemptions(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("legacy_productized_not_in_inventory") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return set()
    return {str(x).strip() for x in rows if str(x).strip()}


def _extract_payload_blocks(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    blocks: list[str] = []
    collecting = False
    current: list[str] = []
    for line in lines:
        if '<field name="payload_json" eval="{' in line:
            collecting = True
            current = [line]
            if '}"/>' in line:
                blocks.append("\n".join(current))
                collecting = False
                current = []
            continue
        if collecting:
            current.append(line)
            if '}"/>' in line:
                blocks.append("\n".join(current))
                collecting = False
                current = []
    return blocks


def _is_productized(payload: str) -> bool:
    return any(marker in payload for marker in PRODUCT_MARKERS)


def _extract_scene_code(payload: str) -> str:
    match = re.search(r"'code'\s*:\s*'([^']+)'", payload)
    return str(match.group(1)).strip() if match else ""


def _is_test_payload(payload: str) -> bool:
    return "'is_test': True" in payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce scene inventory freeze rules for productized scenes.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--exemptions", default="scripts/verify/baselines/scene_inventory_freeze_guard_exemptions.json")
    parser.add_argument(
        "--scene-files",
        nargs="*",
        default=[
            "addons/smart_construction_scene/data/sc_scene_layout.xml",
            "addons/smart_construction_scene/data/sc_scene_list_profile.xml",
            "addons/smart_construction_scene/data/project_management_scene.xml",
        ],
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    inventory = _load_inventory(root / args.inventory)
    exemptions = _load_exemptions(root / args.exemptions)

    productized_codes: set[str] = set()
    for rel in args.scene_files:
        path = root / rel
        if not path.is_file():
            continue
        for payload in _extract_payload_blocks(path):
            code = _extract_scene_code(payload)
            if not code or _is_test_payload(payload):
                continue
            if _is_productized(payload):
                productized_codes.add(code)

    errors: list[str] = []

    for code in sorted(productized_codes):
        if code not in inventory and code not in exemptions:
            errors.append(f"productized scene missing in inventory: {code}")

    for code, row in inventory.items():
        maturity = str(row.get("maturity_level") or "").strip().upper()
        if maturity in R2_PLUS and code not in productized_codes:
            errors.append(f"inventory {maturity} scene missing productized payload markers: {code}")

    for code, row in inventory.items():
        maturity = str(row.get("maturity_level") or "").strip().upper()
        if code in productized_codes and maturity not in R2_PLUS:
            errors.append(f"productized scene maturity must be R2/R3: {code} (current={maturity})")

    if errors:
        print("[scene_inventory_freeze_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[scene_inventory_freeze_guard] PASS")
    print(f"- inventory_scene_count: {len(inventory)}")
    print(f"- productized_scene_count: {len(productized_codes)}")
    print(f"- exemptions: {len(exemptions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


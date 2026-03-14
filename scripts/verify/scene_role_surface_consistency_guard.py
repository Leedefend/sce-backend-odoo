#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
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
ALLOWED_ROLE_CODES = {"owner", "pm", "finance", "executive"}


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _load_inventory(path: Path) -> dict[str, dict[str, str]]:
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


def _extract_payload_texts(path: Path) -> list[str]:
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


def _parse_payload_dict(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    raw = text[start : end + 1]
    try:
        value = ast.literal_eval(raw)
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _load_scene_role_variants(scene_files: list[Path]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for path in scene_files:
        if not path.is_file():
            continue
        for payload_text in _extract_payload_texts(path):
            payload = _parse_payload_dict(payload_text)
            if not isinstance(payload, dict):
                continue
            scene_key = str(payload.get("code") or payload.get("key") or "").strip()
            if not scene_key:
                continue
            role_variants = payload.get("role_variants") if isinstance(payload.get("role_variants"), dict) else {}
            roles = {str(role or "").strip() for role in role_variants.keys() if str(role or "").strip()}
            mapping[scene_key] = roles
    return mapping


def _extract_dict_literal(source: str, anchor: str) -> dict:
    pos = source.find(anchor)
    if pos < 0:
        raise ValueError(f"missing anchor: {anchor}")
    eq_pos = source.find("=", pos)
    if eq_pos < 0:
        raise ValueError(f"missing '=' after anchor: {anchor}")
    start = source.find("{", eq_pos)
    if start < 0:
        raise ValueError(f"missing '{{' after anchor: {anchor}")

    depth = 0
    end = -1
    for idx in range(start, len(source)):
        char = source[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = idx
                break
    if end < 0:
        raise ValueError(f"unterminated dict for anchor: {anchor}")

    raw = source[start : end + 1]
    value = ast.literal_eval(raw)
    if not isinstance(value, dict):
        raise ValueError(f"anchor literal is not dict: {anchor}")
    return value


def _load_role_surface_overrides(path: Path) -> dict[str, dict]:
    source = path.read_text(encoding="utf-8")
    value = _extract_dict_literal(source, "ROLE_SURFACE_OVERRIDES")
    out: dict[str, dict] = {}
    for role_code, role_meta in value.items():
        key = str(role_code or "").strip()
        if not key:
            continue
        out[key] = role_meta if isinstance(role_meta, dict) else {}
    return out


def _list_str(value) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _write_report(path: Path, summary: dict[str, int], role_rows: list[dict], scene_rows: list[dict], warnings: list[str]) -> None:
    lines: list[str] = []
    lines.append("# Scene Role Surface Consistency Report")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- `role_count`: {summary['role_count']}")
    lines.append(f"- `r3_scene_count`: {summary['r3_scene_count']}")
    lines.append(f"- `errors`: {summary['error_count']}")
    lines.append(f"- `warnings`: {summary['warning_count']}")
    lines.append("")
    lines.append("## Role Overrides")
    lines.append("")
    lines.append("| role_code | candidates | candidate_missing | menu_overlap | r3_scene_hits | status |")
    lines.append("| --- | ---: | ---: | ---: | ---: | --- |")
    for row in role_rows:
        lines.append(
            "| {role_code} | {candidates} | {candidate_missing} | {menu_overlap} | {r3_scene_hits} | {status} |".format(
                **row
            )
        )

    lines.append("")
    lines.append("## R3 Scene Role Variants")
    lines.append("")
    lines.append("| scene_key | role_variant_count | unknown_roles | status |")
    lines.append("| --- | ---: | --- | --- |")
    for row in scene_rows:
        lines.append(
            "| {scene_key} | {role_variant_count} | {unknown_roles} | {status} |".format(
                **row
            )
        )

    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        for item in sorted(set(warnings)):
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate consistency between role_surface_overrides and R3 role_variants.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--role-overrides-file", default="addons/smart_construction_core/core_extension.py")
    parser.add_argument("--output", default="docs/ops/audit/scene_role_surface_consistency_report.md")
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
    role_overrides = _load_role_surface_overrides(root / args.role_overrides_file)
    scene_role_variants = _load_scene_role_variants([root / rel for rel in args.scene_files])

    errors: list[str] = []
    warnings: list[str] = []

    scene_keys_all = set(inventory.keys())
    payload_scene_keys = set(scene_role_variants.keys())
    r3_scene_keys = {
        scene_key
        for scene_key, row in inventory.items()
        if str(row.get("maturity_level") or "").upper() == "R3"
    }

    role_rows: list[dict] = []
    override_roles = set(role_overrides.keys())
    invalid_override_roles = sorted(override_roles - ALLOWED_ROLE_CODES)
    for role_code in invalid_override_roles:
        errors.append(f"role_surface_overrides: unsupported role code ({role_code})")

    for role_code in sorted(override_roles):
        role_meta = role_overrides.get(role_code)
        if not isinstance(role_meta, dict):
            errors.append(f"role_surface_overrides.{role_code}: must be dict")
            continue

        candidates = _list_str(role_meta.get("landing_scene_candidates"))
        menu_xmlids = _list_str(role_meta.get("menu_xmlids"))
        blocklist_xmlids = _list_str(role_meta.get("menu_blocklist_xmlids"))

        if not candidates:
            errors.append(f"role_surface_overrides.{role_code}: landing_scene_candidates empty")
        candidate_missing = sorted({key for key in candidates if key not in scene_keys_all})
        for key in candidate_missing:
            if key not in payload_scene_keys:
                warnings.append(
                    f"role_surface_overrides.{role_code}: landing_scene_candidate not in inventory/payload ({key})"
                )
            else:
                warnings.append(f"role_surface_overrides.{role_code}: landing_scene_candidate outside inventory ({key})")

        overlap = sorted(set(menu_xmlids) & set(blocklist_xmlids))
        for xmlid in overlap:
            errors.append(f"role_surface_overrides.{role_code}: menu overlap in allow/blocklist ({xmlid})")

        hit_count = 0
        for scene_key in r3_scene_keys:
            roles = scene_role_variants.get(scene_key) or set()
            if role_code in roles:
                hit_count += 1
        if hit_count == 0:
            warnings.append(f"role_surface_overrides.{role_code}: no R3 scene role_variants coverage")

        role_rows.append(
            {
                "role_code": role_code,
                "candidates": len(candidates),
                "candidate_missing": len(candidate_missing),
                "menu_overlap": len(overlap),
                "r3_scene_hits": hit_count,
                "status": "PASS" if not overlap and candidates else "FAIL",
            }
        )

    scene_rows: list[dict] = []
    for scene_key in sorted(r3_scene_keys):
        scene_roles = scene_role_variants.get(scene_key) or set()
        unknown_roles = sorted(scene_roles - override_roles)
        if unknown_roles:
            errors.append(f"{scene_key}: role_variants includes unknown roles ({','.join(unknown_roles)})")
        if not scene_roles:
            warnings.append(f"{scene_key}: role_variants empty for R3 scene")
        scene_rows.append(
            {
                "scene_key": scene_key,
                "role_variant_count": len(scene_roles),
                "unknown_roles": ", ".join(unknown_roles),
                "status": "PASS" if not unknown_roles else "FAIL",
            }
        )

    summary = {
        "role_count": len(override_roles),
        "r3_scene_count": len(r3_scene_keys),
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    _write_report(root / args.output, summary, role_rows, scene_rows, warnings)

    if errors:
        print("[scene_role_surface_consistency_guard] FAIL")
        for item in sorted(set(errors)):
            print(f"- {item}")
        print(f"- output: {args.output}")
        return 1

    print("[scene_role_surface_consistency_guard] PASS")
    print(f"- role_count: {summary['role_count']}")
    print(f"- r3_scene_count: {summary['r3_scene_count']}")
    print(f"- warning_count: {summary['warning_count']}")
    print(f"- output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

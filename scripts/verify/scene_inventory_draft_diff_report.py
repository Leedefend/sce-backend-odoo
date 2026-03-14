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

R3_MARKERS = ("role_variants", "data_sources", "product_policy", "action_specs")
R2_MARKERS = ("page", "zone_blocks", "zones", "list_profile", "form_profile", "action_specs", "related_scenes", "layout")
FOCUS_DIFF_FIELDS = ("maturity_level", "owner_module", "next_action")


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


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

    rows: dict[str, dict[str, str]] = {}
    for row in body:
        cells = _split_row(row)
        if len(cells) != len(REQUIRED_COLUMNS):
            continue
        item = dict(zip(REQUIRED_COLUMNS, cells))
        scene_key = str(item.get("scene_key") or "").strip()
        if scene_key:
            rows[scene_key] = item
    return rows


def _safe_text(value) -> str:
    return str(value or "").strip()


def _infer_domain(scene_key: str) -> str:
    code = _safe_text(scene_key)
    if not code:
        return "others"
    token = code.split(".")[0]
    if token in {"project", "projects"}:
        return "project"
    if token in {"contract", "contracts"}:
        return "contract"
    return token


def _infer_nav_group(domain: str) -> str:
    mapping = {
        "project": "project_management",
        "contract": "contract_management",
        "cost": "cost_management",
        "finance": "finance_management",
        "risk": "risk_management",
        "task": "task_management",
        "data": "data_dictionary",
        "config": "config_center",
        "portal": "workspace",
        "workspace": "workspace",
        "my_work": "workspace",
    }
    return mapping.get(domain, "others")


def _infer_maturity(payload: dict) -> str:
    has_r3 = (
        isinstance(payload.get("role_variants"), dict)
        and bool(payload.get("role_variants"))
        and isinstance(payload.get("data_sources"), dict)
        and bool(payload.get("data_sources"))
        and isinstance(payload.get("product_policy"), dict)
        and bool(payload.get("product_policy"))
        and isinstance(payload.get("action_specs"), dict)
        and bool(payload.get("action_specs"))
    )
    if has_r3:
        return "R3"
    if any(marker in payload for marker in R2_MARKERS):
        return "R2"
    if "target" in payload:
        return "R1"
    return "R0"


def _infer_next_action(maturity: str) -> str:
    mapping = {
        "R3": "维护角色策略与数据契约稳定性",
        "R2": "补齐角色策略与数据契约升级到R3",
        "R1": "补齐场景内容编排进入R2",
        "R0": "补齐注册与路由事实",
    }
    return mapping.get(maturity, "补齐场景产品化信息")


def _owner_module_from_path(path: Path) -> str:
    parts = path.parts
    if "addons" in parts:
        idx = parts.index("addons")
        if idx + 1 < len(parts):
            return _safe_text(parts[idx + 1])
    return "unknown"


def _route_from_payload(payload: dict) -> str:
    target = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    route = _safe_text(target.get("route"))
    return f"`{route}`" if route else "TARGET_MISSING"


def _build_draft_rows(scene_files: list[Path]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in scene_files:
        if not path.is_file():
            continue
        owner_module = _owner_module_from_path(path)
        for payload_text in _extract_payload_texts(path):
            payload = _parse_payload_dict(payload_text)
            if not isinstance(payload, dict):
                continue
            scene_key = _safe_text(payload.get("code") or payload.get("key"))
            if not scene_key:
                continue
            name = _safe_text(payload.get("name")) or scene_key
            domain = _infer_domain(scene_key)
            nav_group = _infer_nav_group(domain)
            maturity = _infer_maturity(payload)
            rows[scene_key] = {
                "scene_key": scene_key,
                "name": name,
                "domain": domain,
                "route_target": _route_from_payload(payload),
                "nav_group": nav_group,
                "maturity_level": maturity,
                "owner_module": owner_module,
                "next_action": _infer_next_action(maturity),
            }
    return rows


def _write_draft(path: Path, rows: dict[str, dict[str, str]]) -> None:
    lines: list[str] = []
    lines.append("# Scene Inventory Matrix（Draft from payload）")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("来源：自动从 scene payload 解析生成")
    lines.append("")
    lines.append("## Matrix")
    lines.append("")
    lines.append("| " + " | ".join(REQUIRED_COLUMNS) + " |")
    lines.append("| " + " | ".join(["---"] * len(REQUIRED_COLUMNS)) + " |")
    for scene_key in sorted(rows.keys()):
        row = rows[scene_key]
        lines.append("| " + " | ".join([_safe_text(row.get(col)) for col in REQUIRED_COLUMNS]) + " |")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_diff_rows(current: dict[str, dict[str, str]], draft: dict[str, dict[str, str]]) -> tuple[list[str], list[str], list[dict], list[dict]]:
    current_keys = set(current.keys())
    draft_keys = set(draft.keys())
    added = sorted(draft_keys - current_keys)
    removed = sorted(current_keys - draft_keys)

    changed: list[dict] = []
    focus_changed: list[dict] = []
    shared = sorted(current_keys & draft_keys)
    for scene_key in shared:
        old = current.get(scene_key) or {}
        new = draft.get(scene_key) or {}
        for field in REQUIRED_COLUMNS[1:]:
            old_value = _safe_text(old.get(field))
            new_value = _safe_text(new.get(field))
            if old_value == new_value:
                continue
            row = {
                "scene_key": scene_key,
                "field": field,
                "old": old_value,
                "new": new_value,
            }
            changed.append(row)
            if field in FOCUS_DIFF_FIELDS:
                focus_changed.append(row)
    return added, removed, changed, focus_changed


def _write_diff_report(
    path: Path,
    current: dict[str, dict[str, str]],
    draft: dict[str, dict[str, str]],
    added: list[str],
    removed: list[str],
    changed: list[dict],
    focus_changed: list[dict],
) -> None:
    lines: list[str] = []
    lines.append("# Scene Inventory Draft Diff Report")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- `current_count`: {len(current)}")
    lines.append(f"- `draft_count`: {len(draft)}")
    lines.append(f"- `added_count`: {len(added)}")
    lines.append(f"- `removed_count`: {len(removed)}")
    lines.append(f"- `changed_count`: {len(changed)}")
    lines.append(f"- `focus_changed_count`: {len(focus_changed)}")
    lines.append("")

    lines.append("## Added Scenes")
    lines.append("")
    if added:
        for scene_key in added:
            lines.append(f"- {scene_key}")
    else:
        lines.append("- 无")
    lines.append("")

    lines.append("## Removed Scenes")
    lines.append("")
    if removed:
        for scene_key in removed:
            lines.append(f"- {scene_key}")
    else:
        lines.append("- 无")
    lines.append("")

    lines.append("## Focus Field Diff")
    lines.append("")
    lines.append("| scene_key | field | current | draft |")
    lines.append("| --- | --- | --- | --- |")
    if focus_changed:
        for row in focus_changed:
            lines.append(f"| {row['scene_key']} | {row['field']} | {row['old']} | {row['new']} |")
    else:
        lines.append("| - | - | - | - |")
    lines.append("")

    lines.append("## Full Field Diff")
    lines.append("")
    lines.append("| scene_key | field | current | draft |")
    lines.append("| --- | --- | --- | --- |")
    if changed:
        for row in changed:
            lines.append(f"| {row['scene_key']} | {row['field']} | {row['old']} | {row['new']} |")
    else:
        lines.append("| - | - | - | - |")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate scene inventory draft from payload and output diff report.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--draft-output", default="docs/ops/audit/scene_inventory_matrix_draft.md")
    parser.add_argument("--diff-output", default="docs/ops/audit/scene_inventory_draft_diff_report.md")
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
    current_inventory = _load_inventory(root / args.inventory)
    draft_inventory = _build_draft_rows([root / rel for rel in args.scene_files])

    added, removed, changed, focus_changed = _build_diff_rows(current_inventory, draft_inventory)
    _write_draft(root / args.draft_output, draft_inventory)
    _write_diff_report(
        root / args.diff_output,
        current_inventory,
        draft_inventory,
        added,
        removed,
        changed,
        focus_changed,
    )

    print("[scene_inventory_draft_diff_report] PASS")
    print(f"- current_count: {len(current_inventory)}")
    print(f"- draft_count: {len(draft_inventory)}")
    print(f"- added_count: {len(added)}")
    print(f"- removed_count: {len(removed)}")
    print(f"- focus_changed_count: {len(focus_changed)}")
    print(f"- draft_output: {args.draft_output}")
    print(f"- diff_output: {args.diff_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


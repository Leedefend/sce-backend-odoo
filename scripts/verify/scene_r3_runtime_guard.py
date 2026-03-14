#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
from datetime import datetime
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


def _route_from_inventory(route_target: str) -> str:
    text = str(route_target or "").strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1].strip()
    return text


def _is_route_openable(route: str) -> bool:
    text = str(route or "").strip()
    if not text:
        return False
    if "TARGET_MISSING" in text:
        return False
    return text.startswith("/")


def _guess_scene_keys_from_action(action_key: str) -> list[str]:
    key = str(action_key or "").strip()
    if key.startswith("open_"):
        key = key[len("open_") :]
    elif key.startswith("go_"):
        key = key[len("go_") :]
    key = key.strip("_")
    if not key:
        return []

    segments = [part for part in key.split("_") if part]
    dotted = ".".join(segments)
    candidates: list[str] = []
    if dotted:
        candidates.append(dotted)

    if segments and segments[0] == "project" and len(segments) > 1:
        candidates.append("projects." + ".".join(segments[1:]))
        candidates.append("project." + ".".join(segments[1:]))

    dedup: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item and item not in seen:
            dedup.append(item)
            seen.add(item)
    return dedup


def _resolve_inventory_route(scene_key: str, inventory: dict[str, dict[str, str]]) -> str:
    row = inventory.get(scene_key) or {}
    return _route_from_inventory(str(row.get("route_target") or ""))


def _resolve_primary_action_route(scene_key: str, payload: dict, inventory: dict[str, dict[str, str]]) -> tuple[str, str]:
    product_policy = payload.get("product_policy") if isinstance(payload.get("product_policy"), dict) else {}
    action_specs = payload.get("action_specs") if isinstance(payload.get("action_specs"), dict) else {}
    related_scenes = payload.get("related_scenes") if isinstance(payload.get("related_scenes"), list) else []

    primary_action = str(product_policy.get("primary_action") or "").strip()
    if not primary_action:
        return "", f"{scene_key}: product_policy.primary_action is empty"

    action_spec = action_specs.get(primary_action)
    if not isinstance(action_spec, dict):
        return "", f"{scene_key}: action_specs missing primary_action={primary_action}"

    intent = str(action_spec.get("intent") or "").strip()
    if intent != "ui.contract":
        return "N/A", ""

    direct_route = _route_from_inventory(str(action_spec.get("route") or action_spec.get("target_route") or ""))
    if _is_route_openable(direct_route):
        return direct_route, ""

    for scene_field in ("scene_key", "target_scene", "scene"):
        target_scene = str(action_spec.get(scene_field) or "").strip()
        if not target_scene:
            continue
        route = _resolve_inventory_route(target_scene, inventory)
        if _is_route_openable(route):
            return route, ""

    related_keys = [str(item or "").strip() for item in related_scenes if str(item or "").strip()]
    for candidate in _guess_scene_keys_from_action(primary_action):
        if candidate in related_keys:
            route = _resolve_inventory_route(candidate, inventory)
            if _is_route_openable(route):
                return route, ""

    action_tail = primary_action
    if action_tail.startswith("open_"):
        action_tail = action_tail[len("open_") :]
    action_tail = action_tail.strip("_")
    tail_token = action_tail.split("_")[-1] if action_tail else ""
    for related in related_keys:
        related_parts = related.split(".")
        if action_tail and (related.endswith(action_tail.replace("_", ".")) or related_parts[-1] == tail_token):
            route = _resolve_inventory_route(related, inventory)
            if _is_route_openable(route):
                return route, ""

    target = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    self_route = _route_from_inventory(str(target.get("route") or ""))
    if not _is_route_openable(self_route):
        self_route = _resolve_inventory_route(scene_key, inventory)
    if _is_route_openable(self_route):
        return self_route, ""

    return "", f"{scene_key}: cannot resolve openable route for primary_action={primary_action}"


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


def _load_payloads(scene_files: list[Path]) -> dict[str, dict]:
    payloads: dict[str, dict] = {}
    for path in scene_files:
        if not path.is_file():
            continue
        for block in _extract_payload_texts(path):
            payload = _parse_payload_dict(block)
            if not isinstance(payload, dict):
                continue
            scene_key = str(payload.get("code") or payload.get("key") or "").strip()
            if scene_key:
                payloads[scene_key] = payload
    return payloads


def _zone_keys(payload: dict) -> set[str]:
    out: set[str] = set()
    zone_blocks = payload.get("zone_blocks") if isinstance(payload.get("zone_blocks"), list) else []
    for item in zone_blocks:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if key:
            out.add(key)
    zones = payload.get("zones") if isinstance(payload.get("zones"), list) else []
    for item in zones:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        if key:
            out.add(key)
    return out


def _validate_r3_scene(scene_key: str, payload: dict, inventory: dict[str, dict[str, str]]) -> tuple[dict[str, bool], list[str]]:
    checks: dict[str, bool] = {
        "has_role_variants": False,
        "has_data_sources": False,
        "has_product_policy": False,
        "primary_action_resolved": False,
        "action_chain_openable": False,
        "role_zone_mapping_valid": False,
    }
    errors: list[str] = []

    role_variants = payload.get("role_variants") if isinstance(payload.get("role_variants"), dict) else {}
    data_sources = payload.get("data_sources") if isinstance(payload.get("data_sources"), dict) else {}
    product_policy = payload.get("product_policy") if isinstance(payload.get("product_policy"), dict) else {}
    action_specs = payload.get("action_specs") if isinstance(payload.get("action_specs"), dict) else {}
    zone_keys = _zone_keys(payload)

    checks["has_role_variants"] = bool(role_variants)
    checks["has_data_sources"] = bool(data_sources)
    checks["has_product_policy"] = bool(product_policy and bool(product_policy.get("role_based")))

    primary_action = str(product_policy.get("primary_action") or "").strip()
    checks["primary_action_resolved"] = bool(primary_action and primary_action in action_specs)
    if not checks["primary_action_resolved"]:
        errors.append(f"{scene_key}: product_policy.primary_action missing or not in action_specs")
    else:
        route, route_error = _resolve_primary_action_route(scene_key, payload, inventory)
        checks["action_chain_openable"] = _is_route_openable(route) or route == "N/A"
        if not checks["action_chain_openable"] and route_error:
            errors.append(route_error)

    role_zone_ok = True
    for role_code, config in role_variants.items():
        if not isinstance(config, dict):
            role_zone_ok = False
            errors.append(f"{scene_key}: role_variants.{role_code} must be dict")
            continue
        focus_zones = config.get("focus_zones") if isinstance(config.get("focus_zones"), list) else []
        if not focus_zones:
            role_zone_ok = False
            errors.append(f"{scene_key}: role_variants.{role_code}.focus_zones empty")
        for zone in focus_zones:
            zone_key = str(zone or "").strip()
            if zone_key and zone_key not in zone_keys:
                role_zone_ok = False
                errors.append(f"{scene_key}: role_variants.{role_code}.focus_zones missing zone={zone_key}")
    checks["role_zone_mapping_valid"] = role_zone_ok

    for check_name, passed in checks.items():
        if not passed and check_name != "role_zone_mapping_valid":
            errors.append(f"{scene_key}: check failed ({check_name})")

    return checks, errors


def _write_report(path: Path, rows: list[dict], summary: dict[str, int]) -> None:
    lines: list[str] = []
    lines.append("# Scene R3 Runtime Dashboard")
    lines.append("")
    lines.append(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- `r3_scene_count`: {summary['r3_scene_count']}")
    lines.append(f"- `pass_count`: {summary['pass_count']}")
    lines.append(f"- `fail_count`: {summary['fail_count']}")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| scene_key | has_role_variants | has_data_sources | has_product_policy | primary_action_resolved | action_chain_openable | role_zone_mapping_valid | status |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        lines.append(
            "| {scene_key} | {has_role_variants} | {has_data_sources} | {has_product_policy} | {primary_action_resolved} | {action_chain_openable} | {role_zone_mapping_valid} | {status} |".format(
                **row
            )
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate runtime-readiness criteria for R3 scenes.")
    parser.add_argument("--inventory", default="docs/ops/scene_inventory_matrix_latest.md")
    parser.add_argument("--output", default="docs/ops/audit/scene_r3_runtime_dashboard.md")
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
    payloads = _load_payloads([root / rel for rel in args.scene_files])

    r3_scene_keys = [key for key, row in inventory.items() if str(row.get("maturity_level") or "").upper() == "R3"]

    rows: list[dict] = []
    errors: list[str] = []
    for scene_key in sorted(r3_scene_keys):
        payload = payloads.get(scene_key)
        if not isinstance(payload, dict):
            errors.append(f"{scene_key}: missing payload definition")
            rows.append(
                {
                    "scene_key": scene_key,
                    "has_role_variants": "❌",
                    "has_data_sources": "❌",
                    "has_product_policy": "❌",
                    "primary_action_resolved": "❌",
                    "action_chain_openable": "❌",
                    "role_zone_mapping_valid": "❌",
                    "status": "FAIL",
                }
            )
            continue

        checks, scene_errors = _validate_r3_scene(scene_key, payload, inventory)
        errors.extend(scene_errors)
        all_pass = all(checks.values())
        rows.append(
            {
                "scene_key": scene_key,
                "has_role_variants": "✅" if checks["has_role_variants"] else "❌",
                "has_data_sources": "✅" if checks["has_data_sources"] else "❌",
                "has_product_policy": "✅" if checks["has_product_policy"] else "❌",
                "primary_action_resolved": "✅" if checks["primary_action_resolved"] else "❌",
                "action_chain_openable": "✅" if checks["action_chain_openable"] else "❌",
                "role_zone_mapping_valid": "✅" if checks["role_zone_mapping_valid"] else "❌",
                "status": "PASS" if all_pass else "FAIL",
            }
        )

    pass_count = sum(1 for row in rows if row.get("status") == "PASS")
    summary = {
        "r3_scene_count": len(r3_scene_keys),
        "pass_count": pass_count,
        "fail_count": len(r3_scene_keys) - pass_count,
    }
    _write_report(root / args.output, rows, summary)

    if errors:
        print("[scene_r3_runtime_guard] FAIL")
        for item in sorted(set(errors)):
            print(f"- {item}")
        print(f"- output: {args.output}")
        return 1

    print("[scene_r3_runtime_guard] PASS")
    print(f"- r3_scene_count: {summary['r3_scene_count']}")
    print(f"- output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

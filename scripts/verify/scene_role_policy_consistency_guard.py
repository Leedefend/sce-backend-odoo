#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


ALLOWED_ROLE_CODES = {"owner", "pm", "finance", "executive"}


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


def _zone_keys(payload: dict) -> set[str]:
    keys: set[str] = set()
    zone_blocks = payload.get("zone_blocks") if isinstance(payload.get("zone_blocks"), list) else []
    for item in zone_blocks:
        if isinstance(item, dict):
            key = str(item.get("key") or "").strip()
            if key:
                keys.add(key)
    zones = payload.get("zones") if isinstance(payload.get("zones"), list) else []
    for item in zones:
        if isinstance(item, dict):
            key = str(item.get("key") or "").strip()
            if key:
                keys.add(key)
    return keys


def _scene_key(payload: dict) -> str:
    return str(payload.get("code") or payload.get("key") or "").strip()


def _validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    scene_key = _scene_key(payload) or "<unknown>"
    role_variants = payload.get("role_variants")
    if role_variants is None:
        return errors
    if not isinstance(role_variants, dict):
        return [f"{scene_key}: role_variants must be dict"]

    action_specs = payload.get("action_specs") if isinstance(payload.get("action_specs"), dict) else {}
    action_keys = {str(key).strip() for key in action_specs.keys() if str(key).strip()}
    zone_keys = _zone_keys(payload)
    product_policy = payload.get("product_policy") if isinstance(payload.get("product_policy"), dict) else {}
    primary_action = str(product_policy.get("primary_action") or "").strip()

    if primary_action and primary_action not in action_keys:
        errors.append(f"{scene_key}: product_policy.primary_action not in action_specs ({primary_action})")

    for role_code, policy in role_variants.items():
        normalized_role = str(role_code or "").strip()
        if normalized_role not in ALLOWED_ROLE_CODES:
            errors.append(f"{scene_key}: unsupported role code in role_variants ({normalized_role})")
            continue
        if not isinstance(policy, dict):
            errors.append(f"{scene_key}: role_variants.{normalized_role} must be dict")
            continue

        default_actions = policy.get("default_actions") if isinstance(policy.get("default_actions"), list) else []
        focus_zones = policy.get("focus_zones") if isinstance(policy.get("focus_zones"), list) else []
        if not default_actions:
            errors.append(f"{scene_key}: role_variants.{normalized_role}.default_actions is empty")
        for action in default_actions:
            key = str(action or "").strip()
            if not key:
                errors.append(f"{scene_key}: role_variants.{normalized_role}.default_actions contains empty value")
                continue
            if key not in action_keys:
                errors.append(f"{scene_key}: role_variants.{normalized_role}.default_actions references missing action ({key})")

        if not focus_zones:
            errors.append(f"{scene_key}: role_variants.{normalized_role}.focus_zones is empty")
        for zone in focus_zones:
            zone_key = str(zone or "").strip()
            if not zone_key:
                errors.append(f"{scene_key}: role_variants.{normalized_role}.focus_zones contains empty value")
                continue
            if zone_key not in zone_keys:
                errors.append(f"{scene_key}: role_variants.{normalized_role}.focus_zones references missing zone ({zone_key})")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scene role policy consistency.")
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
    errors: list[str] = []
    payload_count = 0
    role_payload_count = 0

    for rel in args.scene_files:
        path = root / rel
        if not path.is_file():
            continue
        for payload_text in _extract_payload_texts(path):
            payload = _parse_payload_dict(payload_text)
            if not isinstance(payload, dict):
                continue
            payload_count += 1
            if "role_variants" in payload:
                role_payload_count += 1
            errors.extend(_validate_payload(payload))

    if errors:
        print("[scene_role_policy_consistency_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[scene_role_policy_consistency_guard] PASS")
    print(f"- payload_count: {payload_count}")
    print(f"- payload_with_role_variants: {role_payload_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


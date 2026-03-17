#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


ALLOWED_SOURCE_TYPES = {"odoo_model", "computed", "static", "scene_context", "capability_registry"}


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


def _scene_key(payload: dict) -> str:
    return str(payload.get("code") or payload.get("key") or "").strip() or "<unknown>"


def _validate_data_sources(payload: dict) -> list[str]:
    errors: list[str] = []
    scene_key = _scene_key(payload)
    data_sources = payload.get("data_sources")
    if data_sources is None:
        return errors
    if not isinstance(data_sources, dict):
        return [f"{scene_key}: data_sources must be dict"]
    if not data_sources:
        return [f"{scene_key}: data_sources is empty"]

    for source_key, spec in data_sources.items():
        key = str(source_key or "").strip()
        if not key:
            errors.append(f"{scene_key}: data_sources contains empty key")
            continue
        if not isinstance(spec, dict):
            errors.append(f"{scene_key}: data_sources.{key} must be dict")
            continue
        source_type = str(spec.get("source_type") or "").strip()
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{scene_key}: data_sources.{key}.source_type invalid ({source_type})")
            continue

        if source_type == "odoo_model":
            model = str(spec.get("model") or "").strip()
            if not model:
                errors.append(f"{scene_key}: data_sources.{key} missing model for odoo_model")
            elif not re.fullmatch(r"[a-zA-Z_][\w.]+", model):
                errors.append(f"{scene_key}: data_sources.{key}.model format invalid ({model})")

        if source_type in {"computed", "scene_context", "capability_registry"}:
            provider = str(spec.get("provider") or "").strip()
            if not provider:
                errors.append(f"{scene_key}: data_sources.{key} missing provider for {source_type}")
            elif not re.fullmatch(r"[a-zA-Z_][\w.]+", provider):
                errors.append(f"{scene_key}: data_sources.{key}.provider format invalid ({provider})")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scene data source schema semantics.")
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
    data_source_payload_count = 0

    for rel in args.scene_files:
        path = root / rel
        if not path.is_file():
            continue
        for payload_text in _extract_payload_texts(path):
            payload = _parse_payload_dict(payload_text)
            if not isinstance(payload, dict):
                continue
            payload_count += 1
            if "data_sources" in payload:
                data_source_payload_count += 1
            errors.extend(_validate_data_sources(payload))

    if errors:
        print("[scene_data_source_schema_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[scene_data_source_schema_guard] PASS")
    print(f"- payload_count: {payload_count}")
    print(f"- payload_with_data_sources: {data_source_payload_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


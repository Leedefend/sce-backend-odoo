#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_ROOT_KEYS = ("scene_count", "scenes", "layout_kind_counts", "target_type_counts")
REQUIRED_SCENE_SECTIONS = ("identity", "access", "layout", "components", "target")


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_catalog(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_ROOT_KEYS:
        if key not in payload:
            _fail(errors, f"missing root key: {key}")

    scenes = payload.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        _fail(errors, "scenes must be a non-empty list")
        return errors

    scene_count = payload.get("scene_count")
    if isinstance(scene_count, int) and scene_count != len(scenes):
        _fail(errors, f"scene_count mismatch: declared={scene_count} actual={len(scenes)}")

    keys_seen: set[str] = set()
    for idx, scene in enumerate(scenes):
        prefix = f"scene[{idx}]"
        if not isinstance(scene, dict):
            _fail(errors, f"{prefix} must be object")
            continue
        scene_key = scene.get("scene_key")
        if not _is_non_empty_str(scene_key):
            _fail(errors, f"{prefix}.scene_key must be non-empty")
        else:
            if scene_key in keys_seen:
                _fail(errors, f"duplicate scene_key: {scene_key}")
            keys_seen.add(scene_key)

        for section in REQUIRED_SCENE_SECTIONS:
            section_value = scene.get(section)
            if not isinstance(section_value, dict):
                _fail(errors, f"{prefix}.{section} must be object")

        identity = scene.get("identity")
        if isinstance(identity, dict):
            if not _is_non_empty_str(identity.get("scene_key")):
                _fail(errors, f"{prefix}.identity.scene_key must be non-empty")

        layout = scene.get("layout")
        if isinstance(layout, dict):
            if not _is_non_empty_str(layout.get("kind")):
                _fail(errors, f"{prefix}.layout.kind must be non-empty")
            keys = layout.get("keys")
            if not isinstance(keys, list):
                _fail(errors, f"{prefix}.layout.keys must be list")

        components = scene.get("components")
        if isinstance(components, dict):
            for field in ("tiles_count", "filters_count"):
                if not isinstance(components.get(field), int):
                    _fail(errors, f"{prefix}.components.{field} must be int")
            if not isinstance(components.get("has_list_profile"), bool):
                _fail(errors, f"{prefix}.components.has_list_profile must be bool")

        access = scene.get("access")
        if isinstance(access, dict):
            if not isinstance(access.get("visible"), bool):
                _fail(errors, f"{prefix}.access.visible must be bool")
            if not isinstance(access.get("allowed"), bool):
                _fail(errors, f"{prefix}.access.allowed must be bool")
            if not _is_non_empty_str(access.get("reason_code")):
                _fail(errors, f"{prefix}.access.reason_code must be non-empty")
            if not isinstance(access.get("suggested_action"), str):
                _fail(errors, f"{prefix}.access.suggested_action must be str")
            req_caps = access.get("required_capabilities")
            if not isinstance(req_caps, list):
                _fail(errors, f"{prefix}.access.required_capabilities must be list")
            elif not all(isinstance(item, str) for item in req_caps):
                _fail(errors, f"{prefix}.access.required_capabilities items must be str")
            if not isinstance(access.get("required_capabilities_count"), int):
                _fail(errors, f"{prefix}.access.required_capabilities_count must be int")
            if not isinstance(access.get("has_access_clause"), bool):
                _fail(errors, f"{prefix}.access.has_access_clause must be bool")

        target = scene.get("target")
        if isinstance(target, dict):
            if not _is_non_empty_str(target.get("type")):
                _fail(errors, f"{prefix}.target.type must be non-empty")
            keys = target.get("keys")
            if not isinstance(keys, list) or not keys:
                _fail(errors, f"{prefix}.target.keys must be non-empty list")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scene contract catalog shape.")
    parser.add_argument("--catalog", default="docs/contract/exports/scene_catalog.json")
    parser.add_argument("--report", default="artifacts/scene_contract_shape_guard.json")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    report_path = Path(args.report)
    if not catalog_path.exists():
        raise SystemExit(f"missing catalog: {catalog_path}")

    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("scene catalog must be object")

    errors = validate_catalog(payload)
    report = {
        "ok": len(errors) == 0,
        "catalog": str(catalog_path),
        "scene_count": len(payload.get("scenes") or []),
        "errors": errors,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print(f"[verify.scene.contract.shape] FAIL ({len(errors)} errors)")
        for item in errors[:20]:
            print(f" - {item}")
        return 2

    print("[verify.scene.contract.shape] PASS")
    print(f"[verify.scene.contract.shape] report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

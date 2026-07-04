#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "platform_release_policy_runtime_probe.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "platform_release_policy_runtime_probe.md"
PRODUCT_KEYS = {"construction.standard", "construction.preview"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _check_counts(prefix: str, value: object, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be object")
        return
    for key in ("menu_group_count", "menu_count", "scene_count", "capability_count"):
        if not isinstance(value.get(key), int):
            errors.append(f"{prefix}.{key} must be int")


def _check_delivery(prefix: str, value: object, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be object")
        return
    for key in (
        "product_key",
        "policy_source_kind",
        "nav_source_authority_kind",
        "capability_source_authority_kind",
    ):
        if not isinstance(value.get(key), str):
            errors.append(f"{prefix}.{key} must be string")
    for key in ("policy_empty",):
        if not isinstance(value.get(key), bool):
            errors.append(f"{prefix}.{key} must be bool")
    for key in (
        "menu_key_count",
        "scene_key_count",
        "capability_key_count",
        "nav_leaf_count",
        "stable_leaf_count",
        "native_preview_leaf_count",
        "delivered_menu_leaf_count",
        "group_count",
    ):
        if not isinstance(value.get(key), int):
            errors.append(f"{prefix}.{key} must be int")


def main() -> int:
    payload = _load_json(REPORT_JSON)
    errors: list[str] = []

    if not payload:
        errors.append(f"missing or invalid json: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    else:
        if not isinstance(payload.get("ok"), bool):
            errors.append("ok must be bool")
        for key in ("db", "probe_user_login"):
            if not isinstance(payload.get(key), str) or not payload.get(key):
                errors.append(f"{key} must be non-empty string")
        if not isinstance(payload.get("native_authorized_leaf_count"), int):
            errors.append("native_authorized_leaf_count must be int")
        failures = payload.get("failures")
        if not isinstance(failures, list) or not all(isinstance(item, str) for item in failures):
            errors.append("failures must be string list")
            failures = []
        if payload.get("ok") is True and failures:
            errors.append("ok=true report must not contain failures")
        if payload.get("ok") is False and not failures:
            errors.append("ok=false report must contain failures")

        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, dict):
            errors.append("artifacts must be object")
        else:
            for key in ("json", "markdown"):
                if not isinstance(artifacts.get(key), str) or not artifacts.get(key):
                    errors.append(f"artifacts.{key} must be non-empty string")

        products = payload.get("products")
        if not isinstance(products, list):
            errors.append("products must be list")
            products = []
        seen_products: set[str] = set()
        for idx, product in enumerate(products):
            prefix = f"products[{idx}]"
            if not isinstance(product, dict):
                errors.append(f"{prefix} must be object")
                continue
            product_key = str(product.get("product_key") or "").strip()
            if product_key not in PRODUCT_KEYS:
                errors.append(f"{prefix}.product_key must be one of {sorted(PRODUCT_KEYS)}")
            seen_products.add(product_key)
            if not isinstance(product.get("policy_source_kind"), str) or not product.get("policy_source_kind"):
                errors.append(f"{prefix}.policy_source_kind must be non-empty string")
            _check_counts(f"{prefix}.policy_counts", product.get("policy_counts"), errors)
            _check_counts(f"{prefix}.catalog_counts", product.get("catalog_counts"), errors)
            runtime = product.get("runtime")
            if not isinstance(runtime, dict):
                errors.append(f"{prefix}.runtime must be object")
            else:
                for key in ("user_delivery", "no_native_delivery", "subset_delivery", "admin_delivery"):
                    _check_delivery(f"{prefix}.runtime.{key}", runtime.get(key), errors)
        if seen_products != PRODUCT_KEYS:
            errors.append(f"products must cover {sorted(PRODUCT_KEYS)}")

    if not REPORT_MD.is_file():
        errors.append(f"missing markdown report: {REPORT_MD.relative_to(ROOT).as_posix()}")
    else:
        text = REPORT_MD.read_text(encoding="utf-8")
        for token in ("# Platform Release Policy Runtime Probe", "- ok:", "## Products", "## Failures"):
            if token not in text:
                errors.append(f"markdown report missing token: {token}")

    if errors:
        print("[platform_release_policy_runtime_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[platform_release_policy_runtime_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

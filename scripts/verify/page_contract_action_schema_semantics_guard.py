#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"

ALLOWED_INTENTS = {"ui.contract", "api.data", "execute_button", "file.download"}
ALLOWED_TARGET_KINDS = {"page.refresh", "menu.first_reachable", "route.path", "scene.key"}
UI_CONTRACT_TARGET_KINDS = {"scene.key", "menu.first_reachable", "route.path"}


def _fail(errors: list[str]) -> int:
    print("[page_contract_action_schema_semantics_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _load_builder_module(path: Path) -> ModuleType:
    spec = spec_from_file_location("page_contracts_builder_action_semantics_guard", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _validate_action(page_key: str, action_key: str, action: Any, errors: list[str]) -> None:
    prefix = f"pages.{page_key}.page_orchestration_v1.action_schema.actions.{action_key}"
    if not isinstance(action, dict):
        errors.append(f"{prefix} must be object")
        return

    label = action.get("label")
    intent = str(action.get("intent") or "").strip()
    target = action.get("target")
    visibility = action.get("visibility")

    if not isinstance(label, str) or not label.strip():
        errors.append(f"{prefix}.label must be non-empty string")
    if intent not in ALLOWED_INTENTS:
        errors.append(f"{prefix}.intent invalid: {intent}")
    if not isinstance(target, dict):
        errors.append(f"{prefix}.target must be object")
        return
    if not isinstance(visibility, dict):
        errors.append(f"{prefix}.visibility must be object")
    else:
        roles = visibility.get("roles")
        capabilities = visibility.get("capabilities")
        if "expr" not in visibility:
            errors.append(f"{prefix}.visibility.expr must be present (nullable)")
        if not isinstance(roles, list):
            errors.append(f"{prefix}.visibility.roles must be list")
        if not isinstance(capabilities, list):
            errors.append(f"{prefix}.visibility.capabilities must be list")

    kind = str(target.get("kind") or "").strip()
    if kind:
        if kind not in ALLOWED_TARGET_KINDS:
            errors.append(f"{prefix}.target.kind invalid: {kind}")
        if kind == "route.path":
            path = target.get("path")
            if not isinstance(path, str) or not path.startswith("/"):
                errors.append(f"{prefix}.target.path must be absolute path when kind=route.path")
        if kind == "scene.key":
            scene_key = target.get("scene_key")
            if not isinstance(scene_key, str) or not scene_key.strip():
                errors.append(f"{prefix}.target.scene_key must be non-empty string when kind=scene.key")
        if intent == "ui.contract" and kind not in UI_CONTRACT_TARGET_KINDS:
            errors.append(f"{prefix}.target.kind invalid for ui.contract: {kind}")
    else:
        if intent == "ui.contract":
            errors.append(f"{prefix}.target.kind required for ui.contract")


def _validate_page(page_key: str, page_obj: dict[str, Any], errors: list[str]) -> None:
    orch = page_obj.get("page_orchestration_v1") if isinstance(page_obj.get("page_orchestration_v1"), dict) else {}
    if not isinstance(orch, dict) or not orch:
        return

    action_schema = orch.get("action_schema") if isinstance(orch.get("action_schema"), dict) else {}
    action_registry = action_schema.get("actions") if isinstance(action_schema.get("actions"), dict) else {}
    if not isinstance(action_registry, dict) or not action_registry:
        errors.append(f"pages.{page_key}.page_orchestration_v1.action_schema.actions must be non-empty object")
        return

    for action_key, action in action_registry.items():
        key = str(action_key or "").strip()
        if not key:
            errors.append(f"pages.{page_key}.page_orchestration_v1.action_schema.actions contains empty key")
            continue
        _validate_action(page_key, key, action, errors)

    page = orch.get("page") if isinstance(orch.get("page"), dict) else {}
    global_actions = page.get("global_actions") if isinstance(page.get("global_actions"), list) else []
    seen: set[str] = set()
    for idx, action in enumerate(global_actions):
        prefix = f"pages.{page_key}.page_orchestration_v1.page.global_actions[{idx}]"
        if not isinstance(action, dict):
            errors.append(f"{prefix} must be object")
            continue
        key = str(action.get("key") or "").strip()
        intent = str(action.get("intent") or "").strip()
        label = action.get("label")
        if not key:
            errors.append(f"{prefix}.key must be non-empty")
            continue
        if key in seen:
            errors.append(f"{prefix}.key duplicate: {key}")
        else:
            seen.add(key)
        if key not in action_registry:
            errors.append(f"{prefix}.key not found in action_schema.actions: {key}")
            continue
        if not isinstance(label, str) or not label.strip():
            errors.append(f"{prefix}.label must be non-empty string")
        if intent not in ALLOWED_INTENTS:
            errors.append(f"{prefix}.intent invalid: {intent}")
            continue
        schema_intent = str((action_registry.get(key) or {}).get("intent") or "").strip()
        if schema_intent and schema_intent != intent:
            errors.append(f"{prefix}.intent mismatch with action_schema: {intent} != {schema_intent}")


def main() -> int:
    if not BUILDER.is_file():
        return _fail([f"missing file: {BUILDER}"])

    try:
        builder_mod = _load_builder_module(BUILDER)
    except Exception as exc:  # pragma: no cover
        return _fail([f"load builder failed: {exc}"])

    if not hasattr(builder_mod, "build_page_contracts"):
        return _fail(["build_page_contracts not found in builder module"])

    payload = builder_mod.build_page_contracts({})
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, dict) or not pages:
        return _fail(["page contracts payload missing pages object"])

    errors: list[str] = []
    checked = 0
    for page_key, page_obj in pages.items():
        if not isinstance(page_obj, dict):
            errors.append(f"pages.{page_key} must be object")
            continue
        orch = page_obj.get("page_orchestration_v1")
        if not isinstance(orch, dict):
            continue
        checked += 1
        _validate_page(str(page_key), page_obj, errors)

    if checked == 0:
        errors.append("no page_orchestration_v1 payload found")

    if errors:
        return _fail(errors)

    print(f"[page_contract_action_schema_semantics_guard] PASS (checked_pages={checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

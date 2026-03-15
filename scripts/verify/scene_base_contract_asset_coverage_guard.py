#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
REPOSITORY_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_repository.py"
MODEL_PATH = ROOT / "addons" / "smart_core" / "models" / "ui_base_contract_asset.py"
PRODUCER_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_producer.py"
QUEUE_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_event_queue.py"
TRIGGER_PATH = ROOT / "addons" / "smart_core" / "models" / "ui_base_contract_asset_event_trigger.py"
CRON_XML_PATH = ROOT / "addons" / "smart_core" / "data" / "ui_base_contract_asset_cron.xml"
MANIFEST_PATH = ROOT / "addons" / "smart_core" / "__manifest__.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_wiring(errors: list[str]) -> None:
    text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    _assert(
        "bind_scene_assets" in text,
        "system_init missing bind_scene_assets wiring",
        errors,
    )
    for key in (
        'ui_base_contract_asset_scene_count',
        'ui_base_contract_bound_scene_count',
        'ui_base_contract_missing_scene_count',
    ):
        _assert(key in text, f"system_init missing nav_meta.{key}", errors)


def _validate_builder_coverage(errors: list[str]) -> None:
    text = BUILDER_PATH.read_text(encoding="utf-8")
    _assert(
        "base_contract_bound_scene_count" in text,
        "scene_ready builder missing base_contract_bound_scene_count metric",
        errors,
    )
    _assert(
        "compile_issue_scene_count" in text,
        "scene_ready builder missing compile_issue_scene_count metric",
        errors,
    )
    _assert(
        "scene_compile(" in text,
        "scene_ready builder missing scene_compile invocation",
        errors,
    )


def _validate_asset_model_semantics(errors: list[str]) -> None:
    text = MODEL_PATH.read_text(encoding="utf-8")
    for field_name in (
        "contract_kind",
        "source_type",
        "scope_hash",
        "generated_at",
        "code_version",
    ):
        _assert(field_name in text, f"asset model missing field: {field_name}", errors)
    _assert(
        "_check_single_active_per_scope" in text,
        "asset model missing single-active lifecycle constraint",
        errors,
    )
    _assert(
        "unique(contract_kind, scene_key, role_code, company_id, asset_version)" in text,
        "asset model missing scope+version unique constraint",
        errors,
    )


def _validate_production_wiring(errors: list[str]) -> None:
    model_text = MODEL_PATH.read_text(encoding="utf-8")
    producer_text = PRODUCER_PATH.read_text(encoding="utf-8")
    queue_text = QUEUE_PATH.read_text(encoding="utf-8")
    trigger_text = TRIGGER_PATH.read_text(encoding="utf-8")
    cron_xml = CRON_XML_PATH.read_text(encoding="utf-8")
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    _assert(
        "refresh_assets_for_scene_keys" in model_text and "cron_refresh_ui_base_contract_assets" in model_text,
        "asset model missing production entry methods",
        errors,
    )
    _assert(
        "refresh_ui_base_contract_assets" in producer_text,
        "asset producer missing refresh_ui_base_contract_assets",
        errors,
    )
    _assert(
        "enqueue_scene_keys" in queue_text and "pop_scene_keys" in queue_text,
        "asset queue missing enqueue/pop support",
        errors,
    )
    _assert(
        "event:ir.actions.act_window" in trigger_text and "event:ir.ui.view" in trigger_text and "event:res.groups" in trigger_text,
        "event trigger wiring missing action/view/group hooks",
        errors,
    )
    _assert(
        "pop_scene_keys" in model_text and "source_type = \"event_queue\"" in model_text,
        "asset cron missing queue-consume refresh path",
        errors,
    )
    _assert(
        "model.cron_refresh_ui_base_contract_assets" in cron_xml,
        "cron xml missing ui base contract asset refresh action",
        errors,
    )
    _assert(
        "data/ui_base_contract_asset_cron.xml" in manifest_text,
        "manifest missing ui_base_contract_asset_cron.xml registration",
        errors,
    )


def main() -> int:
    errors: list[str] = []
    for path in (
        BUILDER_PATH,
        SYSTEM_INIT_PATH,
        REPOSITORY_PATH,
        MODEL_PATH,
        PRODUCER_PATH,
        QUEUE_PATH,
        TRIGGER_PATH,
        CRON_XML_PATH,
        MANIFEST_PATH,
    ):
        if not path.is_file():
            errors.append(f"missing required file: {path}")
    if errors:
        print("[verify.scene.base_contract_asset_coverage.guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    try:
        _validate_wiring(errors)
        _validate_builder_coverage(errors)
        _validate_asset_model_semantics(errors)
        _validate_production_wiring(errors)
    except Exception as exc:
        errors.append(str(exc))

    if errors:
        print("[verify.scene.base_contract_asset_coverage.guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[verify.scene.base_contract_asset_coverage.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEMANTICS = ROOT / "addons/smart_core/core/orchestration_semantics.py"
PAGE_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"


def _fail(errors: list[str]) -> int:
    print("[orchestration_semantics_registry_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _load_module(path: Path, name: str):
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module spec: {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stub_odoo_module() -> None:
    if "odoo" in sys.modules:
        return
    odoo_mod = types.ModuleType("odoo")

    class _Datetime:
        @staticmethod
        def now():
            from datetime import datetime

            return datetime.now()

    class _Fields:
        Datetime = _Datetime

    odoo_mod.fields = _Fields  # type: ignore[attr-defined]
    sys.modules["odoo"] = odoo_mod


def _sample_home(role_code: str) -> dict[str, Any]:
    return {
        "capabilities": [{"key": "a", "state": "READY", "ui_label": "A", "default_payload": {"route": "/s/projects.list"}}],
        "scenes": [{"key": "projects.list"}],
        "nav": [{"key": "menu:1"}],
        "role_surface": {"role_code": role_code},
    }


def main() -> int:
    errors: list[str] = []
    if not SEMANTICS.is_file():
        return _fail([f"missing file: {SEMANTICS.relative_to(ROOT).as_posix()}"])
    if not PAGE_BUILDER.is_file():
        return _fail([f"missing file: {PAGE_BUILDER.relative_to(ROOT).as_posix()}"])
    if not HOME_BUILDER.is_file():
        return _fail([f"missing file: {HOME_BUILDER.relative_to(ROOT).as_posix()}"])

    try:
        sem = _load_module(SEMANTICS, "orchestration_semantics_registry_guard_semantics")
        page_builder = _load_module(PAGE_BUILDER, "orchestration_semantics_registry_guard_page_builder")
        _stub_odoo_module()
        home_builder = _load_module(HOME_BUILDER, "orchestration_semantics_registry_guard_home_builder")
    except Exception as exc:  # pragma: no cover
        return _fail([f"load module failed: {exc}"])

    sem_block_types = set(getattr(sem, "BLOCK_TYPES", ()) or ())
    sem_tones = set(getattr(sem, "STATE_TONES", ()) or ())
    sem_progress = set(getattr(sem, "PROGRESS_STATES", ()) or ())

    page_block_types: set[str] = set()
    page_tones: set[str] = set()
    page_progress: set[str] = set()
    # page builder has no exported block type constant; extract from generated payload.
    page_payload = page_builder.build_page_contracts({})
    pages = page_payload.get("pages") if isinstance(page_payload, dict) else {}
    if isinstance(pages, dict):
        for page_obj in pages.values():
            if not isinstance(page_obj, dict):
                continue
            orch = page_obj.get("page_orchestration_v1")
            if not isinstance(orch, dict):
                continue
            state_schema = orch.get("state_schema") if isinstance(orch.get("state_schema"), dict) else {}
            tones = state_schema.get("tones") if isinstance(state_schema.get("tones"), dict) else {}
            business_states = (
                state_schema.get("business_states") if isinstance(state_schema.get("business_states"), dict) else {}
            )
            page_tones.update(str(k).strip() for k in tones.keys() if str(k).strip())
            page_progress.update(str(k).strip() for k in business_states.keys() if str(k).strip())
            zones = orch.get("zones") if isinstance(orch.get("zones"), list) else []
            for zone in zones:
                if not isinstance(zone, dict):
                    continue
                for block in zone.get("blocks") if isinstance(zone.get("blocks"), list) else []:
                    if not isinstance(block, dict):
                        continue
                    block_type = str(block.get("block_type") or "").strip()
                    if block_type:
                        page_block_types.add(block_type)

    home_payload = home_builder.build_workspace_home_contract(_sample_home("pm"))
    home_protocol = home_payload.get("semantic_protocol") if isinstance(home_payload, dict) else {}
    home_block_types = set(home_protocol.get("block_types")) if isinstance(home_protocol, dict) and isinstance(home_protocol.get("block_types"), list) else set()
    home_tones = set(home_protocol.get("state_tones")) if isinstance(home_protocol, dict) and isinstance(home_protocol.get("state_tones"), list) else set()
    home_progress = set(home_protocol.get("progress_states")) if isinstance(home_protocol, dict) and isinstance(home_protocol.get("progress_states"), list) else set()

    unknown_page_block_types = sorted(page_block_types - sem_block_types)
    if unknown_page_block_types:
        errors.append(
            "page_contract block_types contain unknown values not in registry: "
            + ", ".join(unknown_page_block_types)
        )
    if not page_block_types:
        errors.append("page_contract block_types should not be empty")
    if page_tones != sem_tones:
        errors.append(f"page_contract state_schema.tones mismatch registry: expected={sorted(sem_tones)} got={sorted(page_tones)}")
    if page_progress != sem_progress:
        errors.append(
            f"page_contract state_schema.business_states mismatch registry: expected={sorted(sem_progress)} got={sorted(page_progress)}"
        )
    if home_block_types != sem_block_types:
        errors.append(f"workspace_home semantic_protocol.block_types mismatch registry: expected={sorted(sem_block_types)} got={sorted(home_block_types)}")
    if home_tones != sem_tones:
        errors.append(f"workspace_home semantic_protocol.state_tones mismatch registry: expected={sorted(sem_tones)} got={sorted(home_tones)}")
    if home_progress != sem_progress:
        errors.append(
            f"workspace_home semantic_protocol.progress_states mismatch registry: expected={sorted(sem_progress)} got={sorted(home_progress)}"
        )

    if errors:
        return _fail(errors)

    print("[orchestration_semantics_registry_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

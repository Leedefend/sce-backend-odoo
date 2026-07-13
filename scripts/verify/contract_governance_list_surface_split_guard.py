#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
LIST_SURFACE = ROOT / "addons/smart_core/utils/contract_governance_list_surface.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 4121


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    list_surface_text = _read(LIST_SURFACE)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not list_surface_text:
        errors.append(f"missing list surface module: {LIST_SURFACE.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_list_surface_module()",
            "contract_governance_list_surface.py",
            "def _apply_standard_search_toolbar_labels(data: dict) -> None:",
            "_list_surface.apply_standard_search_toolbar_labels(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing list surface split token: {token}")

    if list_surface_text:
        for token in [
            "def apply_standard_search_toolbar_labels(",
            "\"row_open\": \"打开\"",
            "payload[\"view_mode\"] = payload.get(\"view_mode\") or \"form\"",
        ]:
            if token not in list_surface_text:
                errors.append(f"list surface module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in list_surface_text:
                errors.append(f"list surface module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_list_surface_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_list_surface_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_list_surface_split_under_guard")
        data = {
            "search": {},
            "views": {
                "tree": {
                    "row_actions": [
                        {"name": "open_form", "payload": {}},
                    ],
                },
            },
        }
        governance._apply_standard_search_toolbar_labels(data)
        labels = ((data.get("search") or {}).get("ui_labels") or {})
        action = (((data.get("views") or {}).get("tree") or {}).get("row_actions") or [{}])[0]
        if labels.get("row_open") != "打开":
            errors.append("list surface labels must include row_open")
        if action.get("label") != "打开" or (action.get("payload") or {}).get("view_mode") != "form":
            errors.append("list surface row open action semantics were not applied")

    if errors:
        print("[contract_governance_list_surface_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_list_surface_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

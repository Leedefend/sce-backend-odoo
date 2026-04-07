#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

MENU_FILES = [
    ROOT / "addons/smart_construction_core/views",
    ROOT / "addons/smart_enterprise_base/views",
]
ACTION_FILES = [
    ROOT / "addons/smart_construction_core/actions",
    ROOT / "addons/smart_construction_core/views",
    ROOT / "addons/smart_enterprise_base/views",
]

RECORD_ID_RE = re.compile(r'<record\s+id="([^"]+)"\s+model="(ir\.actions\.[^"]+)"')
MENU_ACTION_RE = re.compile(r'action="([^"]+)"')
PCTD_RE = re.compile(r"%\(([^)]+)\)d")


def _collect_action_ids() -> set[str]:
    action_ids: set[str] = set()
    for directory in ACTION_FILES:
        if not directory.exists():
            continue
        for file_path in directory.rglob("*.xml"):
            text = file_path.read_text(encoding="utf-8")
            for xmlid, _model in RECORD_ID_RE.findall(text):
                action_ids.add(xmlid)
    return action_ids


def _normalize_action_ref(raw: str) -> str:
    raw = raw.strip()
    pct = PCTD_RE.search(raw)
    if pct:
        raw = pct.group(1)
    if "." in raw:
        raw = raw.split(".", 1)[1]
    return raw.strip()


def _collect_menu_refs() -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for directory in MENU_FILES:
        if not directory.exists():
            continue
        for file_path in directory.rglob("*.xml"):
            text = file_path.read_text(encoding="utf-8")
            for raw in MENU_ACTION_RE.findall(text):
                refs.append((str(file_path.relative_to(ROOT)), _normalize_action_ref(raw)))
    return refs


def main() -> None:
    action_ids = _collect_action_ids()
    menu_refs = _collect_menu_refs()

    if not menu_refs:
        raise RuntimeError("no menu action refs found in scoped view files")

    missing: list[str] = []
    checked = 0
    for file_rel, action_ref in menu_refs:
        if not action_ref:
            continue
        checked += 1
        if action_ref not in action_ids:
            missing.append(f"{file_rel}:{action_ref}")

    if missing:
        sample = ", ".join(missing[:10])
        raise RuntimeError(f"menu action refs unresolved: count={len(missing)} sample={sample}")

    print(
        "[native_business_fact_action_openability_verify] "
        f"PASS menu_action_refs={checked} action_ids={len(action_ids)}"
    )


if __name__ == "__main__":
    main()

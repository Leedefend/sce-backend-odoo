#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "frontend/apps/web/src/config.ts"
FRONTEND_FILES = [
    ROOT / "frontend/apps/web/src/stores/session.ts",
    ROOT / "frontend/apps/web/src/views/ActionView.vue",
    ROOT / "frontend/apps/web/src/views/SceneView.vue",
    ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    config_text = _read(CONFIG)
    if "const startupRootXmlid = String(import.meta.env.VITE_STARTUP_ROOT_XMLID ?? 'smart_construction_core.menu_sc_root').trim();" not in config_text:
        errors.append("config.ts must expose VITE_STARTUP_ROOT_XMLID with the construction root only as compatibility default")
    if "const localDevPinnedDb = isLocalDevRuntime && !runtimeDb && !localBlockedEnvDb ? 'sc_demo' : '';" not in config_text:
        errors.append("config.ts local dev fallback must not override explicit URL or VITE_ODOO_DB database")
    if "const pinnedDb = runtimeDb || localBlockedEnvDb || enforcedDb || localDevPinnedDb;" not in config_text:
        errors.append("config.ts must prefer URL db, then VITE_ODOO_DB, before local sc_demo fallback")
    if "startupRootXmlid," not in config_text:
        errors.append("config.ts must publish startupRootXmlid in runtime config")

    for path in FRONTEND_FILES:
        text = _read(path)
        rel = path.relative_to(ROOT)
        if "root_xmlid: 'smart_construction_core.menu_sc_root'" in text:
            errors.append(f"{rel} still hardcodes construction root_xmlid in system.init params")
        if "system.init" in text and "root_xmlid" in text and "config.startupRootXmlid" not in text:
            errors.append(f"{rel} must route system.init root_xmlid through config.startupRootXmlid")

    if errors:
        print("[frontend_platform_runtime_config_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_platform_runtime_config_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

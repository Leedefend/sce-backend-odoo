#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "frontend/apps/web/src/config.ts"
INDEX_HTML = ROOT / "frontend/apps/web/index.html"
FRONTEND_FILES = [
    ROOT / "frontend/apps/web/src/stores/session.ts",
    ROOT / "frontend/apps/web/src/views/ActionView.vue",
    ROOT / "frontend/apps/web/src/views/SceneView.vue",
    ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
    ROOT / "frontend/apps/web/src/views/LoginView.vue",
    ROOT / "frontend/apps/web/src/router/index.ts",
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
    if "const appTitle = String(import.meta.env.VITE_APP_TITLE ?? '智能施工企业管理平台').trim();" not in config_text:
        errors.append("config.ts must expose VITE_APP_TITLE with the construction title only as compatibility default")
    if "appBrand," not in config_text:
        errors.append("config.ts must publish appBrand in runtime config")
    for env_key in (
        "VITE_BRAND_NAME",
        "VITE_BRAND_SUBTITLE",
        "VITE_PRODUCT_BADGE",
        "VITE_CAPABILITY_PROJECT",
        "VITE_VALUE_LINE_1",
    ):
        if env_key not in config_text:
            errors.append(f"config.ts missing custom frontend branding env: {env_key}")

    index_text = _read(INDEX_HTML)
    if "<title>智能施工企业管理平台</title>" in index_text:
        errors.append("index.html must not hardcode the construction product title before custom config loads")

    for path in FRONTEND_FILES:
        text = _read(path)
        rel = path.relative_to(ROOT)
        if "root_xmlid: 'smart_construction_core.menu_sc_root'" in text:
            errors.append(f"{rel} still hardcodes construction root_xmlid in system.init params")
        if "system.init" in text and "root_xmlid" in text and "config.startupRootXmlid" not in text:
            errors.append(f"{rel} must route system.init root_xmlid through config.startupRootXmlid")
        if rel.as_posix() != "frontend/apps/web/src/config.ts":
            for token in (
                "智能施工企业管理平台",
                "工程项目全生命周期管理系统",
                "SCEMS · v1.0",
                "Smart Construction Enterprise Management System",
                "项目全过程管理",
                "合同成本联动",
                "资金支付协同",
                "风险预警驾驶舱",
            ):
                if token in text:
                    errors.append(f"{rel} must not hardcode construction branding token: {token}")

    if errors:
        print("[frontend_platform_runtime_config_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_platform_runtime_config_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

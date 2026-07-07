#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "frontend/apps/web/src/config.ts"
DB_CONTEXT = ROOT / "frontend/apps/web/src/services/dbContext.ts"
INDEX_HTML = ROOT / "frontend/apps/web/index.html"
FRONTEND_STATIC_BUILD = ROOT / "scripts/dev/frontend_static_build.sh"
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
    db_context_text = _read(DB_CONTEXT)
    static_build_text = _read(FRONTEND_STATIC_BUILD)
    if "const startupRootXmlid = String(import.meta.env.VITE_STARTUP_ROOT_XMLID ?? 'smart_construction_core.menu_sc_root').trim();" not in config_text:
        errors.append("config.ts must expose VITE_STARTUP_ROOT_XMLID with the construction root only as compatibility default")
    if "const localDevPinnedDb = isLocalDevRuntime && !runtimeDb && !localBlockedEnvDb ? 'sc_demo' : '';" not in config_text:
        errors.append("config.ts local dev fallback must not override explicit URL or VITE_ODOO_DB database")
    if "const envDbLocked = envDb && String(import.meta.env.VITE_ODOO_DB_LOCKED ?? '1').trim() !== '0';" not in config_text:
        errors.append("config.ts must expose VITE_ODOO_DB_LOCKED and lock explicit env db by default")
    if "const platformAdminDb = String(import.meta.env.VITE_PLATFORM_ADMIN_DB ?? '').trim();" not in config_text:
        errors.append("config.ts must expose VITE_PLATFORM_ADMIN_DB for platform-admin entry")
    if "isPlatformAdminEntryRuntime()" not in config_text:
        errors.append("config.ts must consume runtime platform-admin entry detection")
    if "window.location.pathname.startsWith('/platform-admin')" not in db_context_text:
        errors.append("dbContext.ts must recognize the explicit platform-admin entry path")
    if "export function resolveConfiguredDb" not in db_context_text:
        errors.append("dbContext.ts must expose runtime configured db resolution")
    if "export function resolveLoginRoutingDb" not in db_context_text:
        errors.append("dbContext.ts must expose backend login routing db resolution")
    if "export function isConfiguredDbPinned" not in db_context_text:
        errors.append("dbContext.ts must expose runtime db pinned detection")
    if "isPlatformAdminEntryRuntime() && PLATFORM_ADMIN_DB" not in db_context_text:
        errors.append("dbContext.ts must let platform-admin db override the locked tenant db at request time")
    if "resolveConfiguredDb(String(config.odooDb || '').trim())" not in _read(ROOT / "frontend/apps/web/src/api/client.ts"):
        errors.append("api/client.ts must resolve db at request time, not only config module load time")
    if "resolveLoginRoutingDb()" not in _read(ROOT / "frontend/apps/web/src/api/client.ts"):
        errors.append("api/client.ts must route login through backend platform login contract db")
    session_text = _read(ROOT / "frontend/apps/web/src/stores/session.ts")
    if "isConfiguredDbPinned() ? configuredDb : dbOverride || configuredDb" not in session_text:
        errors.append("session.ts must use runtime db pinning during login")
    if "function currentDbScope()" not in session_text or "scopedTokenStorageKey()" not in session_text:
        errors.append("session.ts must scope session/token storage by runtime resolved db")
    if "sessionDb" not in session_text or "result.session?.db" not in session_text:
        errors.append("session.ts must consume backend-returned session db")
    if "const DB_SCOPE = String(config.odooDb" in session_text:
        errors.append("session.ts must not freeze db scope from config module load time")
    if "const pinnedDb = isPlatformAdminEntry && platformAdminDb" not in config_text:
        errors.append("config.ts must allow only the explicit platform-admin db to override locked tenant db")
    if ": envDbLocked ? localBlockedEnvDb : runtimeDb || localBlockedEnvDb || enforcedDb || localDevPinnedDb;" not in config_text:
        errors.append("config.ts must prevent URL db from overriding locked VITE_ODOO_DB")
    if "startupRootXmlid," not in config_text:
        errors.append("config.ts must publish startupRootXmlid in runtime config")
    if "const appTitle = String(import.meta.env.VITE_APP_TITLE ?? '智能施工企业管理平台').trim();" not in config_text:
        errors.append("config.ts must expose VITE_APP_TITLE with the construction title only as compatibility default")
    if "appBrand," not in config_text:
        errors.append("config.ts must publish appBrand in runtime config")
    if "VITE_BUILD_MODE" not in static_build_text:
        errors.append("frontend_static_build.sh must route Vite mode through VITE_BUILD_MODE")
    if "prod|production)" not in static_build_text or 'VITE_BUILD_MODE="${VITE_BUILD_MODE:-production}"' not in static_build_text:
        errors.append("frontend_static_build.sh must map prod/production env to Vite production mode")
    if "dev|daily|development)" not in static_build_text or 'VITE_BUILD_MODE="${VITE_BUILD_MODE:-development}"' not in static_build_text:
        errors.append("frontend_static_build.sh must map dev/daily/development env to Vite development mode")
    if 'exec vite build --mode "${VITE_BUILD_MODE}"' not in static_build_text:
        errors.append("frontend_static_build.sh must invoke vite build with the resolved VITE_BUILD_MODE")
    if "grep -Rqs" not in static_build_text or '"sc_prod"' not in static_build_text or "FRONTEND_DIST_ABS" not in static_build_text:
        errors.append("frontend_static_build.sh must reject sc_prod assets for non-production builds")
    if "-C frontend/apps/web build" in static_build_text:
        errors.append("frontend_static_build.sh must not call the frontend package build script without an explicit Vite mode")
    for env_key in (
        "VITE_BRAND_NAME",
        "VITE_BRAND_SUBTITLE",
        "VITE_PRODUCT_BADGE",
        "VITE_SHELL_LOGO_TEXT",
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
    shell_text = _read(ROOT / "frontend/apps/web/src/layouts/AppShell.vue")
    router_text = _read(ROOT / "frontend/apps/web/src/router/index.ts")
    login_text = _read(ROOT / "frontend/apps/web/src/views/LoginView.vue")
    if "/platform-admin/login" not in router_text or "platform-admin-login" not in router_text:
        errors.append("router/index.ts must expose a dedicated platform-admin login route")
    if "wantsPlatformAdminEntry" not in router_text:
        errors.append("router/index.ts must preserve platform-admin entry when redirecting unauthenticated users")
    if "/?platform_admin=1" not in login_text:
        errors.append("LoginView.vue must preserve platform-admin entry after platform admin login")
    if "isPlatformAdminEntryRuntime() ? '/?platform_admin=1'" not in login_text:
        errors.append("LoginView.vue must use runtime platform-admin entry detection after client-side route changes")
    if "watch(\n  () => route.fullPath" not in login_text or "resolveConfiguredDb(String(config.odooDb || '').trim())" not in login_text:
        errors.append("LoginView.vue must refresh displayed locked db after route changes")
    if '<div class="logo">SC</div>' in shell_text:
        errors.append("AppShell.vue must not hardcode SC logo text")
    if 'v-if="showRecordContext"' not in shell_text:
        errors.append("AppShell.vue must hide unavailable record context instead of showing project-model install errors")
    if "<span>当前项目：</span>" in shell_text:
        errors.append("AppShell.vue must not hardcode project context label")
    if "data-platform-app-catalog" not in shell_text or "app.catalog" not in shell_text or "app.open" not in shell_text:
        errors.append("AppShell.vue must expose platform-published app catalog and open apps through app.catalog/app.open")
    if "const isPlatformAdmin = computed(() => session.user?.is_platform_admin === true)" not in shell_text:
        errors.append("AppShell.vue must derive platform-published app visibility from session.user.is_platform_admin")
    if "isPlatformAdmin.value && (visiblePublishedApps.value.length > 0 || appCatalogLoading.value)" not in shell_text:
        errors.append("AppShell.vue must not render the platform-published app shell for regular users")
    if "session.user?.is_platform_admin !== true" not in shell_text:
        errors.append("AppShell.vue must not request app.catalog for regular users")

    if errors:
        print("[frontend_platform_runtime_config_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[frontend_platform_runtime_config_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

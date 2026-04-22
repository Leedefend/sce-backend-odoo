{
  "next_candidate_family": "verifier_runtime_storage_baseline_mismatch",
  "family_scope": [
    "scripts/verify/unified_system_menu_click_usability_smoke.mjs",
    "frontend/apps/web/src/layouts/AppShell.vue",
    "frontend/apps/web/src/stores/session.ts"
  ],
  "reason": "The verifier reads menu leaves only from localStorage session cache fields `releaseNavigationTree/menuTree`, while the active sidebar now consumes `useNavigationMenu().tree` loaded from `/api/menu/navigation`. AppShell mounts by calling `navigationMenu.loadNavigation()` directly, and only falls back to `session.loadAppInit()` on error, so the custom frontend can render a real menu tree even when the verifier's session-cache source remains empty or stale."
}

# FE Nav MenuId Parity Screen DE

```json
{
  "next_candidate_family": "explained_nav_runtime_menuid_ownership_mismatch",
  "family_scope": [
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T083057Z/summary.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T083057Z/cases.json",
    "scripts/verify/unified_system_menu_click_usability_smoke.mjs",
    "frontend/apps/web/src/composables/useNavigationMenu.ts",
    "frontend/apps/web/src/stores/session.ts",
    "frontend/apps/web/src/views/MenuView.vue",
    "frontend/apps/web/src/app/resolvers/menuResolverCore.js"
  ],
  "reason": "The latest smoke switched nav_source to nav_explained.tree and expanded the leaf set from 31 to 60, but 29 failures now stop directly at /m/:menuId with 'Menu resolve failed / menu not found'. Those failed leaves are dominated by common-entry ids such as 396-405 and carry no scene_key or action_id in the explained tree payload, while runtime /m resolution still searches only session.releaseNavigationTree and session.menuTree via resolveMenuActionCore(findMenuNode). AppShell side navigation now consumes useNavigationMenu().tree from /api/menu/navigation, but router/MenuView/session resolver ownership still remains on releaseNavigationTree/menuTree. This is therefore not a pure verifier sampling issue anymore; the stronger next family is explained-nav versus runtime menu-id ownership mismatch, and the next bounded batch should screen ownership and legal source of truth before any new resolver patch."
}
```

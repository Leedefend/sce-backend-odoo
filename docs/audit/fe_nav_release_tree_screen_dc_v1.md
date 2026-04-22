{
  "next_candidate_family": "verifier_release_tree_source_selection",
  "family_scope": [
    "scripts/verify/unified_system_menu_click_usability_smoke.mjs",
    "frontend/apps/web/src/stores/session.ts",
    "frontend/apps/web/src/router/index.ts",
    "frontend/apps/web/src/views/MenuView.vue",
    "frontend/apps/web/src/layouts/AppShell.vue"
  ],
  "reason": "The runtime currently exposes three menu sources with different priority rules. AppShell renders the actual sidebar from `useNavigationMenu().tree`, but verifier, router, MenuView, and session active-tree defaults all prioritize `releaseNavigationTree` before `menuTree`. Because the latest artifacts stayed fixed on `nav_source=release_tree` while failure membership drifted, the stronger next family is verifier/runtime source selection around releaseNavigationTree trust, not another scene-contract patch."
}

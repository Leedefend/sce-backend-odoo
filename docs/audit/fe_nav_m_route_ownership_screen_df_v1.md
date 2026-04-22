# FE Nav M Route Ownership Screen DF

```json
{
  "next_candidate_family": "verifier_explained_nav_contract_consumer_mismatch",
  "family_scope": [
    "scripts/verify/unified_system_menu_click_usability_smoke.mjs",
    "frontend/apps/web/src/composables/useNavigationMenu.ts",
    "frontend/apps/web/src/layouts/AppShell.vue",
    "frontend/apps/web/src/components/MenuTree.vue",
    "frontend/apps/web/src/views/MenuView.vue",
    "frontend/apps/web/src/router/index.ts",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T083057Z/cases.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T083057Z/summary.json"
  ],
  "reason": "The product sidebar does not treat explained navigation leaves as generic `/m/:menuId` entries. AppShell consumes `useNavigationMenu().tree`, MenuTree emits the explained node itself, and `navigateByExplainedMenuNode` only pushes `node.route`. For the 29 `menu not found` failures, the frozen cases show empty `route`, empty `scene_key`, and `action_id=0`, so the real sidebar would not push `/m/:menuId` for them at all. The current verifier instead flattens `nav_explained.tree` by reading only `node.meta.route/scene_key/action_id`, while the frontend consumer normalizes explained payload from top-level `row.route`, `row.entry_target`, `row.target_type`, and `row.is_clickable`. This contract-consumer mismatch collapses explained-nav leaves into synthetic `/m/:menuId` probes and produces false ownership pressure on the runtime resolver. The stronger next family is therefore verifier_explained_nav_contract_consumer_mismatch, and the next bounded batch should repair verifier consumption of explained navigation before reopening runtime `/m` ownership."
}
```

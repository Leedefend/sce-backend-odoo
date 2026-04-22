{
  "next_candidate_family": "frontend_compatibility_tail_cleanup",
  "family_scope": [
    "frontend/apps/web/src/composables/useNavigationMenu.ts",
    "frontend/apps/web/src/components/MenuTree.vue"
  ],
  "reason": "The scan froze six residual candidates. Five stay inside frontend consumer or renderer compatibility-tail behavior, while the only backend-linked candidate is the dashboard body mismatch after navigation has already succeeded and therefore is not the strongest next family for the menu-specific usability line."
}

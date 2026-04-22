[
  {
    "path": "frontend/apps/web/src/composables/useNavigationMenu.ts:48",
    "module": "frontend nav menu consumer",
    "feature": "unresolved native-action fallback",
    "reason": "When a menu route still arrives as /native/action and scene authority cannot be resolved locally, the consumer redirects to /workbench with a contract-missing diagnostic instead of preserving a menu-scoped disabled or explainable state."
  },
  {
    "path": "frontend/apps/web/src/composables/useNavigationMenu.ts:97",
    "module": "frontend nav menu consumer",
    "feature": "target_type semantic compression",
    "reason": "normalizeTargetType rewrites native, directory, and unavailable into action, which leaves the consumer with less distinct menu usability state than the backend contract originally emitted."
  },
  {
    "path": "frontend/apps/web/src/composables/useNavigationMenu.ts:111",
    "module": "frontend nav menu consumer",
    "feature": "directory auto-route inheritance",
    "reason": "pickFirstActionRoute can make a parent menu appear directly navigable by inheriting the first descendant route, which may blur scene grouping versus explicit entry intent on scenarized navigation trees."
  },
  {
    "path": "frontend/apps/web/src/components/MenuTree.vue:89",
    "module": "frontend nav tree renderer",
    "feature": "frontend label semantic rewriting",
    "reason": "nodeLabel applies hard-coded business and role translations in the renderer, so menu wording still depends partly on frontend local rewriting instead of fully backend-supplied display semantics."
  },
  {
    "path": "frontend/apps/web/src/components/MenuTree.vue:174",
    "module": "frontend nav tree renderer",
    "feature": "raw unavailable reason exposure",
    "reason": "Disabled-title copy is derived straight from reason_code when present, which may leave scenarized menu usability dependent on backend internal reason tokens instead of a formal user-facing explain surface."
  },
  {
    "path": "docs/verify/project_dashboard_profile_timeout_inspect_ch_v1.md:23",
    "module": "live runtime evidence",
    "feature": "menu-visible body-mismatch frontier",
    "reason": "The latest live snapshot shows has_menu_tree=true with \"导航菜单 ... 8 项\" while the main scene body remains stalled on dashboard loading, so current usability evidence points to a post-navigation semantic mismatch rather than a missing menu tree itself."
  }
]

{
  "next_candidate_family": "release_tree_runtime_drift_screen",
  "family_scope": [
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T080748Z/summary.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T080748Z/cases.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T082009Z/summary.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T082009Z/cases.json"
  ],
  "reason": "The latest two artifacts keep leaf_count=31 and fail_count=26 with nav_source fixed at release_tree. The family split barely changes (contract_context_missing 17->16, scene_identity_missing 9->10), while new failing ids 941991035 and 325 appear and two old failures disappear. This pattern does not support a single scene-context projection fix as the dominant lever; it points instead to release_tree runtime drift or unstable release-navigation ownership as the stronger next family to classify."
}

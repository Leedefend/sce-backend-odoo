{
  "next_candidate_family": "scene_contract_context_missing",
  "family_scope": [
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T080748Z/summary.json",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T080748Z/cases.json"
  ],
  "reason": "The latest smoke freezes 26 failing leaves. Of those, 17 already carry scene_key but still degrade to workbench with reason=CONTRACT_CONTEXT_MISSING, while only 9 fail with diag=menu_route_missing_scene_identity. The dominant next family is therefore missing scene contract context on scene-known entries, not missing scene identity itself."
}

{
  "next_candidate_family": "frontend_menu_route_context_projection",
  "family_scope": [
    "frontend/apps/web/src/router/index.ts",
    "frontend/apps/web/src/app/resolvers/menuResolver.ts",
    "artifacts/codex/unified-system-menu-click-usability-smoke/20260420T080748Z/cases.json"
  ],
  "reason": "The dominant 17 scene-known failures already carry both scene_key and action_id in the smoke artifacts, but they still end at workbench with only `scene=...` and no carried action/menu context. The menu route projection path confirms this: `resolveScenePathFromMenuResolve(...)` returns only `sceneKey/path/menuId` when `target.scene_key` exists, so the frontend drops actionable context before SceneView can consume it."
}

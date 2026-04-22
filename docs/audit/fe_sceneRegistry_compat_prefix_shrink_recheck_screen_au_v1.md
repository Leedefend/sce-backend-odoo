# FE SceneRegistry Compat Prefix Shrink Recheck Screen AU v1

## classification

```json
{
  "dominant_residual_boundary": "guarded router private compat registration shell plus unresolved native-action fallback",
  "secondary_residual_boundary": "legacy-only compat prefix constant retained in sceneRegistry fallback path",
  "scene_route_primary_source": "entry_target.route",
  "backend_semantic_blocker": "none newly indicated by scan AT"
}
```

## rationale

- `sceneRegistry.ts`
  - compat prefix constant still exists, but it no longer controls the primary `scene.route` source after batch `AS`
  - classification: secondary residual only
- `router/index.ts`
  - private compat route families still exist as registered shell routes, even though they are now scene-first guarded
  - classification: dominant residual because the shell remains reachable and structurally present
- `useNavigationMenu.ts`
  - unresolved `/native/action/:id` still collapses to `/compat/action/:id` when no scene can be resolved
  - classification: part of dominant residual because it is still an active emitter path in the unresolved branch

## decision

- next governance step should verify this classification without reopening repository scan scope
- next implementation batch, if opened later, should target router shell retirement or unresolved native-action fallback before touching the now-secondary `sceneRegistry` fallback constant

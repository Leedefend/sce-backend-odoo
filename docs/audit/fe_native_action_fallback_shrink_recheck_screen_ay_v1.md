# FE Native Action Fallback Shrink Recheck Screen AY v1

## classification

```json
{
  "dominant_residual_boundary": "guarded router private compat registration shell",
  "secondary_residual_boundary": "legacy-only sceneRegistry compat prefix fallback",
  "resolved_from_dominant": "navigation unresolved native-action fallback no longer emits /compat/action/:id",
  "backend_semantic_blocker": "none newly indicated by scan AX"
}
```

## rationale

- `router/index.ts`
  - private compat route families remain structurally registered and reachable as guarded shell routes
  - classification: dominant residual boundary
- `sceneRegistry.ts`
  - compat prefix constant remains only to normalize legacy delivery when public scene route is absent
  - classification: secondary residual only
- `useNavigationMenu.ts`
  - unresolved native-action branch still exists as a recognition point, but no longer emits private compat route
  - classification: removed from dominant residual boundary in this bounded screen

## decision

- next governance step should verify this classification without reopening repository scan scope
- next implementation batch, if opened later, should target guarded router compat shell retirement before touching the now-secondary sceneRegistry fallback constant

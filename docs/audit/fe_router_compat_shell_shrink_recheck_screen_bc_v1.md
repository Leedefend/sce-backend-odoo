# FE Router Compat Shell Shrink Recheck Screen BC v1

## classification

```json
{
  "dominant_residual_boundary": "legacy-only sceneRegistry compat prefix fallback",
  "secondary_residual_boundary": "redirect-only router compat entry registration",
  "resolved_from_dominant": "router compat shell no longer owns shell-page rendering",
  "backend_semantic_blocker": "none newly indicated by scan BB"
}
```

## rationale

- `sceneRegistry.ts`
  - compat prefix constant remains as the only remaining logic path that still interprets `/compat/*` as legacy delivery input
  - classification: dominant residual boundary
- `router/index.ts`
  - compat routes remain structurally present, but only as redirect-only named entry points
  - classification: secondary residual compatibility shell, no longer dominant boundary

## decision

- next governance step should verify this classification without reopening repository scan scope
- next implementation batch, if opened later, should target retiring or narrowing the remaining legacy-only sceneRegistry compat prefix fallback before considering whether router compatibility entry registration should stay for external backward-compat reasons

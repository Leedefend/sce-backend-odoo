# FE SceneRegistry Legacy Compat Fallback Shrink Recheck Screen BG v1

## classification

```json
{
  "dominant_residual_boundary": "redirect-only router compatibility entry registration",
  "secondary_residual_boundary": "tiny bounded sceneRegistry legacy compat branch",
  "resolved_from_dominant": "global sceneRegistry compat prefix normalization baseline",
  "backend_semantic_blocker": "none newly indicated by scan BF"
}
```

## rationale

- `router/index.ts`
  - compat routes remain structurally registered and callable by name/path
  - even though they are redirect-only, they remain the larger externally visible compatibility surface
  - classification: dominant residual boundary
- `sceneRegistry.ts`
  - only one bounded `isLegacyCompatRoute(...)` branch remains inside scene-ready conversion
  - classification: secondary residual only

## decision

- next governance step should verify this classification without reopening repository scan scope
- next implementation batch, if opened later, should first decide whether compatibility entry registration should remain for backward-compat reasons or be further retired

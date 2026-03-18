# Frontend Architecture Current State Audit v1

## Scope

- Audit-only wave (no refactor), covering `frontend/apps/web/src`.
- Focus: `AppShell`, `ActionView`, `HomeView`, `RecordView`, `SceneView`, and `app/contracts|runtime|resolvers`.

## Baseline

Target six layers:

1. Shell
2. Routing & Navigation
3. Contract Consumption
4. Runtime Execution
5. Page Assembly
6. Render Components

## Current Status (Summary)

- Shell exists but contains heuristic/business extras (`AppShell.vue`).
- Routing exists but route orchestration is still partly page-owned (`SceneView.vue`).
- Contract layer is real but mostly ActionView-scoped (`app/contracts/*`).
- Runtime extraction is substantial (`app/runtime`: 56 files), but still heavily page-coupled.
- Page Assembly layer is missing (`app/assemblers` not present).
- Render layer is mixed: reusable render components exist, but some pages/components still import APIs directly.

## Key Findings

- `ActionView.vue` remains a transition super-component (4020 lines), despite meaningful extraction.
- `HomeView.vue` still includes keyword-based semantic inference.
- `RecordView.vue` and `SceneView.vue` still host broad orchestration logic.
- Strict mode source-of-truth is correctly backend-driven (`app/contractStrictMode.ts`).

## Conclusion

Current frontend is in a **runtime-splitting transition state**:

- better than legacy page stacking,
- not yet a closed six-layer architecture.

Primary bottleneck: **missing Page Assembly layer** (page VM ownership).

## Next Input (for implementation wave)

1. Establish ActionView page-assembly model.
2. Move remaining state/process ownership out of `ActionView.vue`.
3. Then apply the same pattern to `HomeView.vue`.


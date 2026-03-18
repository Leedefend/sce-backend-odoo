# Frontend Architecture Violation Inventory v1

## Severity

- `P1`: architecture-closure blocker.
- `P2`: near-term closure needed.
- `P3`: optimization/cleanup.

## Top Violations

- `ActionView.vue` still owns central load/action/batch orchestration (`P1`).
- `HomeView.vue` still uses keyword-based business inference (`P1`).
- `SceneView.vue` still performs fallback scene reconstruction + route orchestration in-page (`P2`).
- `AppShell.vue` still includes business heuristics and trace export concerns (`P2/P3`).
- Render/API purity breaks in `ContractFormPage.vue` and `ViewRelationalRenderer.vue` (`P2`).

## Closure Priority

1. ActionView ownership transfer to runtime + page assembly.
2. Remove HomeView business keyword heuristics.
3. Introduce canonical Page Assembly entrypoint.


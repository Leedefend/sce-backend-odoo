# Frontend Architecture Violation Inventory v1

## Severity Definition

- `P1`: blocks architecture closure this wave.
- `P2`: should be addressed in near-term wave.
- `P3`: optimization/clean-up after core closure.

## Violation List

| Location | Violation Type | Description | Severity | Target Layer |
| --- | --- | --- | --- | --- |
| `frontend/apps/web/src/views/ActionView.vue:2856` | Page owns central runtime | `load()` still orchestrates full contract->request->route->state pipeline | P1 | Runtime + Page Assembly |
| `frontend/apps/web/src/views/ActionView.vue:2678` | Page owns action runtime | `runContractAction()` handles mutation/navigation/refresh flow in-view | P1 | Runtime |
| `frontend/apps/web/src/views/ActionView.vue:3412` | Page owns batch runtime | batch lifecycle still coordinated in page | P1 | Runtime |
| `frontend/apps/web/src/views/ActionView.vue:803` | State center in page | large ref/computed state surface remains in super component | P1 | Page Assembly |
| `frontend/apps/web/src/views/HomeView.vue:1228` | Keyword business inference | todo action labels inferred by keywords | P1 | Contract Consumption |
| `frontend/apps/web/src/views/HomeView.vue:1046` | Heuristic inference helper | keyword list/inclusion logic still drives business semantics | P1 | Contract Consumption |
| `frontend/apps/web/src/views/SceneView.vue:280` | Page rebuilds scene model | fallback scene constructed directly from scene-ready deep fields | P2 | Contract Consumption + Routing |
| `frontend/apps/web/src/views/SceneView.vue:321` | Page route orchestration overload | scene resolve + route rewrite mixed in one view flow | P2 | Routing |
| `frontend/apps/web/src/layouts/AppShell.vue:296` | Shell contains business heuristics | delivery role text normalization and role mapping in shell | P2 | Shell |
| `frontend/apps/web/src/layouts/AppShell.vue:515` | Shell contains trace/export ops | debug/trace action export logic mixed into shell runtime | P3 | Shell support module |
| `frontend/apps/web/src/pages/ContractFormPage.vue:300` | Render/API boundary broken | page component directly imports API and mutation endpoints | P2 | Runtime + Assembler |
| `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue:48` | Render/API boundary broken | renderer component directly calls data APIs | P2 | Runtime adapter |
| `frontend/apps/web/src/app/runtime/actionViewBatchHintResolverRuntime.ts:58` | Runtime mixed with UI text fallback | runtime module emits fallback labels/text | P3 | Contract/UI fallback policy |

## Rule Violations by Category

- Page-layer overreach: 6
- Heuristic-based business inference: 2
- Shell-layer pollution: 2
- Render purity break: 2
- Runtime/UI-text coupling: 1

## Immediate Closure Candidates

1. `ActionView` load/action/batch ownership transfer (`P1`).
2. `HomeView` keyword inference removal (`P1`).
3. Introduce page assembly entrypoint and shrink page local state (`P1`).


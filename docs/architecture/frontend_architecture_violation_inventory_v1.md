# Frontend Architecture Violation Inventory v1

## Severity Definition

- `P1`: blocks architecture closure this wave.
- `P2`: should be addressed in near-term wave.
- `P3`: optimization/clean-up after core closure.

## Violation List

| Location | Violation Type | Description | Severity | Status | Target Layer |
| --- | --- | --- | --- | --- | --- |
| `frontend/apps/web/src/views/ActionView.vue:797` | State center still retained in page shell | selection/batch 已进 capsule，但页面仍持有 `status/trace/records/group` 这类核心状态 host | P2 | accepted | Page Assembly |
| `frontend/apps/web/src/views/ActionView.vue:1251` | Page assembly not final | assembler 已接管 HUD/advanced rows，但页面仍在 assembler 之前准备大量 display/state input | P2 | backlog | Page Assembly |
| `frontend/apps/web/src/views/ActionView.vue:814` | Group runtime bridge still page-owned | group capsule 已存在，但 drilldown/window/route bridge 仍集中在 page shell | P2 | backlog | Runtime + Page Assembly |
| `frontend/apps/web/src/views/HomeView.vue:1228` | Keyword business inference | todo action labels inferred by keywords | P1 | resolved | Contract Consumption |
| `frontend/apps/web/src/views/HomeView.vue:1046` | Heuristic inference helper | keyword list/inclusion logic still drives business semantics | P1 | resolved | Contract Consumption |
| `frontend/apps/web/src/views/SceneView.vue:280` | Page rebuilds scene model | fallback scene constructed directly from scene-ready deep fields | P2 | downgraded | Contract Consumption + Routing |
| `frontend/apps/web/src/views/SceneView.vue:321` | Page route orchestration overload | scene resolve + route rewrite mixed in one view flow | P2 | backlog | Routing |
| `frontend/apps/web/src/layouts/AppShell.vue:296` | Shell contains business heuristics | delivery role text normalization and role mapping in shell | P2 | resolved | Shell |
| `frontend/apps/web/src/layouts/AppShell.vue:515` | Shell contains trace/export ops | debug/trace action export logic mixed into shell runtime | P3 | backlog | Shell support module |
| `frontend/apps/web/src/pages/ContractFormPage.vue:300` | Render/API boundary broken | page component directly imports API and mutation endpoints | P2 | backlog | Runtime + Assembler |
| `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue:48` | Render/API boundary broken | renderer component directly calls data APIs | P2 | backlog | Runtime adapter |
| `frontend/apps/web/src/app/runtime/actionViewBatchHintResolverRuntime.ts:58` | Runtime mixed with UI text fallback | runtime module emits fallback labels/text | P3 | backlog | Contract/UI fallback policy |

## Rule Violations by Category

- Page-layer overreach: 6
- Heuristic-based business inference: 2
- Shell-layer pollution: 2
- Render purity break: 2
- Runtime/UI-text coupling: 1

## Immediate Closure Candidates

1. 首发切片相关前端 boundary 清理，优先 `ProjectManagementDashboardView.vue` 的 contract 语义重建问题 (`P1`)。
2. `ActionView` backlog 只在未来明确阻断时重开，不再作为当前主线。
3. Render/API boundary 清理保留为后续近程批次。

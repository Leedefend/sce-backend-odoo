# Frontend Contract Consumption Hardening Inventory (Wave)

## Scope
- Frontend runtime target: `frontend/apps/web/src/views/ActionView.vue` and adjacent runtime modules.
- Goal: classify existing heuristics, map them to backend contract ownership, and define removal priority.

## Heuristic Inventory
| Heuristic | File/Function | Type | Backend Target Layer | Runtime Source Priority | Removal Priority |
|---|---|---|---|---|---|
| `surfaceKind` keyword inference | `frontend/apps/web/src/views/ActionView.vue` / `surfaceKind` | page semantics | `scene_ready.surface.kind` | `scene_ready.surface.kind -> scene_contract.extensions.surface_kind -> no guess` | P0 |
| `surfaceIntent` default business copy | `frontend/apps/web/src/views/ActionView.vue` / `surfaceIntent` | page semantics | `scene_ready.surface.intent` | `scene_ready.surface.intent -> page_orchestration.surface_intent -> UI empty fallback` | P0 |
| `viewModeLabel` enum mapping fallback | `frontend/apps/web/src/views/ActionView.vue` / `viewModeLabel` | UI fallback + page semantics | `scene_ready.view_modes[].label` | `scene_ready.view_modes -> page_contract.view_modes -> raw mode key` | P1 |
| `contractActionGroups` keyword grouping | `frontend/apps/web/src/views/ActionView.vue` / `contractActionGroups` | page semantics | `scene_ready.action_surface.groups` | `scene_ready.action_surface.groups -> flat ordered actions` | P0 |
| `resolveDefaultSort` branch by inferred kind | `frontend/apps/web/src/views/ActionView.vue` / `resolveDefaultSort` | business projection | `scene_ready.list_profile.default_sort` | `scene_ready.list_profile.default_sort -> action_contract.search.default_order -> id desc` | P1 |
| `convergeColumnsForSurface` keyword bucket selection | `frontend/apps/web/src/views/ActionView.vue` / `convergeColumnsForSurface` | business projection | `scene_ready.list_profile.columns + column_roles` | `scene_ready.list_profile.columns -> action_contract.columns -> ui fallback columns` | P1 |
| `listSemanticKind` field-set inference | `frontend/apps/web/src/views/ActionView.vue` / `listSemanticKind` | business projection | `scene_ready.projection.kind` | `scene_ready.projection.kind -> no business guess` | P0 |
| `listSummaryItems` frontend aggregation | `frontend/apps/web/src/views/ActionView.vue` / `listSummaryItems` | business projection | `scene_ready.projection.summary_items` | `scene_ready.projection.summary_items -> empty` | P0 |
| `ledgerOverviewItems` frontend aggregation | `frontend/apps/web/src/views/ActionView.vue` / `ledgerOverviewItems` | business projection | `scene_ready.projection.overview_strip` | `scene_ready.projection.overview_strip -> empty` | P0 |
| `advancedViewTitle` switch-case copy | `frontend/apps/web/src/views/ActionView.vue` / `advancedViewTitle` | page semantics | `scene_ready.advanced_view.title` | `scene_ready.advanced_view.title -> neutral fallback` | P2 |
| `advancedViewHint` switch-case copy | `frontend/apps/web/src/views/ActionView.vue` / `advancedViewHint` | page semantics | `scene_ready.advanced_view.hint` | `scene_ready.advanced_view.hint -> neutral fallback` | P2 |
| `semanticStatus` business inference | `frontend/apps/web/src/utils/semantic.ts` / `semanticStatus` business branch | business projection | `rows[].cells[*].semantic` | `cell.semantic -> neutral fallback` | P1 |
| `semanticStatus` minimal UI fallback | `frontend/apps/web/src/utils/semantic.ts` / fallback branch | UI fallback | keep minimal | `neutral badge/text only` | Keep |

## Classification Rule
- `UI fallback`: allowed to keep (loading/empty/error/minor label default).
- `page semantics`: must move to scene/page contract.
- `business projection`: must move to backend projection contract.

## Strict Contract Migration Pilot Scope
Current migration pilot scenes (temporary rollout scope, not source of truth):
- `workspace.home` / `workspace_home`
- `finance.payment_requests`
- `risk.center`
- `project.management`

Source of truth must come from backend `scene_tier` / `runtime_policy`.

## Strict Mode Runtime Policy
1. No keyword-based scene kind inference.
2. No frontend action grouping inference.
3. No frontend business summary aggregation.
4. Missing contract should produce explicit `contract missing` style fallback, not silent business guess.

## Source-of-Truth Guardrail
- 禁止前端硬编码核心场景集合（例如 `CORE_SCENES`）作为 strict mode 真相来源。
- strict mode 必须由后端契约下发并由前端被动消费：
  - `runtime_policy.strict_contract_mode`（最高优先）
  - `scene_tier=core`（次级）
- 若后端未下发上述字段，前端默认 `strict=false`，并通过验证脚本暴露缺口，而不是前端自定义名单补位。

## Removal Completion Rule
A heuristic is considered removed only when:
1. core scenes do not execute the heuristic branch anymore;
2. strict contract mode consumes backend contract as sole semantic source;
3. fallback behavior is UI-only and neutral;
4. verification coverage exists for regression detection.

## Deletion Order
1. P0: `surfaceKind`, `surfaceIntent`, `contractActionGroups` heuristic grouping, `listSemanticKind/listSummaryItems/ledgerOverviewItems`.
2. P1: `resolveDefaultSort`, `convergeColumnsForSurface`, `viewModeLabel`, `semanticStatus` business semantics.
3. P2: `advancedViewTitle/advancedViewHint`.

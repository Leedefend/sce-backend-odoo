# Frontend Contract Consumption Hardening Inventory (Wave)

## Scope
- Frontend runtime target: `frontend/apps/web/src/views/ActionView.vue` and adjacent runtime modules.
- Goal: classify existing heuristics, map them to backend contract ownership, and define removal priority.

## Heuristic Inventory
| Heuristic | File/Function | Type | Backend Target Layer | Removal Priority |
|---|---|---|---|---|
| `surfaceKind` keyword inference | `frontend/apps/web/src/views/ActionView.vue` / `surfaceKind` | page semantics | `scene ready.surface.kind` | P0 |
| `surfaceIntent` default business copy | `frontend/apps/web/src/views/ActionView.vue` / `surfaceIntent` | page semantics | `scene ready.surface.intent` | P0 |
| `viewModeLabel` enum mapping fallback | `frontend/apps/web/src/views/ActionView.vue` / `viewModeLabel` | UI fallback + page semantics | `scene ready.view_modes[].label` | P0 |
| `contractActionGroups` keyword grouping | `frontend/apps/web/src/views/ActionView.vue` / `contractActionGroups` | page semantics | `action_surface.groups` | P0 |
| `resolveDefaultSort` branch by inferred kind | `frontend/apps/web/src/views/ActionView.vue` / `resolveDefaultSort` | business projection | `list_profile.default_sort` | P1 |
| `convergeColumnsForSurface` keyword bucket selection | `frontend/apps/web/src/views/ActionView.vue` / `convergeColumnsForSurface` | business projection | `list_profile.columns + column_roles` | P1 |
| `listSemanticKind` field-set inference | `frontend/apps/web/src/views/ActionView.vue` / `listSemanticKind` | business projection | `projection.kind` | P0 |
| `listSummaryItems` frontend aggregation | `frontend/apps/web/src/views/ActionView.vue` / `listSummaryItems` | business projection | `projection.summary_items` | P0 |
| `ledgerOverviewItems` frontend aggregation | `frontend/apps/web/src/views/ActionView.vue` / `ledgerOverviewItems` | business projection | `projection.overview_strip` | P0 |
| `advancedViewTitle` switch-case copy | `frontend/apps/web/src/views/ActionView.vue` / `advancedViewTitle` | page semantics | `advanced_view.title` | P2 |
| `advancedViewHint` switch-case copy | `frontend/apps/web/src/views/ActionView.vue` / `advancedViewHint` | page semantics | `advanced_view.hint` | P2 |
| `semanticStatus` tone/text inference | `frontend/apps/web/src/utils/semantic.ts` / `semanticStatus` | business projection | `rows[].cells[*].semantic` | P1 |

## Classification Rule
- `UI fallback`: allowed to keep (loading/empty/error/minor label default).
- `page semantics`: must move to scene/page contract.
- `business projection`: must move to backend projection contract.

## Core Scene Strict Mode Baseline
Core scenes for strict mode:
- `workspace.home` / `workspace_home`
- `finance.payment_requests`
- `risk.center`
- `project.management`

Strict mode runtime policy:
1. No keyword-based scene kind inference.
2. No frontend action grouping inference.
3. No frontend business summary aggregation.
4. Missing contract should produce explicit `contract missing` style fallback, not silent business guess.

## Deletion Order
1. P0: `surfaceKind`, `surfaceIntent`, `contractActionGroups` heuristic grouping, `listSemanticKind/listSummaryItems/ledgerOverviewItems`.
2. P1: `resolveDefaultSort`, `convergeColumnsForSurface`, `semanticStatus` business semantics.
3. P2: `advancedViewTitle/advancedViewHint`.


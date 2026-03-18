# Frontend Architecture Asset Inventory v1

## 1. Contract Consumption Assets

| Asset | Path | Role | Reuse Recommendation | Long-term |
| --- | --- | --- | --- | --- |
| strict mode source resolver | `frontend/apps/web/src/app/contractStrictMode.ts` | backend policy/tier strict decision | Reuse across Action/Home/Record/Scene | Keep core |
| strict contract bundle | `frontend/apps/web/src/app/contracts/actionViewStrictContract.ts` | strict missing/default summary + contract entry extraction | Adapt as generic scene-view strict bundle | Keep + generalize |
| surface contract resolver | `frontend/apps/web/src/app/contracts/actionViewSurfaceContract.ts` | view modes + surface intent normalization | Reuse in list/workspace scenes | Keep (reduce fallback branches) |
| projection contract resolver | `frontend/apps/web/src/app/contracts/actionViewProjectionContract.ts` | projection metric mapping | Reuse in Home/Action KPI strips | Keep |
| advanced contract resolver | `frontend/apps/web/src/app/contracts/actionViewAdvancedContract.ts` | advanced fallback title/hint | Reuse in downgraded views | Keep |

## 2. Runtime Assets

| Asset | Path | Role | Reuse Recommendation | Long-term |
| --- | --- | --- | --- | --- |
| grouped runtime composable | `frontend/apps/web/src/app/runtime/useActionViewGroupRuntime.ts` | grouped paging/window/drilldown state capsule | Reuse in list-heavy views | Keep core |
| request runtime helpers | `frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts` | request domain/context/sort merge helpers | Promote as common list runtime helpers | Keep + rename/generalize |
| route/runtime sync helpers | `frontend/apps/web/src/app/runtime/actionViewRouteRuntime.ts` + `actionViewRoutePresetRuntime.ts` | route preset and sync shaping | Reuse with assembler-owned state | Keep |
| group window runtime | `frontend/apps/web/src/app/runtime/actionViewGroupWindowRuntime.ts` | grouped page offset parsing/serialization | Keep as shared utility | Keep |
| projection refresh runtime | `frontend/apps/web/src/app/projectionRefreshRuntime.ts` | unified projection refresh execution | Reuse across scene mutation runtimes | Keep core |
| scene mutation runtime | `frontend/apps/web/src/app/sceneMutationRuntime.ts` | mutation contract execution | Reuse across Action/Home/Record quick actions | Keep core |

## 3. Resolver Assets

| Asset | Path | Role | Reuse Recommendation | Long-term |
| --- | --- | --- | --- | --- |
| scene ready resolver | `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts` | scene-ready entry lookup and helpers | Keep as one contract source adapter | Keep |
| scene registry resolver | `frontend/apps/web/src/app/resolvers/sceneRegistry.ts` | scene metadata and diagnostics | Keep, reduce page direct deep reads | Keep |

## 4. Render Assets

| Asset | Path | Role | Reuse Recommendation | Long-term |
| --- | --- | --- | --- | --- |
| list renderer page | `frontend/apps/web/src/pages/ListPage.vue` | table/list/group rendering surface | Keep as render target, reduce runtime ownership | Keep after purity pass |
| kanban renderer page | `frontend/apps/web/src/pages/KanbanPage.vue` | kanban rendering surface | Keep as render target | Keep |
| group summary bar | `frontend/apps/web/src/components/GroupSummaryBar.vue` | grouped summary render primitive | Reuse in grouped pages | Keep |
| status panel | `frontend/apps/web/src/components/StatusPanel.vue` | loading/empty/error panel | Reuse globally | Keep |

## 5. Asset Maturity Summary

- Mature reusable assets: strict mode resolver, scene mutation runtime, projection refresh runtime, grouped runtime capsule.
- High-potential assets needing normalization: ActionView-specific contract/runtime helpers (naming + scope).
- Assets needing boundary cleanup before broad reuse: `ListPage.vue`, `ContractFormPage.vue`, relational view renderers.


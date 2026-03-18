# Frontend Architecture Layer Mapping v1

## 1. Layer Mapping Matrix

| Layer | Current Entrypoints | Status | Notes |
| --- | --- | --- | --- |
| Shell | `layouts/AppShell.vue` | Partial | Shell host exists, contains extra heuristic/diagnostic logic |
| Routing & Navigation | `router/*`, `app/resolvers/*`, page-local route handlers | Partial | Route ownership split across router and views |
| Contract Consumption | `app/contracts/*`, `app/contractStrictMode.ts`, parts of `sceneReadyResolver` | Partial+ | Pilot quality good in ActionView scope |
| Runtime Execution | `app/runtime/*` | Partial+ | Large extraction completed; still view-coupled |
| Page Assembly | N/A (`app/assemblers` missing) | Missing | Biggest structural gap |
| Render Components | `pages/*`, `components/*` | Mixed | Some pure components, some runtime/API-heavy components |

## 2. Key File Mapping

| File | Current Role | Target Layer | Gap |
| --- | --- | --- | --- |
| `frontend/apps/web/src/layouts/AppShell.vue` | shell + role heuristics + HUD trace ops | Shell | Should remove business heuristics |
| `frontend/apps/web/src/views/ActionView.vue` | template + contract + runtime + orchestration | Shell consumer + Assembler consumer | Still super component |
| `frontend/apps/web/src/views/HomeView.vue` | home render + keyword heuristics + nav actions | Shell consumer + Assembler consumer | Semantic heuristics remain |
| `frontend/apps/web/src/views/RecordView.vue` | record contract loading + data flow + render | Runtime/Assembler consumer | Runtime-heavy page |
| `frontend/apps/web/src/views/SceneView.vue` | scene route orchestration + fallback compose | Routing/Assembler consumer | Route/target logic still in page |
| `frontend/apps/web/src/app/contracts/actionViewStrictContract.ts` | strict contract bundle | Contract Consumption | Good pilot asset |
| `frontend/apps/web/src/app/runtime/useActionViewGroupRuntime.ts` | grouped runtime capsule | Runtime | Good reusable asset |
| `frontend/apps/web/src/pages/ContractFormPage.vue` | page + API + mutation orchestration | Runtime+Assembler consumer | Violates render purity |

## 3. Layer Coverage Snapshot

- Strongest layer: `Runtime Execution` (depth).
- Most mature policy: strict mode source-of-truth in `app/contractStrictMode.ts`.
- Weakest layer: `Page Assembly` (currently absent).
- Most urgent closure point: `ActionView` ownership split (state/process -> runtime & assembler).


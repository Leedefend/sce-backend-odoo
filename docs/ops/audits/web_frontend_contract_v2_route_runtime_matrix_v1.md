# Web Frontend Contract V2 Route Runtime Matrix V1

Date: 2026-05-13

Layer Target: Frontend Architecture Guard

Module: `frontend/apps/web`

Reason: lock the product route/runtime boundary before contract v2 frontend cleanup continues.

## Product Route Matrix

| Route | Product Runtime | Contract Source | Batch A Decision |
| --- | --- | --- | --- |
| `/a/:actionId` | `ActionViewShell` -> `ActionView.vue` | action/load contract, currently mixed legacy + v2 bridge | keep as product route, refactor to `ContractV2ActionSnapshot` in Batch D |
| `/f/:model/:id` | `ContractFormPage` | model/action contract, currently mixed legacy + v2 bridge | keep as product route, refactor to pure `ContractV2FormRenderer` in Batch C |
| `/r/:model/:id` | `ContractFormPage` | same form runtime as `/f` | keep as product route, must remain same renderer as `/f` |

## Non-Product Runtime Matrix

| Runtime | Current Status | Required Boundary |
| --- | --- | --- |
| `RecordView.vue` | removed after `/r/:model/:id` converged on `ContractFormPage` | retired delegate must not return |
| `ModelFormPage.vue` | removed after `/f/:model/:id` converged on `ContractFormPage` | retired wrapper must not return |
| `ModelListPage.vue` | legacy redirect shell | remove after route migration or keep diagnostics-only |
| `unifiedPageContractLitePilot.ts` | transitional lite pilot | formal version harness only, not product default |
| `unifiedPageContractLite.ts` with `legacy_default` | transitional compatibility fallback | retire or isolate under explicit compat mode |

## Runtime Ownership

| Concern | Current Default Owner | Target Owner |
| --- | --- | --- |
| contract load | `api/contract.ts` projection + page runtime | `ContractV2Client` |
| normalized page state | page-local computed state | `ContractV2Store` |
| reads/writes/actions | page/view direct data API calls | `ContractV2Runtime` |
| relation behavior | page/component action handlers | declared v2 relation actions/data sources |
| permission/action visibility | mixed permission shapes and groups | backend v2 status/action availability |
| rendering | page-specific layout and fallback logic | pure `ContractV2Renderer` registry |

## Guard Policy

`scripts/verify/web_contract_v2_frontend_architecture_guard.py` enforces this matrix in two modes:

- debt-lock mode: existing deviations are reported and bounded; count growth fails.
- strict mode: all listed deviations must be zero.

The strict mode switch is:

```bash
WEB_CONTRACT_V2_ARCH_GUARD_STRICT=1 python3 scripts/verify/web_contract_v2_frontend_architecture_guard.py
```

Batch A keeps debt-lock mode as the default because cleanup is not yet complete. Later cleanup batches should reduce the allowed counts, then enable strict mode in CI when the default product path is pure v2.

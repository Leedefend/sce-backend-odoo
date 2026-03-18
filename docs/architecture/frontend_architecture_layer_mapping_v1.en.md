# Frontend Architecture Layer Mapping v1

## Layer Matrix

| Layer | Current Entrypoints | Status |
| --- | --- | --- |
| Shell | `layouts/AppShell.vue` | Partial |
| Routing & Navigation | `router/*`, `app/resolvers/*`, page-local route handling | Partial |
| Contract Consumption | `app/contracts/*`, `app/contractStrictMode.ts` | Partial+ |
| Runtime Execution | `app/runtime/*` | Partial+ |
| Page Assembly | N/A (`app/assemblers` missing) | Missing |
| Render Components | `pages/*`, `components/*` | Mixed |

## Key Mapping Notes

- `ActionView.vue` is still a transition super-component.
- `AppShell.vue` is functional but not fully boundary-clean.
- `ContractFormPage.vue` and some view components still break render/API purity.
- Biggest gap remains Page Assembly layer.


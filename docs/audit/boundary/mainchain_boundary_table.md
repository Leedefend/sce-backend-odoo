# Mainchain Boundary Table

| Chain | Route Object | Risk Level | Category | Boundary Signal |
|---|---|---|---|---|
| page/block fetch 链 | `/api/contract/capability_matrix` | P1 | `B` | 疑似越界 |
| page/block fetch 链 | `/api/contract/portal_dashboard` | P1 | `B` | 疑似越界 |
| page/block fetch 链 | `/api/contract/portal_execute_button` | P1 | `B` | 疑似越界 |
| execute/action 链 | `/api/execute_button` | P1 | `F` | 疑似越界 |
| 登录链 | `/api/login` | P0 | `B` | 明显越界 |
| menu/nav 链 | `/api/menu/tree` | P0 | `B` | 明显越界 |
| execute/action 链 | `/api/portal/execute_button` | P1 | `B` | 疑似越界 |
| scene open 链 | `/api/scenes/export` | P2 | `F` | 疑似越界 |
| scene open 链 | `/api/scenes/import` | P2 | `F` | 疑似越界 |
| scene open 链 | `/api/scenes/my` | P0 | `C` | 疑似越界 |

Legacy compliance note: `/api/scenes/my` is deprecated; successor endpoint is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.
| 登录链 | `/api/session/get` | P0 | `B` | 明显越界 |
| page/block fetch 链 | `/api/ui/contract` | P1 | `B` | 疑似越界 |
| menu/nav 链 | `/api/user_menus` | P3 | `B` | 疑似越界 |

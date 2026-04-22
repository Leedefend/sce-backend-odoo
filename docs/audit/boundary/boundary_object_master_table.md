# Boundary Object Master Table

| Object | Path | Category | Current Owner | Expected Owner | Runtime Level | Risk Level | Migration Difficulty |
|---|---|---|---|---|---|---|---|
| `/api/capabilities/export` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/capabilities/lint` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/capabilities/search` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/contract/capability_matrix` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | page/block fetch 链 | P1 | medium-high |
| `/api/contract/portal_dashboard` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | page/block fetch 链 | P1 | medium-high |
| `/api/contract/portal_execute_button` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | page/block fetch 链 | P1 | medium-high |
| `/api/execute_button` | `addons/smart_construction_core/controllers/*` | `F` | `smart_construction_core` | `split_pending(screened mixed)` | execute/action 链 | P1 | medium-high |
| `/api/insight` | `addons/smart_construction_core/controllers/*` | `A` | `smart_construction_core` | `smart_construction_core(domain)` | 其他运行链 | P1 | medium-high |
| `/api/login` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | 登录链 | P0 | high |
| `/api/logout` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | 其他运行链 | P1 | medium-high |
| `/api/menu/tree` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | menu/nav 链 | P0 | high |
| `/api/meta/describe_model` | `addons/smart_construction_core/controllers/*` | `F` | `smart_construction_core` | `split_pending(screened mixed)` | 其他运行链 | P1 | medium-high |
| `/api/meta/project_capabilities` | `addons/smart_construction_core/controllers/*` | `A` | `smart_construction_core` | `smart_construction_core(domain)` | 其他运行链 | P1 | medium-high |
| `/api/ops/audit/search` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/ops/job/status` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/ops/packs/batch_rollback` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/ops/packs/batch_upgrade` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/ops/subscription/set` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/ops/tenants` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/packs/catalog` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/packs/install` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/packs/publish` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/packs/upgrade` | `addons/smart_construction_core/controllers/*` | `D` | `smart_construction_core` | `smart_core(governance)` | 治理辅助链 | P2 | medium |
| `/api/portal/execute_button` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | execute/action 链 | P1 | medium-high |
| `/api/preferences/get` | `addons/smart_construction_core/controllers/*` | `C` | `smart_construction_core` | `smart_construction_scene(scene runtime)` | 其他运行链 | P2 | medium |
| `/api/preferences/set` | `addons/smart_construction_core/controllers/*` | `C` | `smart_construction_core` | `smart_construction_scene(scene runtime)` | 其他运行链 | P2 | medium |
| `/api/scenes/export` | `addons/smart_construction_core/controllers/*` | `F` | `smart_construction_core` | `split_pending(screened mixed)` | scene open 链 | P2 | medium |
| `/api/scenes/import` | `addons/smart_construction_core/controllers/*` | `F` | `smart_construction_core` | `split_pending(screened mixed)` | scene open 链 | P2 | medium |
| `/api/scenes/my` | `addons/smart_construction_core/controllers/*` | `C` | `smart_construction_core` | `smart_construction_scene(scene runtime)` | scene open 链 | P0 | high |

Legacy compliance note: `/api/scenes/my` is deprecated; successor endpoint is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.
| `/api/session/get` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | 登录链 | P0 | high |
| `/api/ui/contract` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | page/block fetch 链 | P1 | medium-high |
| `/api/user_menus` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | menu/nav 链 | P3 | low |
| `/sc/auth/activate/<string:token>` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | 其他运行链 | P3 | low |
| `/web/signup` | `addons/smart_construction_core/controllers/*` | `B` | `smart_construction_core` | `smart_core(platform runtime)` | 其他运行链 | P3 | low |

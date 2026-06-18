# Agent Instructions

## Codex Execution Policy
- Always follow `docs/ops/codex_execution_allowlist.md` for all execution and validation steps.
- If a requested action falls outside the allowlist, stop and ask for confirmation before proceeding.
- Always follow `docs/ops/codex_workspace_execution_rules.md` before any write action.
- Mandatory preflight before edits: `pwd` + `git rev-parse --show-toplevel` + `git branch --show-current` + `git status --short`.

## Architecture Guard
- Always follow `ARCHITECTURE_GUARD.md` and `docs/architecture/ai_development_guard.md` before making code changes.
- For frontend page work, always follow `docs/architecture/native_view_reuse_frontend_spec_v1.md`.
- For product/module boundary decisions, always follow `docs/product/formal_product_boundary_v1.md` and then map the decision to `docs/architecture/backend_contract_boundaries.md`.
- For every implementation task, explicitly identify `Formal Product Layer`, `Layer Target`, `Module`, and `Reason` before coding.
- Boundary decision is mandatory before every iterative change that touches contracts, forms, menus, frontend rendering, runtime configuration, data repair, or business semantics. Before editing, answer:
  - `Formal Product Layer`: P0 platform kernel product, P1 construction industry standard product, P2 specific user product, P3 low-code configuration product, or P4 ops delivery tool.
  - `Layer Target`: concrete module/mechanism target, such as `smart_core`, `smart_construction_core`, `smart_construction_custom`, low-code runtime configuration, ops repair/replay, or frontend renderer.
  - `Standard vs User-Specific`: whether the rule belongs to the platform mechanism, construction product standard, confirmed customer baseline, administrator runtime configuration, or one-off ops repair.
  - `Why Here`: why the chosen layer owns the rule.
  - `Why Not Elsewhere`: why the rule must not be placed in another P0-P4 product layer, frontend, runtime config, or module as applicable.
  - `Blast Radius`: expected affected menus/models/contracts and what validation will prove containment.
- Platform core must not receive industry or customer-specific business semantics. Put construction-industry defaults in `smart_construction_core`; put stable customer-specific differences in `smart_construction_custom` or a dedicated customer module; keep temporary administrator changes in low-code runtime configuration; use migration scripts only for repair/replay/verification. Keep frontend changes limited to generic contract rendering behavior.
- Ownership rules for configuration and orchestration:
  - `smart_core` owns platform mechanisms only: contract models, versioning, publishing, rollback, low-code handlers, orchestration merge behavior, and generic frontend contract consumption. It must not encode construction-industry semantics or customer preferences.
  - `smart_construction_core` owns construction-industry standard defaults: models, menus, actions, native XML baselines, standard business fields, standard search/list/form behavior, and semantics that every standard construction deployment should inherit.
  - `smart_construction_custom` owns stable customer/user preferences and delivery configuration: customer-specific form layouts, field order, labels, visibility, role/company defaults, and confirmed low-code results that must survive rebuilds and upgrades.
  - Low-code configuration is an editing surface and runtime carrier, not the final architectural owner. If a low-code change becomes a confirmed standard, move it to the industry module; if it becomes a confirmed customer preference, move it to the custom module; if it is experimental, it may remain runtime data.
  - Ops scripts are for migration, repair, replay, and verification. They must not be the long-term source of truth for platform behavior, industry defaults, or customer preferences.

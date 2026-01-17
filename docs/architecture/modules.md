# Module Boundaries and Dependency Rules

This document defines module responsibilities, allowed dependency direction, and
placement rules for new code. Treat it as a pre-release checklist and a review
baseline.

## Dependency Direction (single direction only)

Allowed direction (top = most generic, bottom = most specific):

1) odoo_test_helper
2) sc_norm_engine
3) smart_construction_bootstrap
4) smart_construction_core
5) smart_construction_custom
6) smart_construction_seed
7) smart_construction_demo

Rules:
- No reverse dependencies.
- core must not depend on demo/seed/custom.
- demo/seed/custom must not inject business logic back into core.

## Responsibilities by Module

smart_construction_core
- Business models/fields/computations.
- Security (ACL/record rules).
- Menus/actions/views.
- UI/UX features that are product-level (sidebar, workbench, login redirect).
- Anything that stands alone without demo data or a specific customer.

smart_construction_custom
- Current position: extension layer (not client-specific) for this release.
- Customer-specific changes: labels, reports, flows, UI branding.
- Client-only rules or approval chains.
- Must depend on core; must not leak into core.

smart_construction_demo
- Demo data only: companies, users, projects, contracts, payments.
- Demo assets: images/attachments.
- Scenario loaders.
- No business logic, no behavior overrides, no auth/login hacks.

smart_construction_seed
- Idempotent initialization: parameters, dictionaries, roles, taxes.
- Hooks (pre/post init) guarded by config or env flags.
- Must be safe to disable without breaking core.

smart_construction_bootstrap
- Install/first-run experience.
- Environment setup guidance and templates.
- No business models or product features.

sc_norm_engine
- Industry norms, field standardization, validation rules.
- Shared rule engines or standard code tables.
- No UI views or demo data.

odoo_test_helper
- Test fixtures, mocks, helpers for CI.
- Must not affect production runtime.

## Placement Rules (fast decision)

1) Works without demo data and without a specific customer?
   - Yes: core.
2) Only needed once on first install or to seed base config?
   - Yes: seed/bootstrap.
3) Only for showcase or marketing?
   - Yes: demo.

## Review Checklist

- Dependencies are one-way and declared in __manifest__.py.
- core does not import or depend on demo/seed/custom.
- demo/seed/custom avoid overriding core behavior unless explicitly gated.

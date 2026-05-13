# Platform Core Business Kernel Gap v1

Status: draft architecture contract

Binding registry: `platform_core_business_kernel_gap_v1.json`

## Core Answer

Yes. This is now the highest priority platform gap.

Before this step, `smart_core` mainly provided runtime contracts, intent routing,
UI base contract assets, preferences, users, and technical governance. Those are
necessary platform services, but they did not fully express the platform
business kernel:

```text
platform -> company -> business -> carrier -> fact -> projection
```

If the construction module is removed, the platform still has technical
infrastructure, but it has no reusable business scope vocabulary. That makes
`project.project` look like the platform business kernel by accident.

## First Gate: Company Access

The platform must first answer:

```text
which companies can use the platform?
```

That is earlier than project, business fact, or industry carrier. The platform
owns this layer through:

- `sc.subscription.plan`
- `sc.subscription`
- `sc.entitlement`
- `sc.usage.counter`
- `sc.ops.job`

These models belong in `smart_core`, not in a construction industry module.
Construction may provide menus and admin surfaces, but model authority is
platform-level.

## Minimum Kernel Decision

The platform kernel must be filled in stages:

1. own company access, entitlement, usage, and ops state in `smart_core`.
2. define a cross-industry business/carrier scope contract in `smart_core`.
3. let industry modules bind that contract to their carriers.
4. only introduce concrete platform tables such as `sc.business` or
   `sc.business.carrier` after runtime evidence shows metadata is not enough.

The first platform artifacts are therefore:

- `sc.subscription.plan`
- `sc.subscription`
- `sc.entitlement`
- `sc.usage.counter`
- `sc.ops.job`
- `sc.business.scope.mixin`

The access models answer company usability. The scope mixin is an abstract
metadata contract, not a business source-of-truth table.

## Runtime Surface Ownership

Company access is now a platform-owned runtime surface, not a construction
module configuration surface.

`smart_core` owns:

- seed entrypoint: `smart_core/data/sc_subscription_default.xml`
- admin views and menu: `smart_core/views/platform_company_access_views.xml`
- access group: `smart_core.group_smart_core_admin`
- verification: `make verify.platform_company_access_kernel.probe`

Construction modules may consume subscription, entitlement, usage, and ops state,
but they must not host the canonical seed data, action records, menu records, or
admin views for these platform models.

## Why Not Add sc.business Immediately

The audit has proven a concept gap, not yet a lifecycle ownership gap.

Adding a concrete `sc.business` table too early would force every industry and
existing construction workflow through a new master-data object before the
platform has evidence for creation rules, ownership rules, lifecycle rules,
carrier multiplicity, migration policy, and projection semantics.

The correct first move is a platform-owned scope contract that industry facts
can inherit without replacing their current authoritative carrier.

## Boundary

`sc.business.scope.mixin` may define:

- `business_scope_key`
- `business_direction`
- `carrier_type`
- `carrier_model`
- `carrier_res_id`

It must not define:

- project semantics
- construction workflow states
- customer migration assumptions
- required business master data
- carrier lifecycle ownership

## Current Construction Binding

`tender.bid` now inherits the platform scope contract while keeping
`project_id` required. This keeps the construction workflow stable and proves
that platform scope can exist outside construction vocabulary.

The immediate platform correction is therefore not "platform core owns all
business data". It is "platform core owns company usability and the
cross-industry business scope language; industry modules own carrier semantics
until evidence requires a shared business table."

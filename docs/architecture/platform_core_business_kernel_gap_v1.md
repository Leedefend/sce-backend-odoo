# Platform Core Business Kernel Gap v1

Status: draft architecture contract

Binding registry: `platform_core_business_kernel_gap_v1.json`

## Core Answer

Yes. This is now the highest priority platform gap.

Before this step, `smart_core` mainly provided runtime contracts, intent routing,
UI base contract assets, preferences, users, and technical governance. Those are
necessary platform services, but they do not by themselves express the platform
business kernel:

```text
platform -> company -> business -> carrier -> fact -> projection
```

If the construction module is removed, the platform still has technical
infrastructure, but it has no reusable business scope vocabulary. That makes
`project.project` look like the platform business kernel by accident.

## Minimum Kernel Decision

The platform kernel must be filled in stages:

1. define a cross-industry business/carrier scope contract in `smart_core`.
2. let industry modules bind that contract to their carriers.
3. only introduce concrete platform tables such as `sc.business` or
   `sc.business.carrier` after runtime evidence shows metadata is not enough.

The first platform artifact is therefore:

- `sc.business.scope.mixin`

This is an abstract metadata contract, not a business source-of-truth table.

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
business data". It is "platform core owns the cross-industry business scope
language, industry modules own carrier semantics until evidence requires a
shared business table."

# System Init ext_facts Contribution Protocol v1

## Purpose

Define a platform-owned extension protocol for `system.init`.
Industry modules only provide additive facts/collection summaries; platform
owns final payload assembly, normalization, and exposure scope.

## Ownership Boundary

- platform owner (`smart_core`):
  - collect contributions
  - normalize shape and key policy
  - merge ext_facts payload
  - apply size/scope guard
- industry modules:
  - provide module-scoped facts and optional collection summaries
  - no direct mutation of `system.init` root contract

## Preferred Hook

- `get_system_init_fact_contributions(env, user, context=None) -> dict | list[dict]`

## Contribution Shape

Single object form:

```python
{
  "module": "smart_construction_core",
  "facts": {...},
  "collections": {...},
  "meta": {...}
}
```

List form allows multiple scoped bundles from one module.

## Merge Rules

- `module` must be present and stable.
- `facts` is additive; same-key conflicts resolved by platform policy.
- `collections` should be summary-level (count/status/hints), not heavy rows.
- `meta` is optional and used for diagnostics/versioning.

## Forbidden Patterns

- industry module directly mutating root `system.init` payload.
- industry module assembling workspace heavy list payloads in startup chain.
- cross-module overwrite without platform merge policy.

## Transition Notes

- temporary compatibility may keep legacy `smart_core_extend_system_init` read path.
- final ownership target: platform merge service consumes contribution hook only.


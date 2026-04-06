# Capability Contribution Protocol v1

## Purpose

Define a platform-owned capability contribution contract. Runtime query and
projection ownership stay in `smart_core`; industry modules only provide
contribution payload.

## Ownership Boundary

- platform owner:
  - contribution collection
  - merge conflict policy
  - runtime query/projection
  - capability surface exposure
- industry owner:
  - capability facts and module-scoped metadata contribution
  - optional group contribution

## Preferred Hooks

- `get_capability_contributions(env, user) -> list[dict]`
- `get_capability_group_contributions(env) -> list[dict]`

Legacy compatibility hooks are temporarily supported:

- `smart_core_list_capabilities_for_user(env, user)`
- `smart_core_capability_groups(env)`

## Contribution Schema (Capability)

Required fields:

- `key`: unique capability key

Recommended fields:

- `owner_module`
- `source_module`
- `domain`
- `type`
- `ui`
- `binding`
- `permission`
- `lifecycle`
- `release`
- `status`

## Group Contribution Schema

Recommended fields:

- `key`
- `label`
- `icon`
- `sequence`
- `source_module`

## Platform Merge Rules

- dedupe by capability `key` (first valid owner wins in current stage)
- ignore invalid rows without `key`
- group merge dedupe by group `key`
- projection remains platform responsibility

## Forbidden Patterns

- industry module as runtime registry owner
- industry module exposing final capability matrix directly as platform API owner
- cross-module direct mutation of platform capability runtime container


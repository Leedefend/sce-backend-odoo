# Intent Handler Contribution Protocol v1

## Purpose

- establish single-owner registry governance: platform owns final registry write.
- industry modules provide declarative handler contributions only.

## Ownership Rules

1. platform module is the only final writer to runtime intent registry.
2. scenario/industry modules must return contribution data and must not mutate registry.
3. contribution conflicts are resolved by platform merge/validate service.

## Minimal Contribution Schema

```python
{
    "intent": "project.dashboard.enter",
    "handler": ProjectDashboardEnterHandler,
    "source_module": "smart_construction_core",
    "domain": "project",
    "status": "active",
}
```

## Extended Fields (Recommended)

- `intent` (str, required): globally unique intent key.
- `handler` (callable/class, required): handler implementation reference.
- `source_module` (str, required): module providing the contribution.
- `domain` (str, required): business or platform domain tag.
- `status` (str, required): `active|deprecated|experimental|disabled`.
- `priority` (int, optional): conflict-resolution tie breaker.
- `compat_aliases` (list[str], optional): alias intents mapped to same handler.
- `deprecation` (dict, optional): replacement intent and sunset metadata.

## Platform Merge/Validate Contract

1. collect all module contributions.
2. validate required fields and handler importability.
3. enforce intent uniqueness (or explicit priority override policy).
4. build final deterministic registry map.
5. write registry map in platform-only register stage.

## Prohibited Patterns

- direct industry code such as:

```python
registry["some.intent"] = SomeHandler
```

- industry-side implicit runtime mutation of platform registry.

## Migration Guidance (from legacy `smart_core_register`)

1. split legacy registry mutation function into pure provider:
   - `get_intent_handler_contributions()`.
2. keep handler logic in place initially, change only ownership pathway.
3. let platform loader consume contributions and perform final register.

## Acceptance for Batch-1 Task 1.1

- protocol document exists and is versioned.
- minimal schema is fixed and explicit.
- ownership and prohibited patterns are explicit.

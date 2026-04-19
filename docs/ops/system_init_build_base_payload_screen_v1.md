# System Init Build Base Payload Screen v1

## Goal

Screen the real ownership inside the coarse `build_base_payload` wrapper before
opening another backend implementation batch.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: `system.init` build_base_payload ownership screen
- Module Ownership: existing backend code inspection + docs
- Kernel or Scenario: scenario
- Reason: the previous instrumentation batch proved the hotspot is inside the
  build_base payload wrapper, but not necessarily inside
  `SystemInitPayloadBuilder.build_base(...)` itself

## Inherited Facts

- `prepare_runtime_context`: about `7659ms`
- `build_base_payload`: about `7509ms`
- `apply_extension_fact_contributions`: about `147ms`
- other measured prepare-runtime substeps are effectively `0ms` at current
  granularity

## Code-Inspection Result

`SystemInitPayloadBuilder.build_base(...)` itself is not a plausible primary
bottleneck. Its implementation is a direct dict return with no loops, database
lookups, or heavy normalization.

The coarse timing currently wraps argument evaluation before the call:

- `capabilities=normalize_capabilities(_load_capabilities_for_user(env, user))`
- already-built `nav_tree`, `nav_meta`, `default_route`, `intents`, and
  `feature_flags` values being passed through

The only obviously expensive expression still evaluated inline at call time is:

- `_load_capabilities_for_user(env, user)` plus `normalize_capabilities(...)`

## Ownership Decision

The next implementation batch should not optimize `build_base()` itself.

That batch has now been executed and the new timing split shows:

- `load_capabilities_for_user`: about `7821ms`
- `normalize_capabilities`: about `25ms`
- `build_base_call`: `0ms`

## Updated Ownership Decision

The real hotspot is now assigned precisely:

1. capability loading for the current user dominates the entire
   `build_base_payload` wrapper
2. capability normalization is negligible at current scale
3. final `build_base()` dict assembly is negligible

The follow-up batch should move from diagnostics to runtime optimization on the
capability-provider path, not on payload assembly.

# Industry Shadow Bridge Migration Report v1

## Scope

Execution chain: `ITER-2026-04-05-1067` to `ITER-2026-04-05-1082`

Target: migrate ownership from industry shadow bridge (`smart_construction_core`
`smart_core_*` hooks) to platform-owned runtime/protocol paths in `smart_core`.

## Completed Ownership Migrations

1. intent registration ownership
   - platform owns contribution collect/validate/merge/register pipeline
   - industry exports `get_intent_handler_contributions`
   - deprecated `smart_core_register` removed from industry module

2. capability ownership
   - platform owns capability contribution collection path
   - industry exports `get_capability_contributions` and
     `get_capability_group_contributions`
   - legacy capability hook exports removed

3. scene access ownership
   - platform scene access switched to direct-connect first
   - industry P0 scene bridge exports removed

4. policy constant ownership
   - platform policy defaults centralized in
     `addons/smart_core/core/platform_policy_defaults.py`
   - policy consumers switched to platform owner path
   - industry policy legacy exports removed

5. system.init extension ownership
   - platform collector `apply_extension_fact_contributions` introduced
   - industry exports `get_system_init_fact_contributions`
   - legacy `smart_core_extend_system_init` removed

6. create-field fallback ownership naming
   - industry fallback hook migrated to
     `get_create_field_fallback_contributions`
   - legacy `smart_core_create_field_fallbacks` export removed

## Verification Guards Added

`make verify.architecture.*` targets now available for:

- `intent_registry_single_owner_guard`
- `capability_registry_platform_owner_guard`
- `scene_bridge_industry_proxy_guard`
- `platform_policy_constant_owner_guard`
- `system_init_extension_protocol_guard`
- `system_init_heavy_workspace_payload_guard`

All guards were executed and passed in migration chain.

## Compatibility Status

- platform compatibility fallbacks are still retained at loader/policy collection
  layer where needed for broader extension ecosystem safety.
- high-risk forbidden domains (`security/**`, `record_rules/**`, `__manifest__.py`,
  financial domains) remained untouched in this chain.

## Residual / Next Actions

1. run bounded runtime validation in target environments to confirm no external
   dependency on removed legacy hook names.
2. optionally tighten architecture guards from structural checks to usage-level
   assertions after rollout evidence is collected.
3. evaluate startup workspace heavy payload decoupling completion against
   runtime-fetch strategy in dedicated batch.

## Outcome

This migration chain reached boundary-governance objective:

- platform owns registration/merge/expose pathways
- industry module reduced to contribution provider role
- shadow-bridge ownership residue materially reduced and audited


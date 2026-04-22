# Scene Governance

## 1. Purpose

This directory freezes the backend scene-governance rules used to manage scene
identity, entry semantics, runtime bootstrap, family governance, failure model,
and verify guards.

## 2. Scope

Applies to:

- scene registry / provider / runtime bootstrap / menu interpreter governance
- scene-ready contract delivery chains
- family-level backend scenification governance

Does not apply to:

- raw native Odoo menu/action/view definitions by themselves
- frontend rendering or styling details

## 3. Document Map

- `scene_governance_overview_v1.md`
  - governance background, current stage, and current-round goals
- `scene_authority_hierarchy_v1.md`
  - who owns which scene semantics
- `scene_entry_semantics_v1.md`
  - canonical entry, native entry, and fallback semantics
- `system_init_runtime_chain_v1.md`
  - runtime bootstrap chain and stage boundaries
- `scene_family_governance_v1.md`
  - family as the minimum governance unit
- `scene_failure_model_v1.md`
  - failure types and diagnosis model
- `scene_verify_guard_spec_v1.md`
  - verify guard expectations and gate levels

## 4. Reading Order

1. `scene_governance_overview_v1.md`
2. `scene_authority_hierarchy_v1.md`
3. `scene_entry_semantics_v1.md`
4. `system_init_runtime_chain_v1.md`
5. `scene_family_governance_v1.md`
6. `scene_failure_model_v1.md`
7. `scene_verify_guard_spec_v1.md`

## 5. Asset Templates

Structured asset templates live under `assets/`:

- `scene_authority_matrix_v1.csv`
- `scene_family_inventory_v1.csv`
- `scene_failure_codes_v1.csv`

Generated current-state exports live under `assets/generated/`:

- `scene_authority_matrix_current_v1.csv`
- `scene_family_inventory_current_v1.csv`
- `menu_scene_mapping_current_v1.csv`
- `provider_completeness_current_v1.csv`

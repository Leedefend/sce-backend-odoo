# Scene Verify Guard Spec v1

## 1. Goal

Turn scene-governance rules into executable guards so authority drift, entry
drift, compatibility confusion, and provider gaps cannot silently return.

## 2. Gate Levels

- `required`
  - blocks ordinary governance progression when it fails
- `advisory`
  - must be read and tracked, but does not block every low-risk batch
- `audit-only`
  - inventory/coverage oriented, used for governance reporting rather than hard
    gate decisions

## 3. Required Guard Classes

### 3.1 Authority Consistency Guard

Intent:

- detect duplicate or conflicting identity definitions
- detect registry authority drift
- freeze required authority fields for governed scenes

Current mapped guard:

- `scripts/verify/backend_scene_authority_guard.py`

Current gate level:

- `required`

Current artifact expectations:

- `artifacts/backend/backend_scene_authority_guard.json`
- `artifacts/backend/backend_scene_authority_guard.md`

### 3.2 Canonical Entry Uniqueness Guard

Intent:

- ensure governed scenes keep declared canonical semantics
- ensure scene work, compatibility, and route-only modes do not drift

Current mapped guard:

- `scripts/verify/backend_scene_canonical_entry_guard.py`

Current gate level:

- `required`

Current artifact expectations:

- `artifacts/backend/backend_scene_canonical_entry_guard.json`
- `artifacts/backend/backend_scene_canonical_entry_guard.md`

### 3.3 Menu-Scene Mapping Guard

Intent:

- ensure menu interpretation remains stable
- ensure scene/fallback/unavailable classification remains explainable

Current mapped guard:

- `scripts/verify/backend_scene_menu_mapping_guard.py`

Current gate level:

- `required`

### 3.4 Provider Completeness Guard

Intent:

- ensure published scenes have provider coverage or explicit fallback
- prevent provider absence from remaining implicit

Current mapped guard:

- `scripts/verify/backend_scene_provider_completeness_guard.py`

Current gate level:

- `required` for governance batches that materialize generated provider assets
- `advisory` for older batches that predate the generated asset flow

## 4. Current Additional Guard Class

### 4.1 Task-Family Compat Gap Guard

Intent:

- freeze task-family residual compat semantics
- prevent `project.task.list` and `project.task.board` from silently drifting
  back into borrowed ownership

Current mapped guard:

- `scripts/verify/backend_task_family_compat_gap_guard.py`

Current gate level:

- `required` for task-family and task-board governance batches
- `advisory` outside those batches

## 5. Expected Artifacts

Every required/advisory guard should be able to emit:

- summary json
- summary markdown
- fail reason list

Optional:

- detail csv/json

## 6. Unified Suite

Current unified governance suite:

- `python3 scripts/verify/scene_governance_suite.py`

Current suite sequence:

1. governance asset export
2. authority consistency guard
3. canonical entry guard
4. menu-scene mapping guard
5. task-family compat gap guard
6. provider completeness guard
7. family priority scoring

## 7. Guard-to-Failure Expectations

At minimum, guards should be traceable back to these failure classes:

- `identity_missing`
- `authority_conflict`
- `canonical_entry_missing`
- `compatibility_fallback_used`
- `native_only_degraded`
- `provider_missing`
- `record_context_insufficient`
- `runtime_build_failed`

## 8. Current Package Status

Current materialized guard set:

- authority consistency
- canonical entry uniqueness
- menu-scene mapping
- provider completeness
- task-family compat gap

Current missing dedicated guard set:

- failure coverage audit
- runtime chain segment audit
- delivery tier completeness audit

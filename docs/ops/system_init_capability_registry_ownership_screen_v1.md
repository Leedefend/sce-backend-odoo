# System Init Capability Registry Ownership Screen v1

## Goal

Determine whether the current capability registry path in `system.init` is
correctly consuming stable platform facts or still performing request-time
native capability discovery that overlaps with platform-kernel and scene
orchestration responsibilities.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel boundary diagnostics
- Module: capability registry ownership screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: kernel
- Reason: before continuing any performance work, the repository needs an
  explicit judgment on whether `native_projection` belongs in the `system.init`
  mainline at all

## Relevant Architecture Facts

### 1. `system.init` should remain an orchestration shell

`docs/architecture/system_init_runtime_context_v1.md` defines `system.init` as:

- bootstrap input preparation
- runtime context construction
- scene runtime orchestration
- surface assembly
- response metadata assembly

That document does not position `system.init` as a request-time capability
discovery engine.

### 2. Scene orchestration must consume already-parsed facts

`docs/architecture/scene_orchestration_layer_design_v1.md` freezes that scene
orchestration should:

- consume normalized native structure
- consume business verdicts
- organize and enhance scene contract output

It must not become a second fact-discovery layer.

### 3. Contract/governance layers may constrain facts, not become new fact sources

`docs/architecture/backend_contract_layer_responsibility_freeze_v1.md` freezes:

- earlier layers own business facts and native structure facts
- governance may project or annotate those facts
- governance must not become a competing fact source

### 4. Platform capability codes should be stable semantics, not raw native objects

`docs/architecture/capabilities.md` states capability codes are:

- stable capability codes
- not menus
- not models

This is the target semantic ownership line.

## Current Code Path

The current `system.init` path loads capabilities through:

- `addons/smart_core/handlers/system_init.py`
- `addons/smart_core/core/capability_provider.py`
- `addons/smart_core/app_config_engine/capability/core/registry.py`
- `addons/smart_core/app_config_engine/capability/core/contribution_loader.py`

Inside `load_capability_contributions_with_timings(...)`, the hot path still
executes:

- `native_projection`

which in turn calls `load_native_capability_rows(...)` from:

- `addons/smart_core/app_config_engine/capability/native/native_projection_service.py`

That function sequentially projects capabilities from:

- `ir.ui.menu`
- `ir.actions.act_window`
- `ir.model` + `ir.model.access`
- `ir.actions.server`
- `ir.actions.report`
- `ir.actions.act_window.view`

## Ownership Judgment

### Judgment A: this is not just ordinary consumption of already-materialized intent facts

The current `native_projection` path is not simply reading a stable capability
registry that has already been resolved elsewhere.

Instead, it re-discovers capability candidates directly from broad Odoo native
metadata sources on the request path.

### Judgment B: this is closer to a compatibility/bootstrap discovery layer

Because capability codes are intended to be stable semantic codes rather than
menus/models, the current native-projection path is better classified as:

- bootstrap compatibility projection
- dynamic discovery fallback
- registry materialization support path

and not as the ideal steady-state source of truth for `system.init`.

### Judgment C: leaving this in the main startup hot path creates a boundary overlap

The overlap is:

- platform kernel wants stable capability semantics
- `system.init` wants orchestration over already-known runtime facts
- `native_projection` is still discovering capability candidates from native
  metadata at request time

So the current implementation is not a pure ownership model. It is a mixed
transition state.

## Final Conclusion

The repository is currently carrying two capability-registry modes at once:

1. target mode:
   - stable capability semantics / registry facts
2. transition mode:
   - request-time native metadata projection into capability candidates

Therefore:

- continuing with adapter-level performance tuning alone would only treat the
  symptom
- the deeper issue is ownership and materialization boundary

## Recommended Next Batch

The next batch should not directly continue micro-optimizing `model_adapter.py`.

It should open a boundary-recovery screen or design batch that answers:

- what the canonical capability registry fact source is
- whether `native_projection` remains allowed only as fallback/bootstrap
- whether capability materialization should happen before request time
- what invalidation/versioning path governs that materialized registry
- whether `system.init` may consume fallback-discovered capabilities at all in
  steady state

## Operational Consequence

Until that boundary is decided, further performance optimization of
`native_projection` should be treated as provisional stop-gap work, not as the
primary architecture direction.

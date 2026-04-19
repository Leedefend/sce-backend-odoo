# System Init Native Model Adapter Screen v1

## Goal

Map the native model adapter residual to the smallest safe optimization target.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: native model adapter screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: current evidence shows `native_projection` is the next outer hotspot,
  and `project_model_access_capabilities(...)` is the heaviest-looking bounded
  adapter in that fan-out

## Code Mapping

`addons/smart_core/app_config_engine/capability/native/model_adapter.py`

`project_model_access_capabilities(...)` currently executes in this order:

1. `ir.model.search_read([('transient', '=', False)], limit=4000)`
2. derive `model_ids`
3. `ir.model.access.search_read([('model_id', 'in', model_ids)], limit=4000)`
4. compute current user group ids
5. load XMLIDs for all `model_ids`
6. aggregate ACL rows into `perms_by_model`
7. project output rows

## Cost Shape

The current order is expensive because it does full-width work before narrowing:

- reads up to `4000` model rows up front
- then reads ACL rows for that full model set
- then loads XMLIDs for that full model set
- only after that filters ACL applicability by current user groups

So even if the current user can actually see a much smaller subset, the adapter
still pays for broad model + XMLID loading first.

## Safe Optimization Direction

The lowest-risk optimization is to reverse the narrowing order:

1. compute current user group ids first
2. read `ir.model.access`
3. filter to user-applicable ACL rows
4. derive the minimal set of relevant `model_id`s
5. load only those `ir.model` rows
6. load XMLIDs only for that reduced set

This does not change ACL semantics, because permission aggregation still comes
from the same `ir.model.access` rows for the same user-group set. It only
avoids broad reads before narrowing.

## Recommended Next Batch

Open one bounded runtime optimization batch on:

- `addons/smart_core/app_config_engine/capability/native/model_adapter.py`

with the explicit goal of narrowing from ACL rows first and only then reading
matching model rows / XMLIDs.

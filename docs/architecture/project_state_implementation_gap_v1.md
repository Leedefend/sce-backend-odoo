# Project State Implementation Gap v1

## Governance Baseline

The frozen governance decision says:

```text
lifecycle_state = business truth
stage_id = UI projection
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
```

## Current Alignment

| Area | Status | Notes |
| --- | --- | --- |
| lifecycle truth field | aligned | `lifecycle_state` is state-machine backed and used in header |
| lifecycle -> stage sync | aligned | create/write map lifecycle to stage |
| stage -> lifecycle reverse sync | aligned | no direct reverse write found |
| stage as independent UI projection | partial | guarded stage writes are still allowed |
| signal -> stage sync | gap | `_sync_stage_from_signals` can advance `stage_id` from business facts without lifecycle transition |
| import default behavior | conditional | create-only import defaulted to `draft` + `筹备中` |

## Risks

### Risk 1: Stage Can Diverge From Lifecycle

Manual stage writes are blocked only when they exceed derived business stage.
They may still change stage backward or within the allowed derived boundary
without changing lifecycle.

Impact:

- UI stage may no longer be a strict projection of lifecycle.
- Users may read stage as business truth even when lifecycle remains unchanged.

### Risk 2: Signal Sync Can Advance Stage Without Lifecycle

`_sync_stage_from_signals` can advance `stage_id` based on BOQ/task/material or
settlement/payment signals. This is useful as UI guidance, but it violates the
strict interpretation that stage is derived only from lifecycle.

Impact:

- stage can encode business facts not represented in `lifecycle_state`;
- import expansion may inherit a mixed status model.

### Risk 3: Expansion Could Normalize The Mixed Model

The 30-row write trial produced `lifecycle_state=draft` and `stage_id=筹备中`.
This is acceptable for skeleton records. Larger imports should not proceed
until the team decides whether signal-derived stage progression is allowed as a
UI-only projection.

## Safety Assessment

Current implementation is conditionally safe for the already-created 30-row
trial because no reverse lifecycle mutation exists and all records use the
default `筹备中` stage.

Current implementation is not safe enough for sample expansion under the strict
governance rule until the stage divergence and signal-sync behavior are either:

- explicitly accepted as UI-only behavior; or
- changed in a later implementation alignment batch.

# Project State Governance Decision v1

## Final Answers

| Question | Decision |
| --- | --- |
| 是否采用双状态体系 | Yes. |
| lifecycle 是否主状态 | Yes. `lifecycle_state` is the truth state. |
| stage 是否仅用于 UI | Yes. `stage_id` is UI/native stage projection. |
| 是否允许双向同步 | No. Only lifecycle -> stage is allowed as truth flow. |
| 是否允许用户修改阶段 | Only as guarded UI stage movement; it must not update lifecycle truth. |

## Final Architecture Decision

```text
lifecycle_state = business fact truth layer
stage_id = Odoo UI/native stage projection
```

The system should converge to one-way synchronization:

```text
lifecycle_state -> stage_id
```

Reverse synchronization is not allowed:

```text
stage_id -/-> lifecycle_state
```

## Import Decision

Migration import should write normalized `lifecycle_state` when approved, then
derive `stage_id` from the mapping table.

Until lifecycle conversion is approved, create-only skeleton imports may rely on
default `lifecycle_state=draft` and default `stage_id=筹备中`.

## User Operation Decision

Users may request lifecycle transitions through guarded business actions.

Users must not be able to turn a UI stage drag into lifecycle truth. Dragging
stage should either be UI-only and guarded, or blocked if it would imply a
business transition.

## Current Follow-Up

This batch is documentation-only. If the current implementation still allows
more stage influence than this policy permits, open a later implementation gate
to align code with this decision. Do not change frontend behavior to compensate.

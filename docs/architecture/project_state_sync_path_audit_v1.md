# Project State Sync Path Audit v1

## Audit Question

Does current code implement:

```text
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
```

## Lifecycle To Stage Paths

| Path | Current behavior | Alignment |
| --- | --- | --- |
| `create()` | if `lifecycle_state` absent, sets `draft`; then sets `stage_id` from `_get_stage_for_lifecycle` | aligned |
| `write({"lifecycle_state": ...})` | validates lifecycle transition; if no explicit `stage_id`, maps lifecycle to stage and writes `stage_id` | aligned |
| `_sync_stage_from_lifecycle()` | maps current lifecycle to stage | aligned |
| missing stage repair | if neither lifecycle nor stage was written, records without `stage_id` can sync from lifecycle | aligned |

## Stage To Lifecycle Paths

No direct write path was found that sets `lifecycle_state` from `stage_id`.

| Path | Current behavior | Alignment |
| --- | --- | --- |
| `write({"stage_id": ...})` without lifecycle | computes current business-derived stage key and blocks movement beyond derived state; does not write lifecycle | partially aligned |
| `stage_id` drag / direct write | can still change `stage_id` within guard boundaries without lifecycle change | gap |
| `_get_stage_key_from_stage()` | resolves stage key for guard logic; does not change lifecycle | aligned |

## Business Signal To Stage Paths

| Path | Current behavior | Alignment |
| --- | --- | --- |
| `_sc_compute_stage_key()` | derives a stage key from lifecycle plus BOQ/task/material/settlement/payment signals | mixed |
| `_sync_stage_from_signals()` | advances `stage_id` from derived business signals using `sc_stage_sync` context | gap against pure lifecycle projection |
| `action_sc_stage_sync()` | manually triggers signal-based stage sync | gap |

## Audit Result

| Question | Answer |
| --- | --- |
| lifecycle -> stage 是否成立 | Yes. It exists in create/write/sync paths. |
| 是否存在 stage -> lifecycle | No direct reverse lifecycle write was found. |
| 是否存在 stage 作为业务状态使用 | Yes, stage is used as guarded UI/business-signal projection and can be written independently within guard boundaries. |

## Sync Path Conclusion

The dangerous reverse truth path `stage_id -> lifecycle_state` was not found.
However, current implementation is not a pure one-way projection because
business signals and guarded manual stage writes can change `stage_id` without a
lifecycle change.

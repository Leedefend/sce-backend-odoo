# Project State Control Policy v1

## Control Principle

`lifecycle_state` is the truth layer. It must be protected by business
transition guards. `stage_id` is the UI stage projection and must not override
truth.

## System-Only States

These transitions require system or controlled workflow logic:

| Target lifecycle_state | Control |
| --- | --- |
| `done` | system/workflow-controlled; requires completion evidence |
| `closing` | system/workflow-controlled; requires settlement/closing evidence |
| `warranty` | system/workflow-controlled; requires completion and warranty condition |
| `closed` | system/workflow-controlled; terminal / archived state |

## Human-Allowed Changes

Human operations may request:

| Transition | Condition |
| --- | --- |
| `draft -> in_progress` | allowed only after project start requirements pass |
| `in_progress -> paused` | allowed with business reason |
| `paused -> in_progress` | allowed with resume reason |

Human operations must call lifecycle transition actions or guarded lifecycle
write paths, not raw stage edits.

## Jump Policy

Uncontrolled jump stages are not allowed. The state machine currently defines
legal transitions:

| From | Allowed To |
| --- | --- |
| `draft` | `in_progress`, `paused`, `closed` |
| `in_progress` | `paused`, `done`, `closing`, `closed` |
| `paused` | `in_progress`, `closed` |
| `done` | `closing`, `warranty`, `closed` |
| `closing` | `warranty`, `closed` |
| `warranty` | `closed` |
| `closed` | none |

## Validation Policy

Validation should prevent:

- entering `in_progress` without required start evidence;
- entering closing/completion states without required settlement/payment/BOQ
  evidence;
- stage movement that exceeds derived business facts;
- update/upsert import bypassing lifecycle rules.

## Stage Policy

`stage_id` may be changed by system sync after lifecycle changes. Manual stage
changes are UI-level and must remain guarded. Manual stage movement must not
modify lifecycle truth.

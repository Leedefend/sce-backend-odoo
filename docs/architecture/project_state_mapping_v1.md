# Project State Mapping v1

## Canonical Mapping

| lifecycle_state | Business label | stage_id target | Stage label |
| --- | --- | --- | --- |
| `draft` | 筹备 | `smart_construction_core.project_stage_planning` | 筹备中 |
| `in_progress` | 在建 | `smart_construction_core.project_stage_running` | 在建 |
| `paused` | 停工 | `smart_construction_core.project_stage_paused` | 停工 |
| `done` | 完工 / 竣工 | `smart_construction_core.project_stage_closed` | 竣工 |
| `closing` | 结算中 | `smart_construction_core.project_stage_closing` | 结算中 |
| `warranty` | 保修期 | `smart_construction_core.project_stage_warranty` | 保修期 |
| `closed` | 关闭 | `smart_construction_core.project_stage_archived` | 关闭 |

## Business-Friendly Import Labels

| Migration lifecycle concept | lifecycle_state | stage label |
| --- | --- | --- |
| 筹备 | `draft` | 筹备中 |
| 已签约 | `draft` until contract-specific gate approves a separate value | 筹备中 |
| 在建 | `in_progress` | 在建 |
| 完工 | `done` | 竣工 |

## Notes

The user example included `已签约 -> 待启动`. The current project lifecycle
state machine does not have a dedicated `signed` or `pending_start` value, and
current stage seed data does not contain `待启动`. Therefore this governance
version does not invent new runtime states.

If the business requires a distinct signed-but-not-started state later, open a
new model/state extension gate. Do not overload `stage_id` to create hidden
business truth.

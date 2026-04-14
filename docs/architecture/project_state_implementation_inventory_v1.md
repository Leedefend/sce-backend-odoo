# Project State Implementation Inventory v1

## Scope

Read-only audit of current `project.project` state implementation against the
frozen governance rule:

```text
lifecycle_state = 主状态
stage_id = UI投影
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
```

No code, model, view, or import logic was changed.

## State Assets

| Asset | Type | Current implementation |
| --- | --- | --- |
| `lifecycle_state` | `fields.Selection` | uses `ScStateMachine.selection(ScStateMachine.PROJECT)`; default `draft`; tracked |
| `stage_id` | `fields.Many2one` | uses `project.project.stage`; default `_default_stage_id`; indexed/tracked |
| `project.project.stage` | Odoo stage model | extended with `is_default`, `description`, `mail_template_id` |
| `legacy_state` | `fields.Char` | preserves old `STATE`; not normalized truth |
| `legacy_stage_id` | `fields.Char` | preserves old `XMJDID`; not normalized truth |
| `legacy_stage_name` | `fields.Char` | preserves old `XMJD`; not normalized truth |
| `sc_execution_state` | `fields.Selection` | execution sub-state, not project lifecycle truth |

## Stage Seed Inventory

| Stage XMLID | Stage label | Lifecycle candidate |
| --- | --- | --- |
| `project_stage_planning` | 筹备中 | `draft` |
| `project_stage_running` | 在建 | `in_progress` |
| `project_stage_paused` | 停工 | `paused` |
| `project_stage_closed` | 竣工 | `done` |
| `project_stage_closing` | 结算中 | `closing` |
| `project_stage_warranty` | 保修期 | `warranty` |
| `project_stage_archived` | 关闭 | `closed` |

## UI Inventory

The native project form header replaces the original `stage_id` statusbar with
`lifecycle_state`:

```text
//form/header//field[@name='stage_id'] -> lifecycle_state statusbar
```

This is aligned with the governance decision that lifecycle is the visible
business status.

## Implementation Inventory Conclusion

The implementation already contains the core assets needed for the frozen
policy. The main audit question is not missing fields; it is whether all write
paths treat `lifecycle_state` as truth and `stage_id` as projection only.

# Project State System Inventory v1

## Scope

This inventory covers `project.project` state semantics only. It does not change
code, models, import logic, or data.

## A. Native Stage System

| Asset | Current role | Evidence |
| --- | --- | --- |
| `project.project.stage` | Odoo native stage model extended by `smart_construction_core` | `_inherit = "project.project.stage"` |
| `project.project.stage.is_default` | marks the default UI stage | `project_stage_planning` has `is_default=True` |
| `project.project.stage.description` | stage explanation text | custom field |
| `project.project.stage.mail_template_id` | optional stage notification template | custom field |
| `project.project.stage_id` | Odoo project stage field overridden to `project.project.stage` and indexed/tracked | default comes from `_default_stage_id` |

Current stage seed values:

| XML ID | Stage | Sequence | Role |
| --- | --- | ---: | --- |
| `project_stage_planning` | 筹备中 | 5 | default / preparation UI stage |
| `project_stage_running` | 在建 | 10 | running UI stage |
| `project_stage_paused` | 停工 | 20 | paused UI stage |
| `project_stage_closed` | 竣工 | 30 | completed UI stage |
| `project_stage_closing` | 结算中 | 40 | closing UI stage |
| `project_stage_warranty` | 保修期 | 50 | warranty UI stage |
| `project_stage_archived` | 关闭 | 60 | folded archived UI stage |

## B. Custom State System

| Field | Type | Current role |
| --- | --- | --- |
| `lifecycle_state` | Selection from `ScStateMachine.PROJECT` | project lifecycle business state |
| `sc_execution_state` | Selection | execution-progress sub-state, not the main lifecycle truth |
| `legacy_stage_id` | Char | raw legacy `XMJDID` preservation |
| `legacy_stage_name` | Char | raw legacy `XMJD` preservation |
| `legacy_state` | Char | raw legacy `STATE` preservation |
| `legacy_project_nature` | Char | raw legacy project nature |
| `legacy_is_material_library` | Char | raw legacy material-library marker |

Current `lifecycle_state` values:

| Key | Label |
| --- | --- |
| `draft` | 草稿 |
| `in_progress` | 在建 |
| `paused` | 停工 |
| `done` | 竣工 |
| `closing` | 结算中 |
| `warranty` | 保修期 |
| `closed` | 关闭 |

## C. Current Usage

| Surface | Current behavior |
| --- | --- |
| Native form header | replaces native `stage_id` statusbar with `lifecycle_state` statusbar |
| Construction information tab | displays `lifecycle_state` as a field |
| Create path | defaults `lifecycle_state` to `draft`; then maps lifecycle to `stage_id` |
| Write path | lifecycle changes validate transitions and sync `stage_id` when absent |
| Stage-only write path | currently blocks stage movement beyond derived business signals, but does not rewrite `lifecycle_state` |
| Signal sync | `_sync_stage_from_signals` can advance `stage_id` based on execution/settlement signals |
| Migration safe slice | first write trial did not write `lifecycle_state` or `stage_id`; system default created `lifecycle_state=draft` and `stage_id=筹备中` |

## Inventory Conclusion

The project model already has a dual-state surface:

- `lifecycle_state` is the business lifecycle field and is already the form
  header statusbar.
- `stage_id` is still the Odoo native stage carrier and receives default/sync
  values.

The governance gap is not missing fields. The gap is that the source of truth
must be stated explicitly before migration expands.

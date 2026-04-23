# Project Stage Default Behavior Review v1

## Scope

- Target database: `sc_demo`
- Target model: `project.project`
- Reviewed records: 30 write-trial project skeletons
- Source artifact: `artifacts/migration/project_rollback_dry_run_result_v1.json`

This document diagnoses default `stage_id` behavior only. It does not modify
project stages.

## Stage Distribution

| stage_id | stage_name | count |
| ---: | --- | ---: |
| 5 | 筹备中 | 30 |

## Answers

| Question | Answer |
| --- | --- |
| 这 30 条记录的 `stage_id` 分布 | All 30 records use `stage_id=5`, `stage_name=筹备中`. |
| 是否全部同一个默认值 | Yes. |
| 当前默认阶段的业务含义 | `筹备中` indicates a preparation-stage project skeleton, before later lifecycle/state mapping. |
| 该默认值是否可接受 | Conditionally acceptable for create-only skeleton records if the business accepts all first-round imported projects entering preparation by default. |
| 如果不可接受，后续在哪个门禁处理 | Handle in the next safe-import write gate before expanding samples; do not patch this through rollback or frontend logic. |

## Interpretation

The write script did not explicitly write `stage_id`. The uniform value suggests
Odoo/project default stage assignment during `project.project` creation.

This default is safer than missing stage metadata for native Odoo behavior, but
it is a business decision. If imported skeletons should not appear as `筹备中`,
the next import gate must explicitly define a stage policy before any sample
expansion.

## Current Decision

`stage_id=5 / 筹备中` is conditionally acceptable for the already-created 30-row
trial. It is not yet approved for expanded imports until manual review confirms
the default-stage policy.

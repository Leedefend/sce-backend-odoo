# Project Create-Only 100-Row Business Usability Review v1

Iteration: `ITER-2026-04-13-1837`

Status: `PASS`

Target state: `USABILITY_REVIEW_READY`

Mode: read-only business usability review.

## Scope

This review covers the 100 `project.project` rows created in `ITER-2026-04-13-1835` and locked by `ITER-2026-04-13-1836`.

This review did not create, update, delete, rollback, expand, or advance lifecycle state.

## Inputs

- Locked post-write snapshot: `artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv`
- Rollback dry-run lock: `artifacts/migration/project_expand_rollback_dry_run_result_v1.json`
- Review artifact: `artifacts/migration/project_create_only_expand_manual_review_result_v1.json`

## 1836 Background Evidence

The 100-row batch is still valid as the review target:

| Item | Result |
|---|---:|
| Locked target rows | 100 |
| Current matched records | 100 |
| Missing rows | 0 |
| Duplicate matches | 0 |
| Out-of-scope matches | 0 |
| Projection mismatches | 0 |

## Sample Strategy

The review uses deterministic sampling from the locked 100-row snapshot:

- Deep review: 10 rows.
- Quick page review: 20 rows.
- Full background: 100 rows inherited from the 1836 rollback dry-run lock.

Deep review sample:

| project.id | legacy_project_id | Name | Result |
|---:|---|---|---|
| 2137 | `092bc953078b42ab89b7a9d07fecab66` | 德阳市罗江区自来水公司2019年12月至2020年11月管网安装（抢修）零星土石方开挖恢复及用工等外包 | PASS |
| 2138 | `0a098ceefc5046c380028104a3caa2af` | 中建天投天河区育新街南侧AT0304011-1地块项目 | PASS |
| 2139 | `0b3b88a05d6d454b9cbbe6b4c3c342d5` | 岳普湖县防沙治沙电力配套设施建设项目 | PASS |
| 2146 | `0bb1dac8c9a94e39b421b3a619491c1f` | 公司综合管理平台 | PASS |
| 2156 | `0f314b7eb259455f8ad3bb3419f66957` | 绵竹市星旺大桥与货运通道连接匝道工程项目 | PASS |
| 2176 | `15bc8bfa1f964a609140a3c52c72efaa` | 重庆江北国际机场飞行区服务综合服务外包项目 | PASS |
| 2196 | `1b94da17ad1a42c291a59a5ec6d4996b` | 2025年西南石油工程公司钻前辅助工程劳务框架招标（5标段：中江、孝泉等地区）项目 | PASS |
| 2216 | `211a1be6b5ee4d6c830d2cf06378107b` | 德阳凯州新城检验检测创新产业园建设项目-实验室装修项目 | PASS |
| 2235 | `28020d9fe0c345f295ebbf4b41c119e4` | 绵竹市城区停车场建设项目二期设计施工（一标段）项目模板脚手架专业分包工程 | PASS |
| 2236 | `282fc5242a4f465cae7d7630c279ef91` | 德阳市寿丰河截污干管工程、中江县城 镇污水处理设施及配套管网项目等四个项目厂站及管网维修、服务单 | PASS |

## Native Page Readability

The review script checked the native Odoo form, tree/list, and kanban server-side view definitions for `project.project`. Nested x2many subviews were resolved against their own comodels to avoid false positives from task fields inside project form subviews.

| View | Loaded | Field refs | Missing field refs | Result |
|---|---:|---:|---:|---|
| form | yes | 52 | 0 | PASS |
| tree/list | yes | 14 | 0 | PASS |
| kanban | yes | 25 | 0 | PASS |

Quick page review covered 20 locked sample rows. Each checked row was searchable by name, readable as a form record, and had kanban-required display/stage fields available.

## State And Label Consistency

All 10 deep review rows are in the expected initial business state:

- `lifecycle_state = draft`
- lifecycle-derived label = `筹备中`
- `project_payload.stage_name = 筹备中`
- `state_explain.stage_label = 筹备中`
- `project_context.stage_label = 筹备中`
- `project_insight.stage = 筹备中`
- header summary `stage_name = 筹备中`
- header semantic summary `current_stage = 筹备中`

No `stage_name / stage_label / current_stage` mismatches were found.

## Read-Side Output Review

The following read-side outputs were generated successfully for each deep sample:

- `project payload`
- `state explain`
- `project context`
- `project insight`
- dashboard/header summary
- `flow_map`
- dashboard `next_actions`
- execution `next_actions`

Observed flow/action shape:

- `flow_map.current_stage = initiation`
- `flow_map.items = 5`
- dashboard `next_actions.action_count = 4`
- execution `next_actions.action_count = 4`

These are consistent with a create-only project skeleton in `draft` / `筹备中`.

## Decision

Result: `PASS`

Recommendation: keep the 100-row sample as an observation sample.

The sample does not need immediate rollback based on this usability review. The next low-risk step is the observation-retention decision and follow-up action constraint batch.

Next recommended batch: `ITER-2026-04-13-1838 project create-only 100-row observation sample retention decision`.

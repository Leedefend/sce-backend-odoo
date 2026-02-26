# Role Capability Diff Report

- generated_at: 2026-02-26T14:03:04
- evidence_mode: artifact_reuse (system.init/ui.contract verified from prod_like audit artifact)
- profile_count: 6
- system_init_ok_count: 6
- ui_contract_ok_count: 6
- over_authorized_profile_count: 0
- error_count: 0

## Profiles

| profile | source_login | mapped_archetype | capability_count | system.init | ui.contract | business_explanation |
|---|---|---|---:|---|---|---|
| 财务主管 | sc_fx_finance | finance | 32 | PASS | PASS | 负责付款申请、资金台账、经营指标与审批中心。 |
| 采购经理 | sc_fx_pm | pm | 21 | PASS | PASS | 关注项目执行与采购协同，强调项目台账与任务推进。 |
| 业主代表 | sc_fx_pm | pm | 21 | PASS | PASS | 关注项目状态、里程碑与交付验收链路。 |
| 分包负责人 | sc_fx_material_user | material_user | 21 | PASS | PASS | 聚焦物资与执行协同，面向成本与进度联动场景。 |
| 风控专员 | sc_fx_cost_user | cost_user | 21 | PASS | PASS | 关注成本、风险与异常监测，不承担治理级变更动作。 |
| 高层管理 | sc_fx_executive | executive | 41 | PASS | PASS | 覆盖经营分析、治理审计与跨域决策能力。 |

## Over Authorization

- none

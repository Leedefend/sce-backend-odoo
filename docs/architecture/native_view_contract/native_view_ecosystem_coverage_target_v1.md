# Native View Ecosystem Coverage Target v1

## Goal
将当前“样本级通过”提升为“生态级全覆盖”，作为切换前端大规模迭代前的后端契约硬门槛。

## Scope
- View types: `form`, `tree`, `kanban`, `search`
- Contract surfaces: `native_view`, `semantic_page`, `actions`, `permission_verdicts`, `action_gating`
- Governance chain: `verify.contract.preflight`, `verify.phase_next.evidence.bundle`

## Ecosystem-Level Definition
满足以下条件才可判定为“生态级全覆盖”：

1. 样本覆盖
- 覆盖 `20+` 模型样本，且跨至少 `6` 业务域（项目、任务、合同、成本、资金、协同/附件）。
- 每类视图至少 `4` 个样本（form/tree/kanban/search）。

2. 结构完整
- `semantic_page` 必须通过 `shape + schema` 双守卫。
- `search_semantics` 必须包含 `filters/group_by/search_fields/search_panel/favorites/quick_filters`。
- `kanban_semantics` 必须包含 `title_field/card_fields/metric_fields`。
- `x2many` 关系必须包含 `items + editable + row_actions`。

3. 行为与权限闭环
- `permission_verdicts` 全键齐全：`read/create/write/unlink/execute`。
- `action_gating` 必须输出 `record_state/policy/verdict`。
- 行级/卡片动作必须有 `enabled + reason_code`。

4. 证据链纳入
- `native_view_semantic_guard` 出现在 `phase11_1_contract_evidence.json`。
- `backend_evidence_manifest` 摘要包含：
  - `native_view_semantic_shape_ok`
  - `native_view_semantic_schema_ok`

## Exit Criteria (Go/No-Go)
- `verify.native_view.semantic_page`: PASS
- `verify.native_view.coverage.report`: PASS
- `verify.native_view.samples.compare`: PASS
- 生态样本 readiness 报告显示：
  - `total_case_count >= 20`
  - `ready_case_count == total_case_count`
  - `pass_ratio == 1.0`

满足上述条件后，允许进入“前端产品化深迭代阶段”。


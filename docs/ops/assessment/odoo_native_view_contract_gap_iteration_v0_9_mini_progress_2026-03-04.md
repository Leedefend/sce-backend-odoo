# Odoo 原生承载差距迭代进展（v0.9-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_9`

## 已完成项

1. e2e grouped 签名升级到 `v0.4`，新增能力位：
   - `supports_group_key`
   - `supports_page_flags`
   - `supports_page_window`
   - `request_offset_matches_observed`
   - `page_window_matches_range`
2. 新增 `grouped_contract_consistency_guard`，校验：
   - fe_tree grouped 基线能力位
   - e2e grouped 基线结构与类型
   - smoke/e2e 脚本关键产出 marker
3. `verify.frontend.quick.gate` 已接入上述一致性 guard
4. contract evidence 新增 `grouped_pagination_contract.window_range_consistency`
5. contract evidence schema/guard/policy baseline 同步强化该指标
6. `contract_evidence_guard` 增加 grouped 字段布尔类型校验（类型+语义双重约束）

## 提交记录

1. `4702f67` docs(iteration): define v0.9-mini contract-governance goals
2. `a387725` test(e2e): upgrade grouped signature to v0.4 capability markers
3. `c414a8c` test(frontend-gate): add grouped contract consistency guard
4. `529bebe` feat(evidence): add grouped window-range consistency metric and policy
5. `feat(evidence)`: enforce grouped evidence boolean type checks

## 验证结果

1. `python3 scripts/verify/grouped_contract_consistency_guard.py`：PASS
2. `python3 scripts/verify/grouped_pagination_semantic_guard.py`：PASS
3. `python3 scripts/verify/grouped_pagination_semantic_drift_guard.py`：PASS
4. `python3 scripts/verify/grouped_rows_runtime_guard.py`：PASS
5. `python3 scripts/verify/contract_evidence_schema_guard.py`：PASS
6. `python3 scripts/verify/contract_evidence_guard.py`：PASS
7. `make verify.portal.tree_view_smoke.container`：PASS
8. `make verify.frontend.quick.gate`：PASS
9. `make verify.e2e.contract`：PASS
10. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

v0.9-mini 当前已达到可开 PR 并进入合并评审的状态。

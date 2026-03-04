# Odoo 原生承载差距迭代进展（v1.0-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_0`

## 已完成项

1. e2e grouped baseline 增加 `consistency_score` 能力汇总指标
2. `grouped_contract_consistency_guard` 同步校验 `consistency_score` 类型与范围
3. 新增 `grouped_drift_summary_guard`，聚合 fe_tree/e2e/evidence 三层 drift 信号
4. `verify.frontend.quick.gate` 接入 drift summary guard
5. contract evidence 新增 grouped consistency 汇总字段：
   - `consistency_signals_total`
   - `consistency_signals_passed`
   - `consistency_score`
   - `consistency_ok`
6. contract evidence schema/guard/policy baseline 同步强化上述字段
7. grouped 契约文档新增 Drift Diagnostics 排障路径
8. grouped drift summary guard 新增审计报告输出与基线策略文件
9. grouped drift summary 新增 schema guard，并接入 quick gate
10. grouped drift summary 新增 baseline guard（指标阈值治理）并接入 quick gate
11. phase11_1 evidence 纳入 grouped_drift_summary 分节（schema + guard + policy）

## 提交记录

1. `14da3ba` docs(iteration): define v1.0-mini evidence-closure goals
2. `ffeae8f` test(e2e): add grouped consistency_score and align consistency guard
3. `73a43f9` test(frontend-gate): add grouped drift summary guard aggregator
4. `cf89daa` feat(evidence): add grouped consistency summary score and policy checks
5. `test(frontend-gate)`: report-based grouped drift summary policy baseline
6. `test(frontend-gate)`: grouped drift summary schema guard in quick gate
7. `test(frontend-gate)`: grouped drift summary baseline guard in quick gate
8. `feat(evidence)`: include grouped drift summary section in phase11_1 evidence chain

## 验证结果

1. `python3 scripts/verify/grouped_drift_summary_guard.py`：PASS
2. `python3 scripts/verify/grouped_contract_consistency_guard.py`：PASS
3. `python3 scripts/verify/contract_evidence_schema_guard.py`：PASS
4. `python3 scripts/verify/contract_evidence_guard.py`：PASS
5. `make verify.portal.tree_view_smoke.container`：PASS
6. `make verify.e2e.contract`：PASS
7. `make verify.frontend.quick.gate`：PASS
8. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

v1.0-mini 当前达到可合并状态，grouped 契约在 smoke/e2e/evidence 三层闭环一致性已建立。

# Odoo 原生承载差距迭代进展（v2.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 已完成项

1. `export_evidence.py` 增加 `grouped_governance_trend_consistency` 分节，并接入 `--grouped-governance-trend-consistency-report` 参数
2. `contract_evidence_schema_guard` baseline 增加 `grouped_governance_trend_consistency` 分节键约束
3. `contract_evidence_guard` 完成职责去重：
   - 关闭重复 trend 细粒度规则默认开关
   - 新增 `grouped_governance_trend_consistency` 结论型约束
4. `contract_evidence_guard` baseline 同步到新的治理策略集合

## 验证结果

1. `python3 -m py_compile scripts/contract/export_evidence.py scripts/verify/contract_evidence_guard.py scripts/verify/grouped_governance_trend_consistency_guard.py scripts/verify/grouped_governance_trend_consistency_schema_guard.py scripts/verify/grouped_governance_trend_consistency_baseline_guard.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

v2.5-mini 已完成 evidence guard 与独立 trend consistency guard 的职责解耦，治理结构从“重复细粒度校验”收敛到“结论消费 + 独立报告审计”，达到可合并状态。

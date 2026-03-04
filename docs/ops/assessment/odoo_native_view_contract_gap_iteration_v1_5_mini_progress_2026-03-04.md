# Odoo 原生承载差距迭代进展（v1.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v1_2`

## 已完成项

1. `grouped_governance_brief_baseline_guard.py` 新增趋势策略化校验：
   - `has_previous=true` 且策略开启时，关键 delta 必须存在且类型正确
   - 可按策略开关限制 `grouped_e2e_case_count` / `grouped_rows_case_count` / `grouped_export_marker_hits` 回退
2. baseline policy 新增：
   - `require_trend_delta_when_previous`
   - `forbid_grouped_e2e_case_count_regression`
   - `forbid_grouped_rows_case_count_regression`
   - `forbid_grouped_export_marker_hits_regression`

## 验证结果

1. `make verify.grouped.governance.bundle`：PASS
2. `make verify.frontend.quick.gate`：PASS
3. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

v1.5-mini 达到可合并状态，grouped governance brief 的 trend 治理由“隐式校验”升级为“可配置强约束”。

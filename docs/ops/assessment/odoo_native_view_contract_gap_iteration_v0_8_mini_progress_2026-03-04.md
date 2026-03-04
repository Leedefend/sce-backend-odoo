# Odoo 原生承载差距迭代进展（v0.8-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v0_8`

## 完成项

1. grouped rows 契约新增 `page_window.{start,end}`，保留 `page_range_start/page_range_end` 兼容字段
2. 前端 `ActionView/ListPage` 优先消费 `page_window`，缺失时回退旧字段与本地推导
3. tree smoke 与 grouped signature 基线新增 `page_window` 能力断言
4. grouped runtime guard / semantic drift guard 增加 `page_window` 链路与漂移校验
5. contract evidence 导出新增 `supports_page_window`
6. contract evidence schema/evidence guard 增加 `supports_page_window` 强约束
7. grouped pagination 语义文档补齐并接入 `docs/contract/README.md`
8. grouped semantic summary 增加 `page_window` 与 `range` 一致性语义，并纳入 drift guard

## 提交记录

1. `804d6ec` docs(iteration): define v0.8-mini contract capability goals
2. `207ce56` feat(grouped-pagination): add page_window contract and frontend consumption
3. `9888685` test(grouped-pagination): guard page_window contract in smoke and runtime checks
4. `c42f0a0` feat(evidence): enforce grouped page_window support in contract evidence
5. `bde463e` test(grouped-pagination): require page_window in semantic guard
6. `ab21bbd` docs(contract): add grouped pagination contract semantics guide
7. `9ed95cd` test(grouped-pagination): enforce page_window-range consistency semantics

## 验证结果

1. `python3 scripts/verify/grouped_rows_runtime_guard.py`：PASS
2. `python3 scripts/verify/grouped_pagination_semantic_guard.py`：PASS
3. `python3 scripts/verify/grouped_pagination_semantic_drift_guard.py`：PASS
4. `python3 scripts/verify/contract_evidence_schema_guard.py`：PASS
5. `python3 scripts/verify/contract_evidence_guard.py`：PASS
6. `make verify.portal.tree_view_smoke.container`：PASS
7. `make verify.frontend.quick.gate`：PASS
8. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

v0.8-mini 目标已达到“可合并”状态：契约能力、验证链路、证据导出与语义文档同步完成。

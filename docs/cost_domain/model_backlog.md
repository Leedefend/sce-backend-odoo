# 模型 Backlog（Phase 0 基线版本）
版本：v1.0  
状态：已对齐蓝图，可作为后续 issue 的引用基线  
模块：smart_construction_core  
标签：phase-0, doc, backend/model, p0

---

# 待实现/重构模型 Backlog（基于蓝图 & P0-01）

标签：phase-0, doc, backend/model, p0  
模块：smart_construction_core

说明：每个模型包含用途+关键外键+关键金额字段，供后续阶段开发 issue 引用。

---

## project.budget / project.budget.line
- 用途：项目预算版本，定义目标收入/成本，作为预算基线与对比源。
- 关键外键：project_id, (line) boq_line_id。
- 关键金额：amount_cost_target, amount_revenue_target；(line) budget_amount, budget_qty, budget_price。

## project.contract / project.contract.line（收入/分包/采购统一）
- 用途：承诺层合同行（收入/成本/采购），决定合同量价与承诺成本/收入。
- 关键外键：project_id, partner_id; (line) boq_line_id, wbs_id。
- 关键金额：amount_total；(line) contract_amount, contract_qty, contract_price。

## project.change.order / project.change.order.line
- 用途：变更/索赔，调整合同量价，形成动态合同价/结算依据。
- 关键外键：project_id; (line) boq_line_id, wbs_id。
- 关键金额：amount_change, qty_change, price_change。

## sc.work.visa / sc.work.visa.line
- 用途：现场签证（合同外/零星工作），增加合同价款或成本。
- 关键外键：project_id; (line) boq_line_id, wbs_id。
- 关键金额：amount (line.amount), qty, price; visa 总额汇总到头。

## sc.settlement / sc.settlement.line
- 用途：收入/成本结算终局价，覆盖合同+变更+签证+计量，形成审定价。
- 关键外键：project_id; (line) boq_line_id, wbs_id。
- 关键金额：amount_contract, amount_change, amount_progress, amount_final, audit_deduction。

## project.progress.entry（计量批次头） + project.progress.line（计量行）
- 用途：产值计量批次（头）与逐清单/WBS 的本期/累计计量（行），驱动产值、进度、收款。
- 关键外键：project_id; (line) boq_line_id, wbs_id, entry_id。
- 关键金额：amount_period, amount_cumulative; (line) amount_period, amount_cumulative; qty_period, qty_cumulative。

TODO: 在 Phase 1 中创建 model.py / views / access / compute。

# Smart Construction 2.0 鈥?Six Center Blueprint (v1.0)

This blueprint locks down the target architecture for the 鈥滃叚涓績 + 骞冲彴鈥?middle-platform. Every new capability must align with these domain boundaries, models, and menus.

---

## 1. Global ERD Snapshot

```
[Data Center]
  project.dictionary(type, code, name, ...)
  project.cost.code(code, name, cost_type, parent_id, ...)
  product.category(...)
  res.partner(...)
        鈹?        鈻?[Project Center]
  project.project(id, name, company_id, ...)
        鈹?
        鈻?  project.wbs(id, project_id, parent_id, ...)
        鈹?
        鈻?  project.task(id, project_id, wbs_id, ...)

[Contract Center]
  project.contract(id, project_id, partner_id, ...)
        鈹?
        鈻?  contract.line(id, contract_id, wbs_id, boq_code, ...)

[Cost Control Center]
  project.budget(id, project_id, contract_id, version, is_active, ...)
        鈹?
        鈻?  project.budget.boq.line(id, budget_id, wbs_id, qty_bidded, price_bidded, ...)
        鈹?
        鈻?  project.budget.boq.alloc(id, boq_line_id, cost_code_id, budget_amount, ...)

  project.progress(id, project_id, wbs_id, date, qty_period, qty_cumulative, ...)
  project.cost.ledger(id, project_id, wbs_id, cost_code_id, date, qty, amount, source_model, ...)

[Material Center]
  sc.material.request(id, project_id, wbs_id, ...)
        鈹?        鈻?  sc.material.request.line(id, request_id, product_id, qty, ...)
        鈹?        鈻?  project.material.plan(id, project_id, ...)
        鈹?        鈻?  purchase.order(id, project_id, ...)
        鈹?        鈻?  stock.picking(id, project_id, ...)
        鈹?        鈻?  stock.move(id, picking_id, project_id, wbs_id, cost_code_id, quantity_done, ...)

[Finance Center]
  payment.request(id, project_id, contract_id, amount, ...)
        鈹?        鈻?  account.payment(id, partner_id, amount, ...)
        鈹?        鈻?  account.move(id, move_type, project_id?, ...)
```

Key principles:

- Every business object carries `project_id` and (when relevant) `wbs_id` / `cost_code_id` for cross-domain analytics.
- Actual costs flow into `project.cost.ledger`; budget allocations stay in `project.budget.boq.alloc` for direct comparisons.
- Dictionaries in the Data Center are the single source of truth for selectable values across all domains.

---

## 2. Center-Level Model Notes

### 2.1 Project Center

- **project.project** 鈥?master data (company, managers, dictionary-driven attributes).
- **project.wbs** 鈥?hierarchical breakdown per project; optional cost-code linkage.
- **project.task** 鈥?execution tasks referencing WBS (can reuse `project.task`).

### 2.2 Contract Center

- **project.contract** 鈥?every contract (main, subcontract, supply) tied to a project.
- **project.contract.line** 鈥?BoQ lines bound to WBS; basis for measurement/settlement.
- Optional: change orders, milestones, receivable/payable plans.

### 2.3 Cost Control Center

- **project.budget** 鈥?versioned budgets (`origin_budget_id`, `is_active`, version codes).
- **project.budget.boq.line** 鈥?detailed BoQ entries with target qty/price.
- **project.budget.boq.alloc** 鈥?BoQ-to-cost-code splits with ratios & amounts.
- **project.progress** 鈥?progress measurement entries (feed revenue recognition).
- **project.cost.ledger** 鈥?fact table for costs (project/wbs/cost_code/date/qty/amount/source).

### 2.4 Material Center

- **sc.material.request** / **sc.material.request.line** 鈥?site demand capture plus AI hints.
- **project.material.plan** 鈥?consolidated plan from requests.
- **purchase.order**, **stock.picking**, **stock.move** 鈥?extended with project/WBS/cost codes.
- Validated stock moves auto-write to `project.cost.ledger`.

### 2.5 Finance Center

- **payment.request** 鈥?approval workflow for outgoing/incoming payments.
- **account.payment** & **account.move** 鈥?financial documents extended with project context.
- Future additions: cash-flow plans, profitability dashboards, invoice-to-budget reconciliation.

### 2.6 Data Center

- **project.dictionary** 鈥?typed dictionaries (project types, material scenes, etc.).
- **project.cost.code** 鈥?cost-code tree (labor/material/subcontract/machine/fee/tax).
- Supporting masters: `product.category`, `uom.uom`, `res.partner` classifications, WBS templates.

---

## 3. Menu Blueprint

Top navigation:

```
椤圭洰涓績 | 鍚堝悓涓績 | 鎴愭帶涓績 | 鐗╄祫涓績 | 璐㈠姟涓績 | 鏁版嵁涓績 | 閰嶇疆
```

Center submenus (current + planned):

- **椤圭洰涓績**
  - 椤圭洰鍒楄〃 (`project.project`)
  - WBS/鍒嗛儴鍒嗛」 (`project.wbs`)
  - 椤圭洰浠诲姟 / 宸ョ▼璧勬枡 / AI 椤圭洰鍒嗘瀽鏃ュ織
- **鍚堝悓涓績**
  - 鍚堝悓鍒楄〃 (`project.contract`)
  - 鍚堝悓琛?(`project.contract.line`)
  - 鍙樻洿/绛捐瘉銆佹敹娆捐鍒掋€佷粯娆捐鍒掞紙杩唬鎸佺画锛?- **鎴愭帶涓績**
  - 鎴愭湰鎺у埗浠〃鐩橈紙dashboard / client action锛?  - 椤圭洰棰勭畻 (`project.budget`)
  - 棰勭畻娓呭崟鍒嗘憡 (`project.budget.boq.alloc`)
  - 杩涘害璁￠噺 (`project.progress`)
  - 鎴愭湰鍙拌处 (`project.cost.ledger`)
  - 鎴愭湰/鍒╂鼎鎶ヨ〃 (`project.cost.compare`, `project.profit.compare`)
- **鐗╄祫涓績**
  - 鐗╄祫闇€姹傚崟 (`sc.material.request`)
  - 鐗╄祫璁″垝 (`project.material.plan`)
  - 閲囪喘璁㈠崟 (`purchase.order`)
  - 鍏ュ簱/鍑哄簱 (`stock.picking`)
  - 鐗╄祫鍙拌处銆佷緵搴斿晢绠＄悊
- **璐㈠姟涓績**
  - 璐㈠姟涓績涓诲垪琛?(`account.move` filtered to invoices)
  - 浠樻/鏀舵鐢宠 (`payment.request`)
  - 鏀朵粯娆惧崟 (`account.payment`)
  - 椤圭洰鏀舵敮鎶ヨ〃銆佽祫閲戣鍒?- **鏁版嵁涓績**
  - 涓氬姟瀛楀吀 (`project.dictionary`)
  - 鎴愭湰绉戠洰 (`project.cost.code`)
  - 鐗╄祫绫诲埆 (`product.category`)
  - 渚涘簲鍟?瀹㈡埛瀛楀吀銆乄BS 妯℃澘銆佽鍒欓厤缃?- **閰嶇疆**
  - 绯荤粺鎶€鏈缃€佸畨鍏ㄣ€佸弬鏁扮鐞嗐€?
---

## 4. Dependency Map

```
Data Center 鈹€鈹?             鈹溾攢 Project Center 鈹€鈹攢 Contract Center 鈹€鈹?             鈹?                 鈹?                  鈹溾攢 Finance Center
             鈹?                 鈹斺攢 Cost Control 鈹€鈹€鈹€鈹€鈹?             鈹斺攢 Material Center 鈹€鈹?```

- All centers consume dictionaries/cost codes from the Data Center.
- Material executions feed actual costs into Cost Control; contracts bridge budgets and finance; finance confirms cash flow.
- Project Center is the spine: every major record ultimately links to `project.project`.

---

## 5. Implementation Guardrails

1. **Model placement** 鈥?each new model belongs to exactly one center; cross-center relations rely on `project_id`, `wbs_id`, `cost_code_id`, and explicit foreign keys rather than ad-hoc Many2many links.
2. **Menu governance** 鈥?every UI entry sits under the correct center subtree; avoid orphan menus.
3. **SQL-first analytics** 鈥?cost/profit/trend reports rely on SQL views + readonly models for accuracy.
4. **Version discipline** 鈥?budgets, contracts, dictionaries maintain explicit version/is_active flags.
5. **Doc cadence** 鈥?update this blueprint whenever a new center-level capability ships to keep architecture intent visible.

---

_Maintainer: Smart Construction Core Team_  
_Last updated: 2025-11-26_

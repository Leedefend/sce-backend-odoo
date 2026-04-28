# 应收应付报表（项目）抵扣税额 Batch-F

## 批次边界

- Layer Target：Domain Projection
- Module：`addons/smart_construction_core`
- Reason：旧库“应收应付报表（项目）”剩余字段中，抵扣税额来源明确为 `C_JXXP_DKDJ_CB.DKSE`，需要先补事实载体，再进入汇总报表。

## 本批目标

- 新增 `sc.legacy.tax.deduction.fact` 历史抵扣税额事实模型。
- 从旧库 `C_JXXP_DKDJ_CB + C_JXXP_DKDJ_New` 导入有效抵扣明细到模拟生产库。
- 在 `sc.ar.ap.project.summary` 中新增：
  - 抵扣税额
  - 抵扣比例

## 事实判断

旧库抵扣明细：

- `C_JXXP_DKDJ_CB`：4990 行
- 全量 `DKSE`：59386493.57
- 主表 `DEL=0`：51160562.08
- 主表 `DEL IS NULL`：5075749.26
- 本批有效口径 `ISNULL(DEL, 0)=0`：4915 行，56236311.34

新系统现状：

- `sc.legacy.invoice.tax.fact` 未承载 `C_JXXP_DKDJ_CB`。
- `sc.receipt.income.deducted_tax_amount` 当前合计为 0。
- 因此不能复用现有发票税额事实或收款字段，必须单独资产化抵扣税额事实。

## 口径说明

抵扣事实来源：

- `C_JXXP_DKDJ_CB.DKSE` -> 抵扣税额
- `C_JXXP_DKDJ_CB.D_SCBSJS_DKFJS` -> 抵扣附加税
- `C_JXXP_DKDJ_New.XMID` -> 项目锚点
- `C_JXXP_DKDJ_CB.KPDWID/KPDW/KPDWXYDM` -> 往来单位锚点

过滤条件：

- `ISNULL(C_JXXP_DKDJ_New.DEL, 0)=0`

报表计算：

- 抵扣税额 = 同项目同往来单位有效抵扣明细 `DKSE` 合计
- 抵扣比例 = 抵扣税额 / 销项税额；销项税额为 0 时返回 0

## 交付结果

- 模型：`sc.legacy.tax.deduction.fact`
- 内部菜单：历史财务事实（内部）/ 历史抵扣税额
- 脚本：
  - `scripts/migration/fresh_db_legacy_tax_deduction_replay_adapter.py`
  - `scripts/migration/fresh_db_legacy_tax_deduction_replay_write.py`
- 报表：`sc.ar.ap.project.summary` 新增抵扣税额、抵扣比例

## 验证结果

- `python3 -m py_compile ...`：PASS
- XML parse：PASS
- `CSV ir.model.access duplicate id check`：PASS，336 行，无重复 id
- `ENV=test ENV_FILE=.env.prod.sim CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_prod_sim make mod.upgrade`：PASS
- `python3 scripts/migration/fresh_db_legacy_tax_deduction_replay_adapter.py`：PASS，payload 4915 行
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim MIGRATION_REPLAY_DB_ALLOWLIST=sc_prod_sim ... make odoo.shell.exec < scripts/migration/fresh_db_legacy_tax_deduction_replay_write.py`：PASS，最终已存在 4915 行
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec`：
  - `fact_count=4915`
  - `fact_project_count=4915`
  - `fact_partner_bound_count=4872`
  - `fact_deduction_tax_amount=56236311.34`
  - `summary_count=11167`
  - `summary_deduction_rows=1874`
  - `summary_deduction_tax_amount=56236311.34`
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make verify.restricted`：SKIP，当前 Makefile 无该 target

## 风险

- 抵扣附加税已进入事实模型，但本批未挂入应收应付报表；旧报表存在 `DKDJFJS` 字段，后续可在确认展示需要后补充。
- 43 行抵扣事实未匹配到新系统 `res.partner`，但仍以历史往来单位名称进入汇总，避免丢失抵扣事实。
- 自筹退回和实际可用余额仍未纳入，应继续按事实载体补齐。

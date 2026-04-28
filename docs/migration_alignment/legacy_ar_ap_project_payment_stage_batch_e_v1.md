# 应收应付报表（项目）付款字段 Batch-E

## 批次边界

- Layer Target：Domain Projection
- Module：`addons/smart_construction_core`
- Reason：旧库“应收应付报表（项目）”的付款字段已经找到可对齐的新系统资金台账事实，可以在 Batch-D 第一阶段报表上继续补齐付款相关指标。

## 本批目标

在 `sc.ar.ap.project.summary` 中新增付款侧三项指标：

- 已付款
- 未付款
- 付款超票

## 事实判断

旧库事实：

- `T_FK_Supplier` 总量：13629 行，付款金额合计 2152297118.18
- `T_FK_Supplier` 非删除口径：13573 行，付款金额合计 2148050360.23

新系统事实：

- `payment.ledger`：12194 行，付款金额合计 2087094963.14
- `sc.payment.execution`：1192 行，实付金额合计 58281465.15
- `sc.treasury.ledger` 支出口径：12992 行，金额合计 2147431936.05

判断：

- `sc.payment.execution` 只承载付款执行和历史残余，不足以代表旧库全量供应商付款。
- `payment.ledger` 是付款申请生成的运行态付款台账，金额低于旧库非删除付款口径。
- `sc.treasury.ledger` 的支出流水同时具备项目、往来单位、金额、状态，且金额最接近旧库非删除付款口径，因此作为本批付款事实来源。

## 口径说明

数据来源：

- `sc.treasury.ledger`

过滤条件：

- `direction = out`
- `state = posted`

维度：

- 项目
- 往来单位

计算字段：

- 已付款 = 同项目同往来单位支出资金流水合计
- 未付款 = max(已收供应商发票 - 已付款, 0)
- 付款超票 = max(已付款 - 已收供应商发票, 0)

## 暂缓字段

- 抵扣税额：仍需确认抵扣登记事实与新系统税务事实的完整映射。
- 自筹收入/退回/未退：仍需补 `C_JFHKLR_TH_ZCDF*` 对应事实承载。
- 实际可用余额：应由项目资金汇总能力承载，不在本批临时硬算。

## 验证结果

- `python3 -m py_compile addons/smart_construction_core/models/projection/ar_ap_project_summary.py`：PASS
- `python3 stdlib XML parse addons/smart_construction_core/views/projection/ar_ap_project_summary_views.xml`：PASS
- `ENV=test ENV_FILE=.env.prod.sim CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_prod_sim make mod.upgrade`：PASS
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec`：`summary_count=11076`，菜单和 action 均存在
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make verify.restricted`：SKIP，当前 Makefile 无该 target

汇总金额：

- 已付款：2147431936.05
- 未付款：623379540.51
- 付款超票：128381363.35

## 风险

本批使用资金台账作为付款事实来源，适合业务连续使用和项目往来单位维度统计。它与旧库 `T_FK_Supplier` 非删除口径存在约 618424.18 的差额，需要后续通过旧系统删除标记、负数/退款、特殊付款类型或迁移过滤规则做差异解释。

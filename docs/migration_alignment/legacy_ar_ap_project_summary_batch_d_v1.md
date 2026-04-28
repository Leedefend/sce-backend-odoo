# 应收应付报表（项目）第一阶段 Batch-D

## 批次边界

- Layer Target：Domain Projection
- Module：`addons/smart_construction_core`
- Reason：基于 Batch-C 已确认的新系统事实覆盖率，先承载旧库“应收应付报表（项目）”中可可靠计算的第一阶段字段。

## 本批目标

新增 `sc.ar.ap.project.summary` SQL 只读聚合视图，按项目和往来单位汇总应收应付第一阶段指标，并挂入报表中心。

## 已实现字段

- 收入合同金额
- 已开票
- 已收款
- 未收款
- 已开票未收款
- 已收款未开票
- 应付合同金额
- 已收供应商发票
- 销项税额
- 进项税额

## 暂缓字段

- 已付款、未付款、付款超票：旧库 `T_FK_Supplier` 全量付款尚未完整映射到新系统。
- 抵扣税额：抵扣登记事实覆盖需单独确认。
- 自筹收入/退回/未退：旧库 `C_JFHKLR_TH_ZCDF*` 尚无明确新模型。
- 实际可用余额：依赖旧库 `View_Select_XMCKXX_BS`，应由项目资金汇总能力承载。

## 口径说明

维度：

- 项目
- 往来单位

往来单位键：

- 优先使用 `partner_id`
- 无 `partner_id` 但有 `legacy_partner_name` 的历史发票，先按单位名称精确匹配新系统 `res.partner`，匹配成功后并入同一往来单位维度
- 仍无法匹配 `res.partner` 的历史发票使用 `legacy_partner_name` 文本兜底，避免丢失旧库事实

数据来源：

- `construction.contract`：收入/支出合同
- `sc.receipt.income`：收款
- `sc.invoice.registration`：销项/进项发票和税额

## 验证结果

- `python3 -m py_compile addons/smart_construction_core/models/projection/ar_ap_project_summary.py`：PASS
- `python3 stdlib XML parse addons/smart_construction_core/views/projection/ar_ap_project_summary_views.xml`：PASS
- `CSV ir.model.access duplicate id check`：PASS，332 行，无重复 id
- `ENV=test ENV_FILE=.env.prod.sim CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_prod_sim make mod.upgrade`：PASS
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec`：`summary_count=10834`，`partner_bound=10381`，`partner_unbound=453`，菜单和 action 均存在

汇总金额：

- 收入合同金额：3142399070.99
- 已开票：47602317362.22
- 已收款：480379794.04
- 未收款：2662019276.95
- 已开票未收款：47472912552.33
- 已收款未开票：350974984.15
- 应付合同金额：2402859650.36
- 已收供应商发票：2642430113.21
- 销项税额：177414371.67
- 进项税额：114112494.93

## 交付结果

- 模型：`sc.ar.ap.project.summary`
- 菜单：报表中心 / 应收应付报表（项目）
- 视图：tree、pivot、graph
- 权限：财务能力组和合同能力组只读

## 风险

当前第一阶段报表不是旧库 27 字段完整复刻，而是可用字段优先落地。暂缓字段必须等事实补齐后再扩展，否则会输出错误数字。

# FE-AUDIT-02 角色语义与核心旅程深度审计

## 结论

本轮补充审计确认：115 个导航叶节点的 1440 路由可达性不能等同于业务可用性。J01–J08 均已明确记录为 `BLOCKED`，未将 `NOT_ASSESSED` 计入通过；因此本报告不宣称成熟产品审计通过。

## 已观察事实

- 四角色可登录，固定验收库为 `sc_frontend_acceptance`。
- 现有表面清单包含 115 个叶节点。
- 115 个页面标题均为“业务动作 - 智能施工企业管理平台”，属于标题同质化产品问题，不能只记录 record 标题回退。
- project member 的导航矩阵包含财务、税务、人事、薪资、结算、付款、证照等敏感域；本轮将其标为 `NEEDS_PRODUCT_DECISION`，不能仅凭 HTTP 200 判定权限合理。
- 应用层分类和核心旅程需要逐步浏览器证据；当前表面报告不足以证明列表数据、字段、写按钮或权限状态。

## J01–J08

J01 登录与初始化、J02 公司切换、J03 项目成员旅程、J04 合同、J05 结算、J06 付款申请与执行、J07 我的工作、J08 表单观察均记录为 `BLOCKED`，原因是本轮尚未完成逐步业务操作链。禁止将此状态解释为通过。

## 响应式

1280×800 与 390×844 的核心旅程尚未执行；此前每角色单页采样只能作为代表性证据，不能作为核心旅程响应式结论。

## 证据

- `artifacts/frontend-audit-02/application-surface-classification.json`
- `artifacts/frontend-audit-02/role-visibility-matrix.json`
- `artifacts/frontend-audit-02/journeys.json`
- `artifacts/frontend-audit-02/title-statistics.json`
- `artifacts/frontend-audit-02/responsive-report.json`

本任务不修改产品代码、后端、权限、fixture 或数据库。

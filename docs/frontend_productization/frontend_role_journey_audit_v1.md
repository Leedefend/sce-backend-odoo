# FE-AUDIT-02 角色语义与核心旅程深度审计

## 结论

本轮补充审计确认：115 个导航叶节点的 1440 路由可达性不能等同于业务可用性。J01–J08 已通过真实只读步骤执行并得到明确状态；本轮结果为 J01/J02/J04/J05/J06 `PASS`，J03 `FAIL`，J07/J08 `BLOCKED`。因此本报告不宣称成熟产品审计通过。

## 已观察事实

- 四角色可登录，固定验收库为 `sc_frontend_acceptance`。
- 现有表面清单包含 115 个叶节点。
- 115 个页面标题均为“业务动作 - 智能施工企业管理平台”，属于标题同质化产品问题，不能只记录 record 标题回退。
- project member 的导航矩阵包含财务、税务、人事、薪资、结算、付款、证照等敏感域；本轮将其标为 `NEEDS_PRODUCT_DECISION`，不能仅凭 HTTP 200 判定权限合理。
- J03 实测项目成员可以打开付款申请入口，但页面显示 `当前角色：owner`、`records=0` 和“可读降级渲染”，没有明确权限拒绝；这是 P1 角色语义/应用层状态问题，不可归类为正常空数据。
- J07/J08 当前没有可重复的只读待办/表单入口，记录为 BLOCKED，而非通过。

## J01–J08

J01 登录与初始化、J02 公司切换、J03 项目成员旅程、J04 合同、J05 结算、J06 付款申请与执行、J07 我的工作、J08 表单观察均已执行或明确尝试。详细步骤见 `artifacts/frontend-audit-02/core-journeys.json`。

## 响应式

1280×800 与 390×844 的核心旅程尚未执行；此前每角色单页采样只能作为代表性证据，不能作为核心旅程响应式结论。

## 证据

- `artifacts/frontend-audit-02/application-surface-classification.json`
- `artifacts/frontend-audit-02/role-visibility-matrix.json`
- `artifacts/frontend-audit-02/journeys.json`
- `artifacts/frontend-audit-02/title-statistics.json`
- `artifacts/frontend-audit-02/responsive-report.json`

本任务不修改产品代码、后端、权限、fixture 或数据库。

## FE-B02 修复验收

`fix/frontend-role-trust-boundary` 使用同一固定验收库重新执行角色可信边界旅程，权威证据为 `artifacts/playwright/frontend-productization-fixture/report.json`：

- J02 `PASS`：finance 在 FE Company A 看到 `FE-A-PR-001/002` 与 `FE-B-PR-001`；切换 FE Company B 后仅看到 `FE-C-PR-001`；切回 A 后原三条恢复。两次 `system.init` 请求分别携带 company_id 3 与 2，列表未复用上一公司缓存。
- J03 `PASS`：顶部角色为“项目成员”；release/delivery 权威导航不含财务、税务、人事、薪资、付款、结算管理入口；Project A 可见，Project B/C 不可见。
- 敏感 action 876、menu 606 与 Project A payment record 5 直达均在业务组件挂载前进入公共无权访问状态；Project C payment record 8 无导航上下文直达由 record rule 返回 HTTP 403。
- 拒绝响应与页面未出现 fixture 记录名称、金额或公司信息；finance/member 在预期拒绝步骤前均无 console error 或 pageerror。
- 同一浏览器 logout 后依次登录 PM、owner，角色面均重新初始化，没有复用项目成员导航；finance 的付款和结算入口保持存在。

旧 J03 `FAIL` 结论由上述 FE-B02 证据关闭；J07/J08 与标题产品化不属于本分支。

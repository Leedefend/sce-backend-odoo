# 前端交付 readiness v1

## 当前结论

首批交付范围冻结为 70 个权威导航叶节点：finance 42、project member 9、PM 14、owner 5。70/70 在 1440×900 可达且页面身份通过；J02–J11 已分别覆盖公司/角色隔离、权限拒绝、资金关系链、合法操作、My Work、表单审批、错误恢复、390px 键盘路径和异步乱序。该结论只适用于 `sc_frontend_acceptance` 的公司 A/B、Project A 和冻结角色范围，不扩张为全业务或生产规模承诺。

## 可交付能力

- finance：My Work、合同—结算—付款详情、付款申请新建/保存/提交、公司 A/B 隔离和结果回看有真实证据。
- project member：仅 Project A 范围、敏感导航排除、敏感 action/menu/record 明确拒绝且无标题/金额泄露。
- PM/owner：冻结的 14/5 个合法叶节点保持可达；PM 以正式权限验证 Project A—合同—结算详情，owner 不扩张职责。
- executive：仅作为正式付款审批旅程角色，提交后审批和待办迁移有真实证据，不计入 70 个导航分母。

## 不宜直接承诺的能力

- My Work 扩展到付款申请以外的对象。
- finance 获得 Project A 主表 action 权限，或 project member 获得财务事实。
- 没有可靠审计参与证据时展示“最近完成”。
- 生产数据规模、弱网和非验收硬件上的绝对性能保证。

## 首批用户前置条件

1. 使用冻结 fixture 和正式角色运行 J02–J11，不跳过权限与错误检查。
2. 以 `artifacts/frontend-delivery-hardening/` 中的性能、无障碍、响应式和错误恢复报告作为试点判定输入。
3. 生产发布前另行验证真实部署资源、数据库规模、备份恢复和监控，不把本地验收数值外推为生产 SLA。

## FE-B06 交付证据

- 代表表面：18 个表面在 1440×900、1280×800、768×1024、390×844 共 72 个组合，页面级横向溢出为 0。
- 无障碍：`@axe-core/playwright@4.10.2` 扫描 18 个桌面表面，critical/serious 阻断为 0；J10 验证键盘登录、My Work、详情、确认框焦点进入/约束/返回。
- 恢复：真实记录读取分别注入网络断开、409 和 401；Retry、获取最新数据和安全登录回退通过，登录 URL 不携带旧敏感详情 redirect。
- 异步隔离：请求 epoch 阻止迟到的公司、角色和详情响应覆盖当前页面；J11 最终只显示最后选择的公司 B，logout 后 project member 不出现 finance 数据。
- 性能：固定验收环境每场景保留 5 个原始样本、中位数和最慢值；登录 1382/1612ms、My Work 942/947ms、付款详情 1970/2051ms、结算详情 1965/1989ms、付款执行 1463/1466ms、表单 1411/1418ms、公司切换 849/1516ms（中位数/最慢）。未达绝对中位数的详情/表单相对同机 main 基线均改善，逐指标门禁通过；完整原始样本在 `artifacts/frontend-delivery-hardening/performance.json`。

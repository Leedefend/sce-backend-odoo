# Daily Payment E2E Probe v1

## 目的

验证无合同、无结算单的企业日常付款是否可以在新系统完整办理：提交、审批通过、登记付款台账、办结。

## 结果

状态：`FAIL`

失败点不是业务载体缺失，而是角色事实缺失：

- 可用业务载体存在：`draft no contract no settlement with project/partner = 10429`
- 前 2000 条中满足项目生命周期、资金基线、可读权限的载体：`1907`
- 财务用户：`11`
- 财务经理：`11`
- 审批人组 `smart_core.group_smart_core_finance_approver` 用户：`0`
- 同时具备提交、审批、办结权限的用户：`0`

## 判断

日常付款业务事实已经具备：

- 真实导入项目载体存在
- 真实往来单位存在
- 项目资金条件可满足
- 财务用户可读项目

当前无法完成端到端办理探针，是因为运行库缺少审批角色事实，导致审批动作无法用真实权限路径执行。

## 架构定位

- Layer Target: Business Fact Verification
- Module: daily no-contract payment lifecycle
- Backend sub-layer: business-fact layer

这不是前端消费问题，也不是页面交互问题。下一步应补齐运行库中的审批角色/用户事实，或先筛查审批角色初始化链路。

## 下一步

开启 dedicated role-fact screen：

- 核实 `smart_core.group_smart_core_finance_approver` 是否已安装、可分配。
- 核实客户运行库中审批用户/业务管理员是否应继承该组。
- 在不改 ACL、不改 record rule 的前提下，判断是种子数据缺口、角色矩阵缺口，还是迁移用户角色同步缺口。

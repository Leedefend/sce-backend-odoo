# 原生菜单/动作健康检查 v1

## 检查范围

- `addons/smart_construction_core/views/**/*.xml`
- `addons/smart_construction_core/actions/*.xml`
- `addons/smart_enterprise_base/views/*.xml`

## 检查结果（静态）

## 1) 菜单 action 悬挂引用

- `smart_construction_core`：菜单 action 总数 `61`，缺失引用 `0`。
- `smart_enterprise_base`：菜单 action 总数 `4`，缺失引用 `0`。

结论：**未发现菜单直连 action 的静态悬挂问题**。

## 2) 关键动作面

- `ir.actions.act_window`：项目、预算、成本、付款、结算、企业主数据入口均存在。
- `ir.actions.server`：审批相关动作链存在（材料计划、付款申请、字典中心入口等）。

## 3) 权限面快速核对

- 企业基座菜单动作当前绑定 `base.group_system`（管理员域）。
- 行业核心动作广泛绑定 `group_sc_cap_*` 能力组。

## 4) 风险观察

1. 动作数量较多（静态命中 >100），后续修改应坚持最小改动。
2. `security/action_groups_patch.xml` 后置加载，动作权限补丁链需与 ACL/rule 变更同步回归。

## 结论

- 原生菜单/动作在静态结构上健康。
- 下一步重点不是“补入口”，而是“修权限冲突 + 保障 smoke 可达”。


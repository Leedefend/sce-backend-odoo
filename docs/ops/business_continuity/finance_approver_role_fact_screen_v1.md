# Finance Approver Role Fact Screen v1

## 目的

定位日常付款端到端办理失败的审批角色事实缺口。

## 结论

`smart_core.group_smart_core_finance_approver` 已安装，但没有任何有效用户继承该组。

这不是付款业务载体问题，也不是旧数据缺失问题，而是权限语义没有对齐：

- 原生 Odoo 付款表单按钮使用 `smart_construction_core.group_sc_cap_finance_manager` 执行审批/完成。
- 自定义 intent 链路 `payment.request.approve` / `payment.request.done` 要求 `smart_core.group_smart_core_finance_approver`。
- 客户角色 `smart_construction_custom.group_sc_role_payment_manager` 只继承 `smart_construction_core.group_sc_cap_finance_manager`，没有继承 canonical finance approver。

## 运行库事实

| 角色/组 | 状态 |
| --- | ---: |
| `smart_core.group_smart_core_finance_approver` | exists |
| canonical approver effective active users | 0 |
| legacy `smart_core.group_sc_finance_approver` effective active users | 0 |
| `group_sc_cap_finance_user` effective active users | 11 |
| `group_sc_cap_finance_manager` effective active users | 11 |
| `group_sc_role_payment_manager` effective active users | 8 |

`group_sc_role_payment_manager` 当前继承：

- `smart_construction_core.group_sc_cap_finance_manager`

但没有继承：

- `smart_core.group_smart_core_finance_approver`
- `smart_core.group_sc_finance_approver`

## 受影响用户

财务经理存在但没有 canonical approver 的用户包括：

- `admin`
- `wutao`
- `duanyijun`
- `wennan`
- `lina`
- `jiangyijiao`
- `chenshuai`
- `shuiwujingbanren`
- `luomeng`
- `sc_fx_executive`
- `sc_fx_finance`

## 架构判断

- Layer Target: Business Authority Fact Screening
- Module: finance approver role facts
- Backend sub-layer: business-fact layer

下一步属于 authority-surface alignment，不是付款业务规则本身：

- 推荐方向：让客户付款审批角色或财务经理能力继承 canonical finance approver。
- 不推荐方向：把 intent required group 改回行业旧组，因为新代码已经明确以 `smart_core.group_smart_core_finance_approver` 为 canonical 审批权限。

## 风险边界

下一步若实施会触达 `security/**` 或角色矩阵，必须开启 dedicated high-risk permission-governance 批次，并显式授权。

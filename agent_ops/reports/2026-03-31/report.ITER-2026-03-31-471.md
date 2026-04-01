# ITER-2026-03-31-471

## Summary
- 审计了四川保盛 `business_admin` 的展示语义与运行态权限是否一致
- 结果为 `PASS`
- 结论：当前 `admin.sc_role_profile = owner` 属于现有单主角色模型下的受控展示残差，不是运行态权限错误

## Scope
- 本批仅做仓库与 runtime 治理审计
- 变更路径：
  - [report.ITER-2026-03-31-471.md](/mnt/e/sc-backend-odoo/agent_ops/reports/2026-03-31/report.ITER-2026-03-31-471.md)
  - [ITER-2026-03-31-471.json](/mnt/e/sc-backend-odoo/agent_ops/state/task_results/ITER-2026-03-31-471.json)
  - [delivery_context_switch_log_v1.md](/mnt/e/sc-backend-odoo/docs/ops/iterations/delivery_context_switch_log_v1.md)
- 不涉及：
  - `addons/**`
  - `frontend/**`
  - ACL / record rules / manifest

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-471.yaml` → `PASS`
- repository and runtime audit on `sc_odoo` → `PASS`

## Audit Facts

### 1. `sc_role_profile` 是单主角色字段，不承载 `business_admin`
- [res_users_role_profile.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/res_users_role_profile.py) 只定义四个可选主角色：
  - `owner`
  - `pm`
  - `finance`
  - `executive`
- `write/create` 时，`sc_role_profile` 只同步这些受管主角色组，不会同步 `group_sc_role_business_admin`
- 这说明 `business_admin` 在当前模型里不是 `sc_role_profile` 的一等枚举值

### 2. `business_admin` 是客户系统角色 overlay，而不是主角色枚举
- [security_policy.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/models/security_policy.py) 把客户系统角色映射成：
  - `管理员角色 -> group_sc_role_business_admin`
  - `通用角色 -> group_sc_role_owner`
- [role_matrix_groups.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/security/role_matrix_groups.xml) 中，`group_sc_role_business_admin` 直接承接 `group_sc_business_full`
- 因而 `business_admin` 的真实 authority 来源是 overlay 组，而不是 `sc_role_profile`

### 3. 当前客户数据本身就是“主角色 + overlay”混合建模
- [customer_users.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/data/customer_users.xml) 中：
  - `admin` 初始同时带 `group_sc_role_business_admin` 与 `group_sc_role_owner`
- [customer_user_authorization.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/data/customer_user_authorization.xml) 中：
  - `admin` 只补 `business_admin + owner` 组，不写 `sc_role_profile`
  - `duanyijun` / `wennan` 这类用户则是 `sc_role_profile = executive/finance` 再叠加 `business_admin`
- 这进一步证明 `business_admin` 被设计成附加治理通道，而不是主展示角色字段

### 4. 运行态权限已正确落到业务管理员通道
- `470` 已确认：
  - `business_admin / admin` 关键菜单与动作链全部可用
  - authority 来自 `group_sc_business_full`
  - 问题只剩 `sc_role_profile` 展示仍为 `owner`
- `461` 冻结矩阵也明确：
  - `owner` 是主角色基线
  - `business_admin` 是 overlay 名单

## Conclusion
- 当前 `admin.sc_role_profile = owner` 不构成模型错误，也不构成运行态权限错误
- 现有实现表达的是：
  - 主角色语义：`owner`
  - 叠加治理权限：`business_admin`
- 因此本批将该现象归类为“可解释的展示残差”，不是必须立即修复的 authority misalignment
- 若后续要对齐显示语义，必须新开一张窄实现批次，并先决定以下治理口径：
  - 是把 `business_admin` 升格为 `sc_role_profile` 新枚举
  - 还是保留单主角色字段，新增一个 overlay 展示字段

## Risk
- 结果：`PASS`
- 观察项：
  - 当前 UI 只显示主角色字段，容易弱化 `business_admin` overlay 的可见性
  - 但仓库与 runtime 证据一致表明这不是权限或契约错误

## Rollback
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-471.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-471.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 若当前目标仍是四川保盛首批交付闭环，下一步可继续更细粒度的业务流程验收
- 若产品更重视角色展示一致性，则应新开一张窄实现批次，先冻结 `business_admin` 的展示模型再改代码

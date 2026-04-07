# 项目组织落位与隔离骨架设计 v1

## 目标
- 将原生业务事实层从“结构存在”推进到“组织可落位 + 隔离可验证 + 访问边界可解释”。
- 前端保持通用契约消费者，不引入前端业务特判。

## 事实层组织骨架
- `project.project`：承载项目主责岗位事实（项目经理/技术/商务/成本/财务对接）。
- `project_member_ids`：承载项目成员事实（成员、岗位、部门、主责、有效期）。
- 项目可见基线：创建人 + 项目成员 + 主责岗位关联用户。

## outsider 样本语义（冻结）
- outsider 验证样本定义为“临时最小权限内部用户”，仅具备 `base.group_user`，不携带 `project` 或 `SC capability` 业务组。
- 禁止将 `outsider_seed` 作为默认 outsider 样本（其历史账号具备 `project.group_project_user` 与 `group_sc_cap_project_user`，会引入 project/task 可见性噪音）。
- fresh 证据脚本必须在运行期创建临时 outsider，并在验证后自动清理，以保证多 fresh 库复验可重复。

## company/project 隔离锚点（关键对象）
- 项目域：`project.project(company_id)`。
- 任务域：`project.task(company_id, project_id)`。
- 预算域：`project.budget(company_id, project_id)`。
- 成本域：`project.cost.ledger(company_id, project_id)`。
- 付款域：`payment.request(company_id, project_id)`、`payment.ledger(company_id, project_id)`。
- 结算域：`sc.settlement.order(company_id, project_id)`。

## 权限闭环策略（本轮）
- 本轮执行“锚点可验证 + 真实角色可办 + 全链路可达”。
- `ACL/record-rule` 文件改动属于高风险闸门，需专用授权任务，不在本轮直接改写。

## 门禁收敛
- 保留：运行可达、真实角色、关键对象可访问、关键流程可办。
- 暂停：继续扩展表面一致性类 smoke（从 stage_gate 主链移除）。

## 特权放行边界（当前）
- `base.group_system`
- `project.group_project_manager`
- `smart_construction_core.group_sc_super_admin`
- `smart_construction_core.group_sc_cap_project_manager`

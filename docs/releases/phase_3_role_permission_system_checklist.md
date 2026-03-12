# SCEMS v1.0 Phase 3：角色权限体系检查清单

## 1. 目标
建立 V1 固定角色的权限闭环，确保“看得到、进得去、做得了、拦得住”。

## 2. 角色范围（V1）
- 项目经理
- 项目成员
- 合同管理人员
- 财务协同人员
- 管理层查看
- 系统管理员

## 3. 必做项

### A. 模型权限（ACL）
- [x] 各角色关键模型读写权限已定义并可追踪
- [x] `project.project`、`construction.contract`、`project.cost`、`payment.request` 的最小权限集完成
- [x] 无角色出现“可写但无读”或“无必要权限”异常配置

### B. 记录规则（Record Rules）
- [x] 项目成员仅可见被分配/授权项目数据
- [x] 财务协同可见资金相关数据且不越权修改非财务对象
- [x] 管理层查看角色为只读视角

### C. Capability 与 Block 可见性
- [x] 核心 capability 按角色矩阵可控
- [x] `project.management` 的 7-block 可按角色做可见/只读控制
- [x] 未授权 capability 在 contract 中应被拒绝或降级

### D. 场景与路由权限
- [x] 主导航场景按角色显示一致
- [x] 无权限场景返回规范 reason_code（非空白页）
- [x] 深链访问（deep link）遵循同等权限策略

### E. 演示账号与证据
- [x] prod-like 角色账号齐备并可登录
- [x] 角色矩阵验证报告可复现
- [x] 关键权限校验产物可归档

## 4. 建议验证命令
- `make verify.role.capability_floor.prod_like`
- `make verify.role.capability_floor.prod_like.schema.guard`
- `make verify.role.management_viewer.readonly.guard`
- `make verify.role.project_member.unification.guard`
- `make verify.role.system_admin.minimum_permission_audit.guard`
- `make verify.role.acl.minimum_set.guard`
- `make verify.relation.access_policy.consistency.audit`
- `make verify.portal.role_scene_navigation_guard`
- `make verify.scene.contract.shape`
- `make verify.project.dashboard.role_runtime.guard`
- `make verify.scene.permission_reasoncode_deeplink.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.phase_next.evidence.bundle`

## 5. 交付产物
- 角色权限矩阵文档（建议：`docs/releases/role_permission_matrix_v1.md`）
- Phase 3 报告（建议：`artifacts/release/phase3_role_permission_system.md`）
- 关键 verify artifacts（role/capability/contract）

## 6. 退出条件
- 清单项全部打勾
- 主要角色链路验证通过（项目经理、财务协同、管理层查看）
- 执行看板 Phase 3 状态更新为 `DONE`

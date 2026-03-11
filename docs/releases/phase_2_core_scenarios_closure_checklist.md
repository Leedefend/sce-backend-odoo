# SCEMS v1.0 Phase 2：核心场景闭环检查清单

## 1. 目标
完成 V1 四大核心场景的最小可用闭环，确保“可演示、可验证、可交付”。

## 2. 场景范围
- `my_work.workspace`
- `projects.ledger`
- `project.management`
- 业务工作台（`contracts.workspace` / `cost.analysis` / `finance.workspace`）

## 3. 必做项

### A. 场景可达性
- [ ] 主导航可进入四大核心场景
- [ ] `projects.ledger` 可跳转到 `project.management`
- [ ] 各场景默认路由与回退路由可用

### B. 场景契约完整性
- [ ] `my_work.workspace` 包含：待办、我的项目、快捷入口、风险摘要
- [ ] `projects.ledger` 包含：列表、筛选、搜索、进入控制台动作
- [ ] `project.management` 包含 7 个 block：Header/Metrics/Progress/Contract/Cost/Finance/Risk
- [ ] 业务工作台可见合同/成本/资金核心入口

### C. 角色与可见性
- [ ] 项目经理角色下 4 个场景均可访问
- [ ] 财务协同角色下资金相关场景可访问
- [ ] 管理层查看角色下控制台指标区块可见

### D. 运行稳定性
- [ ] 连续两次 `system.init` 场景结构稳定（无随机漂移）
- [ ] `ui.contract` 在 user/hud 模式均可返回契约
- [ ] 页面关键入口点击后无空白页/无 action unresolved

## 4. 建议验证命令
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`

## 5. 交付产物
- 场景闭环报告（建议：`artifacts/release/phase2_core_scenarios_closure.md`）
- 关键验证产物（backend artifacts + scene governance artifacts）

## 6. 退出条件
- 本清单全部打勾
- 执行看板中 Phase 2 状态更新为 `DONE`
- Phase 3（角色权限体系）任务正式启动


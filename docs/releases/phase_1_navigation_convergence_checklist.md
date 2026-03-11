# SCEMS v1.0 Phase 1：导航收口检查清单

## 1. 目标
确保 `construction_pm_v1` 的主导航、Scene 配置、运行态返回结果三者一致。

## 2. 必做项

### A. 策略定义
- [ ] `construction_pm_v1` 产品面明确为唯一主投放面
- [ ] 主导航 allowlist 固定为 7 项
- [ ] `config.*` `data.*` `internal.*` 在主导航不可见

### B. 运行一致性
- [ ] `system.init` 返回的导航项与 allowlist 一致
- [ ] `system.init` 返回的 scenes 与导航可相互追踪
- [ ] `project.management` 可从导航直接进入

### C. 文档一致性
- [ ] 发布蓝图中的导航定义与实际配置一致
- [ ] `docs/releases/release_scope_v1.md` 已更新为最新导航口径
- [ ] 执行看板已更新 Phase 1 状态

## 3. 建议验证命令
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.runtime.surface.dashboard.strict.guard`

## 4. 交付产物
- 导航收口报告（建议：`artifacts/release/phase1_navigation_convergence.md`）
- 运行证据（相关 verify artifact JSON/MD）

## 5. 退出条件
- 本清单全部打勾
- Phase 1 状态更新为 `DONE`
- Phase 2 任务已创建并开始执行


# SCEMS v1.0 Phase 6：试运行与首发检查清单

## 1. 目标
完成小范围试运行、反馈闭环和首发发布，确保 v1.0 可稳定落地。

## 2. 覆盖范围
- 试运行组织与场景
- 发布前最终门禁
- 首发发布动作
- 发布后观测与回收

## 3. 必做项

### A. 试运行准备
- [x] 试运行组织范围与角色名单明确
- [x] 试运行数据准备完成（项目、合同、成本、资金、风险样本）
- [x] 试运行脚本与问题提报路径明确

### B. 试运行执行
- [x] 核心业务路径全链路演练完成
- [x] 关键角色（项目经理/财务协同/管理层）均完成体验验证
- [x] 试运行问题按严重级别分级并闭环

### C. 首发门禁
- [x] Phase 0~5 退出条件全部满足
- [x] 发布阻断项（P0 缺陷）清零
- [ ] 最终发布评审结论为可发布

### D. 首发发布
- [ ] 发布窗口、回滚窗口、责任人明确
- [ ] 发布步骤按脚本执行并记录
- [ ] 发布完成后关键功能 spot-check 通过

### E. 发布后运营
- [ ] 发布后 24h 关键指标监控正常
- [ ] 用户反馈收集与优先级分流机制启动
- [ ] v1.0 发布总结文档完成

## 4. 建议验证命令
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.runtime.surface.dashboard.strict.guard`

## 5. 交付产物
- 试运行报告（建议：`artifacts/release/phase6_pilot_report.md`）
- 首发记录（建议：`docs/ops/releases/current/scems_v1_0_launch.md`）
- 发布总结（建议：`docs/releases/scems_v1_0_post_launch_review.md`）

## 6. 退出条件
- 清单项全部打勾
- v1.0 首发完成并可回溯
- 执行看板 Phase 6 状态更新为 `DONE`

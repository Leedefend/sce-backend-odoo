# SCEMS v1.0 Phase 4：前端体验稳定检查清单

## 1. 目标
统一页面框架、区块组件与交互规范，确保 V1 前端表现稳定、可预测、可培训。

## 2. 覆盖范围
- 场景页面：`SceneView` / `WorkbenchView` / 关键业务视图
- 契约页面：`ui.contract` 驱动页面
- 区块组件：Header/Metric/Progress/Table/Alert

## 3. 必做项

### A. 页面框架一致性
- [ ] 主要场景页面采用统一布局容器与间距规范
- [ ] 页面标题、面包屑、返回路径行为一致
- [ ] 空状态、加载状态、错误状态表现一致

### B. 区块组件一致性
- [x] 7-block 在视觉层次与数据呈现方式上统一
- [x] 指标卡、表格、告警组件遵循统一 props/数据契约
- [ ] 区块缺数据时采用统一降级样式与文案

### C. 交互规范一致性
- [ ] 主操作按钮位置与命名规范一致
- [ ] 关键跳转（台账 -> 控制台）交互路径一致
- [ ] 搜索、筛选、排序反馈一致（无无响应状态）

### D. 跨模式一致性（user/hud）
- [ ] user 与 hud 模式下关键页面可渲染
- [ ] contract_mode 差异可解释且无破坏性偏差
- [ ] 页面在模式切换后无关键组件丢失

### E. 稳定性与可观测性
- [ ] 页面关键操作无控制台严重报错
- [x] 前端关键 smoke 脚本通过
- [ ] 关键失败场景可定位（日志/报错信息足够）

## 4. 建议验证命令
- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.frontend.lint.src`
- `make verify.frontend.page_contract.runtime_universal.guard`
- `make verify.frontend.page_block_registry_guard`
- `make verify.frontend.page_renderer_default_guard`
- `make verify.frontend.page_block_renderer_smoke`
- `make verify.phase_next.evidence.bundle`

## 5. 交付产物
- 前端稳定性报告（建议：`artifacts/release/phase4_frontend_stability.md`）
- 关键页面截图/录屏样例（建议归档到 `artifacts/release/`）

## 6. 退出条件
- 清单项全部打勾
- 核心场景在 user/hud 模式均可稳定演示
- 执行看板 Phase 4 状态更新为 `DONE`

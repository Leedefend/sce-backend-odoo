# Next Product Scene Preselection v1（Phase 12-B）

## 候选范围
- `project.dashboard`
- `project.plan_bootstrap`
- `project.task_root_init`

## 评估维度
1. 与现有 `project.initiation` 的流程连续性
2. 依赖复杂度（模型/权限/场景耦合）
3. 可验证性（是否可在 smoke 中稳定断言）
4. 失败可降级能力（contract-safe）

## 评估结果

### A. `project.dashboard`
- 优势：与当前 app/nav 已连通，适合作为“创建后落地页”。
- 风险：受数据聚合与统计依赖影响，回归波动较高。

### B. `project.plan_bootstrap`
- 优势：与 initiation 连续，语义清晰（创建后计划初始化）。
- 风险：涉及流程模板、默认任务生成，业务规则较重。

### C. `project.task_root_init`
- 优势：可最小化验证“任务根初始化”闭环。
- 风险：依赖任务结构模型与权限组合，容易引入跨模块耦合。

## 本轮预选结论
- 首选：`project.dashboard`
- 备选：`project.plan_bootstrap`
- 延后：`project.task_root_init`

理由：`project.dashboard` 最适合作为 initiation 的下一个产品体验落点，且更容易构建稳定 smoke。

## 入口预留（仅设计，不实现）
- 预留 `scene_key`: `project.dashboard`
- 预留 `capability_key`: `project.dashboard.open`
- 预留验证入口（下一轮新增）：
  - `make verify.product.project_dashboard`

说明：本轮仅冻结设计与入口命名，不落地 handler/scene 代码。


# v1.0 Iteration Round 2 进展（进行中）

## 1. 目标

在不改平台内核的前提下，继续强化列表型页面的产品表达一致性，并适配模拟生产环境验证链路。

## 2. 已完成

1. 验证链路修复
   - 修复 `role_capability_floor_prod_like` 的管理员登录口令回退策略，适配 prod-sim 常见口令差异。
   - 在 `ENV=test ENV_FILE=.env.prod.sim` 下跑通：
     - `make verify.phase_next.evidence.bundle`

2. 三页列表表达增强（第二轮）
   - `task.center` / `risk.center` / `cost.project_boq` 新增统一 Summary Strip（顶部统计卡）。
   - 新增 scene 级 list profile 预设（仅展示层注入，不改 contract）：
     - 任务中心：任务名称/状态/负责人/截止日期/更新时间
     - 风险中心：风险单号/状态/项目/单位/金额/触发日期
     - 工程量清单：清单名称/项目/工程量/单价/金额/更新时间

## 3. 风险与边界

- 本轮仍未触碰 scene governance、ACL、部署回滚和核心 envelope。
- 列表字段基于运行时模型可见字段显示；若模型缺失对应字段，将自动回退到原始列集合。

## 4. 待你登录验证后执行

1. 根据真实页面反馈做第二轮微调（文案、优先级、状态色阈值）。
2. 如需，补 round2 回归报告并准备下一轮任务包。

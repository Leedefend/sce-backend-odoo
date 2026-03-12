# SCEMS v1.0 Round 4 进展记录（工作台用户视角）

## 本批目标（Batch B）

聚焦“真实业务优先”与“PM 角色可见数据不足”问题，按事实先诊断再修复：

- 先判断是否权限问题；
- 再判断是否 demo 数据分配/归属问题；
- 最后收敛 today_actions 的 fallback 介入策略。

## 事实结论

基于 prod-sim `system.init` 实测：

- PM 角色可见业务集合主要为 `project_actions` + `risk_actions`；
- Finance 角色额外有 `payment_requests`，可见业务行明显更多；
- 当前 PM “数据偏少”并非单一前端渲染问题，属于“角色可见范围 + 示例数据分配”共同结果。

## 本批改动

1. `today_actions` fallback 收敛：
   - 当业务动作数 `>=4` 时，只展示业务动作，不再混入 capability fallback；
   - 仅在业务动作不足时才补 capability fallback。

2. 新增业务可见性诊断：
   - 输出 `diagnostics.business_visibility`；
   - 包含角色期望集合、缺失集合、gap 等级与可能原因；
   - 支撑“权限问题 vs 数据归属问题”快速定位。

3. Hero 状态文案增强：
   - 当业务信号存在但可见集合偏少时，提示“核对项目归属与示例数据分配”；
   - 避免用户误判为系统故障。

## 影响说明

- 不修改 ACL、scene governance、delivery policy、登录链路。
- 不修改 `page_orchestration_v1` 主协议。
- 仅收敛工作台语义与诊断表达层。

## 下一步（Batch C）

- 生成“工作台点击 -> intent”链路清单；
- 固化 10 秒 / 30 秒验收口径；
- 执行最小回归并给出可登录验证点位。

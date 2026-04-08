# 平台开发标准流程 v1

## 1. 总目标

任何新业务模块统一按以下主线推进：

`业务事实层 -> 契约层 -> 前端承接层 -> 运行时验证 -> 基线冻结`

核心原则：

> 先把业务真相做对，再让契约表达准确，最后让前端稳定消费。

## 2. 五层执行顺序

### Phase 1：业务事实层建立

目标：先确认模块在原生页可成立、可办理、可隔离。

必做项：
- 明确核心模型与关键字段。
- 明确 `company_id` / `project_id` 等隔离锚点。
- 明确角色与成员事实。
- 明确最小办理闭环与 outsider deny 边界。

验收标准：
- 原生页可创建、可编辑、可办理。
- outsider 默认不可见/不可写。
- fresh 安装与历史升级均成立。

输出物：
- 业务事实验收文档。
- 隔离矩阵。
- 最小办理闭环验证脚本。

### Phase 2：契约层定义

目标：让后端能力以稳定 contract 暴露，避免前端猜测语义。

必做项：
- 抽取 `list` / `form` / `rights` / `runtime` / `action` surface。
- 明确字段归属：
  - `model-surface`
  - `action-surface`
  - `scene-runtime-extension-surface`
- 冻结稳定字段面，标注条件供给字段。

验收标准：
- 契约语义与原生业务语义一致。
- 前端真实依赖字段已识别。
- 无错误 surface 归属误判。

输出物：
- `docs/ops/contract_alignment_acceptance_v1.md`
- `docs/ops/contract_freeze_surface_v1.md`
- `docs/ops/contract_consumer_dependency_v1.md`

### Phase 3：前端承接

目标：前端仅消费契约，不反向创造业务真相。

必做项：
- 先建立对齐矩阵，再按对象核对：列表、表单、创建、编辑、deny-path。
- 允许 no-op，但必须给出逐项证据。
- 禁止模型特判与权限补丁。

验收标准：
- 通用容器可承接。
- 路由与入口成立。
- 创建/编辑链路成立。
- deny-path 与原生一致。

输出物：
- 前端对齐矩阵。
- slice 对齐报告。
- 端到端最小办理链一致性报告。

### Phase 4：运行时验证

目标：验证真实运行时 payload，不只验证静态代码与文档。

必做项：
- 按角色抓取真实 contract payload。
- 对比 freeze surface 与 consumer dependency。
- 差距分类仅允许：
  - `closed`
  - `intentional-not-in-surface`
  - `conditional-pending-env-supply`

验收标准：
- runtime payload 与冻结面一致。
- 前端依赖字段稳定供给。
- 所有 gap 有归属与处理通道。

输出物：
- runtime payload samples。
- runtime compare 文档。
- runtime acceptance 文档。
- gap list 文档。

### Phase 5：阶段冻结

目标：把当前模块纳入平台基线并设定后续变更门禁。

必做项：
- 冻结业务事实结论。
- 冻结 contract surface。
- 冻结前端承接结论。
- 明确：已完成范围、未覆盖范围、后续门禁。

验收标准：
- 后续迭代不可随意破坏当前结论。
- 新模块可复用同一标准流程。

输出物：
- `docs/ops/delivery_baseline_v1.md`
- 变更门禁规则。
- 冻结结论文档。

## 3. 固定批次模板（新模块通用）

- Batch A：业务事实盘点（模型/字段/隔离/权限/最小办理）
- Batch B：原生闭环（创建/编辑/最小办理/outsider deny）
- Batch C：契约盘点（model/action/runtime surface）
- Batch D：前端对齐（矩阵 + slice + no-op 或最小入口修正）
- Batch E：运行时验证（payload 抓取 + freeze/consumer 对比）
- Batch F：阶段冻结（acceptance + freeze surface + baseline）

## 4. 长期硬规则

- 原生页是真相源，前端不得反向定义业务。
- 权限问题回后端处理，前端禁止权限补丁。
- 模型特判不得常态化，例外需准入理由与退出条件。
- gap 必须分类，禁止笼统“缺失”结论。
- no-op 也必须提交证据链。
- freeze 后字段变更必须走审批门禁。

## 5. 报告统一模板

每轮报告固定包含：

1. Summary of change
2. Verification result
3. Native / contract / frontend consistency evidence
4. Delta assessment
5. Risk analysis
6. Rollback suggestion
7. Next suggestion

## 6. 结论分级标准

- `PASS`：运行态成立、证据完整、无关键 gap。
- `PARTIAL_PASS`：主链成立但有已分类不阻断 gap。
- `PASS_WITH_RISK`：当前目标成立但边界风险未完全收口。
- `FAIL`：主链不成立或证据不足或 gap 未分类。

## 7. 适用边界

- 本标准适用于平台新业务模块交付主线。
- 本标准不授权跨层实现，不替代现有架构守卫与执行白名单。
- 与仓库任务契约冲突时，以任务契约和仓库治理规则优先。

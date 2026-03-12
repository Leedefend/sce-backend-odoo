# v1.0 Iteration Round 1 Scope（产品表达层迭代）

## 1. 本轮目标

本轮目标不是继续扩展平台架构，而是在 `release/construction-system-v1.0` 上完成一轮产品表达层迭代：

- 将页面从“内部工具感”提升为“施工企业管理产品感”；
- 强化页面模式语义、信息优先级、字段可读性与演示可讲述性；
- 在不动核心机制的前提下，提高核心场景的一眼可懂程度。

## 2. 严格边界（本轮不改）

以下范围视为平台内核，本轮不改：

1. `scene registry / scene governance / delivery policy` 核心机制；
2. ACL、记录规则、权限基线；
3. 部署、回滚、发布脚本主逻辑；
4. 核心 contract envelope 结构。

## 3. 允许改动范围（本轮只改）

- 页面模式定义与前端消费方式（dashboard/workspace/list）；
- 页面骨架、标题区、工具区、信息条、状态表达；
- block 呈现优先级与文案语义；
- 字段技术值到产品语义值的映射（展示层优先）；
- 演示数据补齐与少量展示型聚合字段。

## 4. 页面范围

本轮重点覆盖以下页面：

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

## 5. 输出标准

本轮完成后应满足：

- 页面模式区分明确，不再“所有页面都像万能页”；
- 驾驶舱先表达“指标/风险/进度”；
- 台账先表达“项目群总览”，再下钻单项目；
- 列表页不再像裸数据库浏览器；
- 核心页面减少技术字段直出（如 `draft` / `done` / `No`）。

## 6. 完成后的验证与发布策略

- 本轮完成后不立即发布；
- 先执行一轮“产品表达验证”（页面可懂性与演示可讲性）；
- 再执行最小回归：
  - `make verify.frontend.build`
  - `make verify.frontend.typecheck.strict`
  - `make verify.project.dashboard.contract`
  - `make verify.phase_next.evidence.bundle`

## 7. 风险与控制

- 风险：页面表达调整可能影响局部样式和弱耦合字段展示。
- 控制：坚持“展示层优先、结构不破坏、verify 主链路可过”。

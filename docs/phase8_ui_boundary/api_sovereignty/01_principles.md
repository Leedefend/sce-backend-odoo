# API 主权原则（Principles）

**版本**：v1.0

---

## P0：Odoo 是能力引擎，API 是能力主权出口

- Odoo 提供：ORM/ACL/Workflow/Validator/Constraint
- Smart Construction 对外提供：**稳定可演进的 API Contract**
- UI（Odoo 或自研）只是 API 的某种消费端。

> 结论：**Contract 定义产品边界，而不是 Odoo 菜单/视图。**

---

## P1：任何能力必须支持“脱离 Odoo UI 仍成立”

能力 = Model + Rule + Validator（+ Workflow/State Machine）

- UI 不应承载关键约束逻辑
- UI 只负责输入输出、交互呈现
- 校验失败必须可通过 API 返回结构化错误

---

## P2：权限语义以 capability group 为中心，而非菜单/视图

- capability group：表达“能做什么”
- menu/action/view：表达“从哪进入”
- read tier：**可以**赋予 API 读取，但 **不等于** UI 可见入口

---

## P3：Contract v1 优先“稳定与可测试”，再谈“优雅与丰富”

v1 要求：
- 简单一致（统一 Envelope、统一错误、统一分页）
- 可被自动化测试（契约明确，可 mock）
- 可扩展（v2 增量，不破坏 v1）

---

## P4：过渡期允许 Odoo UI 存在，但必须满足“可替换、可弃用”

凡是暂用 Odoo UI 的能力：
- 不依赖复杂前端 attrs/domain 作为关键约束
- 不以 UI 作为唯一操作路径（未来必须 API 可达）
- 所有关键写操作必须有清晰的后端动作与校验点

---

## P5：对“产品级交互”强制 API-first

Level 3（驾驶舱/经营分析/跨项目汇总/高管/移动端）：
- 禁止依赖 Odoo 原生 UI
- 必须走 API（可被 BI/自研前端消费）

# Phase8-B · 能力 API 主权设计（Scope）

**版本**：v1.0  
**阶段**：Phase8-B · 能力 API 主权设计  
**目标**：把《Odoo UI 使用边界白皮书（v1）》落成可执行的 API 边界、契约与权限语义。

---

## 1. In Scope（本阶段要做）

1) **API Contract v1**：统一请求/响应 Envelope、错误、分页、幂等、ETag（可选）等规范。  
2) **权限语义统一**：capability groups（read/user/manager）如何映射到 API 动作。  
3) **Endpoint Catalog**：按“五中心”列出能力端点清单（只定义，不实现）。  
4) **迁移路线**：哪些能力必须 API-first，哪些可先用 Odoo UI 过渡，并定义替换策略。  
5) **与现有系统对齐**：不破坏当前 Odoo UI 可用性，不改业务模型，不引入前后端分离实现。

---

## 2. Out of Scope（本阶段不做）

- 不实现任何 Controller / RPC / REST 代码
- 不重构模型、不改数据库结构
- 不引入新前端、不做移动端
- 不做 BI / 指标平台落地
- 不把 Odoo UI 彻底替换（只定义替换规则与策略）

---

## 3. 约束（必须遵守）

- **能力成立不依赖 UI**：任何关键约束必须在后端 rule/validator 生效。
- **UI 只是入口**：Odoo UI 可随时替换/弃用，不作为能力边界。
- **权限最小化**：read 不等于可见菜单；菜单入口受 user/manager 控制。
- **兼容演进**：Contract v1 需允许 v2 扩展，不做破坏性更改。

---

## 4. Phase8-B 交付物

- `01_principles.md`：API 主权原则
- `02_contract_spec_v1.md`：Contract 规范 v1
- `03_permission_mapping.md`：权限映射矩阵（capability → API）
- `04_endpoint_catalog.md`：端点目录（五中心）
- `05_migration_plan.md`：迁移与演进路线

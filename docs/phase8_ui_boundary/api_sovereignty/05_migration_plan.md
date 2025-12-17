# Migration Plan（从 Odoo UI 过渡到 API-first 的路线）

**版本**：v1.0  
**目标**：保持当前可用性，同时确保未来可替换 UI，不让 Odoo UI 成为能力边界。

---

## 1) 迁移分层（与白皮书 Level 对齐）

### Level 0（系统级）
- 继续使用 Odoo UI
- API 仅用于必要集成（可选）

### Level 1（管理型 UI）
- 可保留 Odoo UI
- 必须定义对应 API（至少 GET/LIST），为未来替换留出口

### Level 2（业务操作型）
- 允许暂用 Odoo UI
- 必须保证：
  - 状态机/审批动作都有 API Action
  - 关键校验在 validator
  - UI 不是唯一入口

### Level 3（产品级交互）
- 强制 API-first
- 任何汇总/驾驶舱/高管/移动端必须走 API
- Odoo UI 仅作为内部验证工具（非产品入口）

---

## 2) 迁移顺序建议（不立即执行）

优先级从“风险最大/收益最大”开始：

1) 财务中心：付款申请/结算动作 API 化（动作最强、权限最敏感）
2) 物资中心：物资计划 + 审批链 API 化
3) 合同中心：合同台账 API 化（供其他域读取）
4) 成控中心：预算与分析 API 化
5) 项目中心：结构/清单导入 API 化（异步任务体系可选）

---

## 3) 验收标准（Phase8-B）

- Contract v1 文档完备（Envelope/错误/分页/幂等/Action）
- 五中心端点目录覆盖现有核心单据
- 权限矩阵与 capability groups 语义一致
- 明确 Level 3 禁止依赖 Odoo UI

---

## 4) 收口方式（与 Phase8 一致）

- 只提交 docs
- 不合并 main
- tag：`api-sovereignty-v1`
- 推分支：`feat/phase8b-api-sovereignty`

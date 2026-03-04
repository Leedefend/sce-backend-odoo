# Odoo 原生视图承载评估（P0 进展版）

English version: [odoo_native_view_contract_gap_assessment_p0_progress_2026-03-03.en.md](./odoo_native_view_contract_gap_assessment_p0_progress_2026-03-03.en.md)

日期：2026-03-03
范围：`smart_core` 契约链路 + `frontend/apps/web` 交互运行时

## 1. 结论（当前是否“完整承载”）

结论：**还不能称为完整承载 Odoo 原生视图系统**，但已完成 P0 关键闭环，系统从“静态可用”进入“可执行交互内核”。

- 已补齐：`modifiers` 最小执行、`onchange` 前后端往返、单一表单引擎入口收敛。
- 仍缺失：x2many 原生命令语义、扩展视图交互（pivot/graph/calendar/gantt）、更完整 attrs 语义与跨模型联动一致性。

## 2. 已完成能力（P0）

### 2.1 Modifier Engine（前端）

已实现文件：
- `frontend/apps/web/src/app/modifierEngine.ts`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

当前能力：
- 运行时输出字段状态：`invisible` / `readonly` / `required`
- 支持表达式：`|` `&` `!` + domain-like tuple
- 对应字段状态已接入渲染层，字段可动态隐藏/只读/必填

### 2.2 Onchange Roundtrip（前后端）

已实现文件：
- 后端：`addons/smart_core/handlers/api_onchange.py`
- 前端 API：`frontend/apps/web/src/api/onchange.ts`
- 前端接入：`frontend/apps/web/src/pages/ContractFormPage.vue`

当前能力：
- 字段变更后前端 300ms 节流触发 `api.onchange`
- 后端返回 `patch` / `modifiers_patch` / `warnings`
- 前端合并 patch 回填 formData，并刷新关系字段 domain 选项

### 2.3 单表单引擎入口收敛

已实现文件：
- `frontend/apps/web/src/router/index.ts`

当前能力：
- `/f/:model/:id` 与 `/r/:model/:id` 均统一到 `ContractFormPage`
- 用户入口层面避免双引擎行为漂移

### 2.4 回归守卫

已实现文件：
- `scripts/verify/modifiers_runtime_guard.py`
- `scripts/verify/onchange_roundtrip_guard.py`
- `Makefile`（已接入 `verify.frontend.quick.gate`）

## 3. 与 Odoo 原生的差距（剩余高优先）

### 3.1 x2many 语义差距（高）

当前多对多/一对多仍以简化多选为主，未形成 Odoo 命令语义闭环：
- 缺 `(0,0,vals)/(1,id,vals)/(2,id)/(6,0,ids)` 的统一前端编辑协议
- 缺内联子表单/行级校验/草稿态命令缓存

影响：复杂业务行编辑、行级 onchange、行级权限将持续失真。

### 3.2 attrs/modifiers 语义覆盖仍偏最小集（中高）

当前仅稳定覆盖 `invisible/readonly/required`。

仍需补充：
- 按 container/group/page 级别修饰
- 更完整表达式兼容（包含 edge cases）
- 与权限策略（field_groups/action_policies）叠加时的冲突判定规范

### 3.3 onchange 契约增强（中）

当前 `api.onchange` 可用，但仍建议补齐：
- 标准化返回协议文档（patch/domain/warning 的 schema）
- 关键模型专项回归（project/task/contract/cost/risk）
- 大表单性能策略（字段白名单、增量 values、可观测性）

### 3.4 双引擎“代码层”尚未移除（中）

虽然路由已收敛到 `ContractFormPage`，但 `RecordView` 代码仍保留。

建议：
- 将 `RecordView` 降级为只读诊断页或移除
- 抽离 `FormCore`（state/action/modifier/onchange）复用于后续表单页

## 4. 契约承载能力评级（2026-03-03）

- 表单基础渲染与动作承载：**A-**
- 原生交互等价性（attrs/onchange/x2many）：**B-**
- 视图体系完整性（含 pivot/graph/calendar/gantt）：**C**
- 可回归与可治理性：**B+**

综合评级：**B（可用于核心业务推进，但未达到“原生完整承载”）**

## 5. 下一步系统性方案（建议顺序）

1. P1：x2many 命令语义层（先命令协议，再 UI）
2. P1：扩展视图只读渲染器（pivot/graph/calendar/gantt）
3. P1：modifiers 语义扩展到容器级 + 冲突优先级规则
4. P2：关键域扩展到 20+ scene 的交互回归矩阵

## 6. 本轮验证证据

- `npm run typecheck`（frontend/apps/web）通过
- `npm run build`（frontend/apps/web）通过
- `make verify.frontend.quick.gate` 通过（含新增 guards）
- `make verify.portal.dashboard` 通过

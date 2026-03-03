# Odoo 原生视图系统承载能力评估（Contract/Frontend 全链路）

日期：2026-03-03  
范围：`ui.contract` 后端契约链路 + Portal 前端渲染/交互链路

## 1. 结论摘要

结论：**当前契约体系无法“完整承载”原生 Odoo 视图系统与交互逻辑**，仅能稳定承载一个“收敛后的子集能力”。

- 当前可稳定承载：
  - `tree/list + kanban + form` 的基础读取
  - 基础字段编辑（部分类型）
  - 按钮执行（`execute_button`）
  - 基础搜索过滤（`search.filters`）
- 当前明显缺失或不一致：
  - 原生 `attrs/modifiers` 的动态交互闭环（前端未消费）
  - 原生 `onchange` 交互链路（后端有入口，前端未接入，且网关模型疑似缺失）
  - x2many 原生编辑语义（命令集/内联子视图）
  - 多视图类型（pivot/graph/calendar/gantt/activity/dashboard）的前端渲染闭环
  - 单一表单引擎一致性（当前存在 `RecordView` 与 `ContractFormPage` 双引擎）

建议判定：
- 如果目标是“对标 Odoo 原生前端能力”：**不达标**。
- 如果目标是“承载当前项目定义的 Portal 收敛能力”：**基本可用，但存在结构性技术债**。

## 2. 评估方法

- 后端契约生成链路：`ui.contract -> dispatch -> page/view assembler -> normalizer`
- 前端消费链路：`ActionView / RecordView / ContractFormPage / View*Renderer`
- 交互链路：`api.data / execute_button / (operation:onchange)`
- 治理与验证：`contract catalog / scene catalog / verify guards`

## 3. 现状能力矩阵

### 3.1 视图结构承载

1. `form/tree/kanban`：**部分支持**
- 后端解析能力较丰富，已解析 `form` 扩展块：`header_buttons/button_box/stat_buttons/field_modifiers/subviews/chatter/attachments`。
- 证据：`addons/smart_core/app_config_engine/models/app_view_config.py` 行 363-375。

2. `pivot/graph/calendar/gantt/activity/dashboard`：**后端有契约，前端渲染不足**
- 后端 view parser 覆盖这些类型；前端 `ActionView` 实际仅分流 `kanban/tree`，其他类型未形成专用渲染页面。
- 证据：
  - 后端支持集：`addons/smart_core/handlers/ui_contract.py` 行 20-24（`VALID_VIEWS`）
  - 前端分流：`frontend/apps/web/src/views/ActionView.vue` 行 405-408、107

3. 表单布局：**双引擎不一致**
- 路由同时存在 `model-form`（`ContractFormPage`）和 `record`（`RecordView`），两套编辑/布局语义不同。
- 证据：`frontend/apps/web/src/router/index.ts` 行 31-32。

### 3.2 交互逻辑承载

1. 按钮执行：**支持（基础）**
- `execute_button` 支持 object/action，并返回 effect（reload/navigate）。
- 证据：`addons/smart_core/handlers/execute_button.py` 行 31-56、98-160。

2. `attrs/modifiers` 动态联动：**未闭环**
- 后端会抽取 modifiers/field_modifiers；前端未检索或执行这些规则。
- 证据：
  - 后端抽取：`addons/smart_core/app_config_engine/services/view_Parser/base.py` 行 114-147
  - 前端无消费：全仓 `frontend/apps/web/src` 无 `field_modifiers` / `modifiers` 使用点

3. `onchange`：**链路不完整**
- `ActionDispatcher` 有 `operation:onchange` 入口，但前端未发起该 intent。
- 并且代码中引用 `self.env['app.action.gateway']`，仓库无该模型定义。
- 证据：
  - 分发入口：`addons/smart_core/app_config_engine/services/dispatchers/action_dispatcher.py` 行 34-40
  - 模型缺失：全仓无 `_name = 'app.action.gateway'`

4. x2many 原生交互：**弱支持**
- `ContractFormPage` 将 many2many/one2many 简化为多选框；`RecordView` 走 `ViewRelationalRenderer` 仅 Name 级增删改。
- 未实现 Odoo x2many 命令语义（如 `(0,0,vals)/(1,id,vals)/(2,id)/(6,0,ids)` 的完整前端编辑体验）。
- 证据：
  - `ContractFormPage`: `many2many/one2many` 分支行 129、1043-1047
  - `ViewRelationalRenderer`: 仅 name 维度编辑 `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue`

### 3.3 契约治理与稳定性

1. 优点
- 契约治理链路健全（catalog/shape/evidence/大量 guards）。
- `relation_entry` 最近已完成契约化增强（`create_mode/default_vals/reason_code`），稳定性提升明显。

2. 风险
- `scene_catalog` 当前仅 5 个场景样本，覆盖广度不足，不能推导“全系统原生承载能力”。
- 证据：`docs/contract/exports/scene_catalog.json` 当前 `scene_count=5`。

## 4. 关键差距（按优先级）

### P0（必须补齐，否则无法称为“原生交互承载”）

1. 动态修饰器执行引擎缺失（`attrs/modifiers`）
- 影响：字段显示/只读/必填联动与 Odoo 行为不一致。
- 根因：后端有契约，前端无解释器。

2. `onchange` 闭环缺失
- 影响：依赖 onchange 的默认值、联动计算、域过滤无法实时生效。
- 根因：前端未接入 + `app.action.gateway` 模型缺失/未实现。

3. 视图类型渲染断层
- 影响：pivot/graph/calendar/gantt 等只能“拿到契约”，无法“按契约渲染交互”。
- 根因：`ActionView` 仅 list/kanban 渲染主路径。

### P1（应尽快补齐，避免行为漂移）

1. 双表单引擎分叉（`RecordView` vs `ContractFormPage`）
- 影响：相同模型不同入口行为不一致，测试成本指数上升。

2. x2many 编辑语义与原生差距大
- 影响：复杂子表编辑场景无法对齐 Odoo。

3. 搜索能力未消费 `group_by/saved_filters`
- 影响：原生搜索体验（分组、收藏筛选）缺失。

### P2（治理增强）

1. 合同覆盖样本偏窄
- 建议把关键模型（project/task/contract/cost/risk）都纳入 scene/contract snapshot 回归。

## 5. 系统性改进路线（建议三阶段）

### 阶段 A：补齐交互内核（2-3 周）

1. 建立前端 `modifier engine`
- 输入：`field_modifiers + formData + context`
- 输出：`visible/readonly/required` 实时态
- 替换当前仅基于 profile/policy 的静态判定

2. 落地 `onchange` 能力
- 后端：补齐/注册 `app.action.gateway`，明确 `run_onchange` 契约
- 前端：字段变更节流触发 `ui.contract(op=operation,onchange)` 或独立 `api.onchange`
- 将返回 patch 合并到 form state

3. 统一表单引擎
- 以 `ViewLayoutRenderer` 为核心，收敛 `ContractFormPage` 与 `RecordView` 的字段渲染逻辑

### 阶段 B：扩展视图与 x2many（2-4 周）

1. 增加 pivot/graph/calendar/gantt 专用渲染器
2. x2many 引入命令语义层（而非仅 name 编辑）
3. many2one 支持 search-more / create-edit / context-domain 实时联动

### 阶段 C：治理闭环（持续）

1. 扩充 contract case 与 scene 覆盖面（至少 20+ 关键场景）
2. 新增专项 guard：
- `modifiers_runtime_guard`
- `onchange_roundtrip_guard`
- `view_type_render_coverage_guard`
- `x2many_command_semantic_guard`
3. 建立“原生等价基线用例”清单并纳入 CI

## 6. 建议的验收门槛（Definition of Done）

满足以下条件后，才建议宣称“可承载原生 Odoo 视图/交互”：

1. `attrs/modifiers` 的动态效果在前端可复现（字段显隐/只读/必填）
2. `onchange` 覆盖关键模型并有回归用例
3. `tree/form/kanban/pivot/graph/calendar/gantt` 至少 7 类视图有可用渲染路径
4. x2many 完成命令语义支持且通过 E2E
5. 单一表单引擎（或双引擎语义一致证明）
6. scene/contract snapshot 覆盖关键业务域并通过漂移检测

## 7. 最终判断

- 当前系统是“**契约驱动的 Portal 收敛实现**”，不是“原生 Odoo Web Client 的完整等价实现”。
- 要达到“完整承载原生视图+交互逻辑”，核心短板在：
  - **动态规则执行（modifiers）**
  - **onchange 实时闭环**
  - **多视图渲染覆盖**
  - **x2many 原生语义**
  - **统一表单引擎**

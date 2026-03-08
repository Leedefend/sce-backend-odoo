# Native / Contract / Scene 职责边界定义 v1

## 1. 五层定义

1. Business Truth Layer（模型层）
- 定义业务事实：字段、约束、状态机、方法、权限规则。

2. Native Expression Layer（XML 层）
- 定义 Odoo 原生表达：form/tree/kanban/search、attrs/modifiers、按钮与布局。

3. Native Parse Layer（解析层）
- 读取原生模型与视图，输出机器可消费的 native 结构。

4. Contract Governance Layer（治理层）
- 统一契约输出形状，按 surface 与策略进行裁剪、标准化、可追踪映射。

5. Scene Orchestration Layer（场景层）
- 按角色/任务组织入口与流程，消费契约能力，不解释底层原生结构。

## 2. 每层负责什么 / 不负责什么

### 2.1 Business Truth Layer
- 负责：
  - 业务模型、计算字段、约束、权限、业务方法。
- 不负责：
  - Portal 页面结构编排。
  - 前端场景体验组织。

### 2.2 Native Expression Layer
- 负责：
  - Odoo 原生界面表达与交互声明。
- 不负责：
  - 产品化场景布局。
  - 用户角色工作台编排。

### 2.3 Native Parse Layer
- 负责：
  - 保真解析 XML/模型元信息为结构化输出。
  - Fallback 仅用于解析兜底，不引入治理策略。
- 不负责：
  - 用户角色裁剪。
  - 合约治理裁决。

### 2.4 Contract Governance Layer
- 负责：
  - `apply_contract_governance` 作为唯一治理入口。
  - 输出 `contract_surface/render_mode/source_mode/governed_from_native/surface_mapping`。
  - 安全收敛、稳定输出、可审计映射证据。
- 不负责：
  - 业务事实创造。
  - 场景产品化组织。

### 2.5 Scene Orchestration Layer
- 负责：
  - 任务流编排、入口组织、角色化组合。
- 不负责：
  - 直接解析 XML。
  - 直接读取 parser 内部结构。
  - 直接做字段/布局级治理裁剪。

## 3. 输入输出边界

### 3.1 Parse -> Governance
- 输入：native parse 结构（尽量保真）。
- 输出：待治理契约草稿。

### 3.2 Governance -> Scene
- 输入：native 草稿 + 策略。
- 输出：`native/governed/hud` surface 契约。

### 3.3 Scene -> Frontend
- 输入：governed（默认）+ native/hud（调试）。
- 输出：按角色/任务组织后的可渲染场景。

## 4. 主链时序图

```text
Odoo Model / XML
    -> Native Parse
    -> Contract Governance (single entry: apply_contract_governance)
    -> Scene Orchestration
    -> Portal Frontend
```

## 5. 常见越界反例

1. Handler 内部做 `form/layout` 重排。
2. Parse 层按用户角色做字段裁剪。
3. Scene 直接调用 `fields_view_get/get_view`。
4. Scene 直接消费 parser 私有结构并二次解释。

## 6. 当前制度化守卫

1. `verify.contract.handler_boundary.guard`
- 防止 handler 夹带布局治理。

2. `verify.contract.parse_boundary.guard`
- 防止 parse 层混入 runtime governance。

3. `verify.scene.input_boundary.guard`
- 防止 scene 越层读取 parser/XML 内部输入。

4. `verify.contract.native_integrity_guard`
- 保障 native surface 保真。

5. `verify.contract.governed_policy_guard`
- 保障 governed surface 策略收敛。

6. `verify.contract.surface_mapping_guard`
- 保障 native -> governed 映射证据完整。


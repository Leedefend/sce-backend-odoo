# Frontend Contract Runtime Architecture Wave v1

English version: `docs/architecture/frontend_contract_runtime_architecture_wave_v1.en.md`

## 1. 迭代定位

### 1.1 目标类型

本轮属于架构级重构，不是页面级修补，也不是视觉层优化。

### 1.2 目标状态

前端从当前的“半解释型页面堆叠（页面组件 + 局部契约消费 + 局部语义推断 + 局部运行时执行）”，升级为“严格契约消费型运行时体系（契约消费层 + 通用运行时层 + 页面装配层 + 纯渲染层）”。

### 1.3 本轮核心目标

- 后端成为唯一业务语义源。
- 前端不再承担业务语义解释职责。
- 页面只负责消费契约、装配页面 VM、输出渲染。
- 核心页面启用 strict contract mode。
- 为后续多前端形态复用预留稳定接口。

## 2. 架构原则

### 2.1 单一语义源原则

后端是唯一业务语义源。前端不得通过关键词、字段组合、默认文案、经验规则推断业务语义。

### 2.2 契约优先原则

前端页面只消费运行时契约产物：`scene_ready`、`page_contract`、`projection`、`action_surface`、`semantic_cells`、`runtime_policy`。

### 2.3 运行时与渲染分离原则

运行时负责执行，渲染层负责展示。渲染组件不得直接调用业务 API，不得解释原始 contract。

### 2.4 strict mode 优先原则

strict contract mode 按以下优先级决策：

1. `runtime_policy.strict_contract_mode=true`
2. `scene_tier=core`

前端不得维护核心场景名单作为 strict mode 真相源。

### 2.5 fallback 收口原则

允许 fallback 仅限 UI 层：`loading`、`empty`、`error`、样式缺省、中性文案缺省。

禁止 fallback：页面类型猜测、动作分组猜测、业务摘要聚合猜测、业务状态语义推断。

## 3. Runtime Consumption Convention

- 首选运行时来源：`scene_ready`
- 次级来源（仅在 `scene_ready` 尚未物化对应字段时）：`scene_contract`
- 前端必须遵循声明的 source priority，不得通过 heuristic 合并多个来源产生语义真相。

## 4. 前端六层模型

### 4.1 `Shell Layer`

职责：应用壳、全局布局、会话态容器、全局错误边界、顶栏/侧栏/HUD Host。

输入：`session/app.init`、全局路由状态。

输出：壳级布局能力、全局上下文容器。

禁止：业务语义解释、业务动作执行、页面契约解析。

### 4.2 `Routing & Navigation Layer`

职责：`scene/action/record` 路由解析、query/context 标准化、导航意图分发。

输入：Vue Router、route params/query、menu/action metadata。

输出：标准化 route context、标准化 navigation target。

禁止：页面语义决定、业务 UI 结构生成。

### 4.3 `Contract Consumption Layer`

职责：解析并归一化 `scene_ready`、`scene_contract`、`page_contract`、`projection`、`action_surface`、`semantic_cells`、`runtime_policy`。

输出：`resolvedSurface`、`resolvedProjection`、`resolvedActionSurface`、`resolvedViewModes`、`resolvedStrictPolicy`。

禁止：直接渲染、直接执行业务动作、通过 heuristic 补业务语义。

### 4.4 `Runtime Execution Layer`

职责：list/form/group/mutation/batch/projection-refresh runtime 执行。

输入：contract-consumption 输出、route context、session context。

输出：运行时状态、可执行动作 handler、加载与刷新结果。

禁止：业务语义推断、业务文案拼装、页面结构决定。

### 4.5 `Page Assembly Layer`

职责：将契约消费结果 + 运行时状态装配为页面 VM。

标准输出：`headerVM`、`filterVM`、`groupVM`、`actionVM`、`contentVM`、`strictAlertVM`、`hudVM`。

禁止：直接发 API、直接解释原始 contract、直接写页面模板逻辑。

### 4.6 `Render Component Layer`

职责：纯渲染，`props + emits`。

输入：Page VM、Section VM、Block VM。

输出：可见界面。

禁止：直接消费原始 contract、直接调用业务 API、越层修改运行时状态。

## 5. 层间依赖规则

依赖方向必须保持单向：

```text
Shell Layer
  -> Routing & Navigation Layer
  -> Contract Consumption Layer
  -> Runtime Execution Layer
  -> Page Assembly Layer
  -> Render Component Layer
```

允许依赖：

- `views/shell` 依赖 `assemblers`
- `assemblers` 依赖 `contracts` 与 `runtime`
- `runtime` 依赖 `contracts` 与 `routing`
- `render components` 仅依赖 `props/emits` 与基础 UI 原语

禁止依赖：

- `Render Component Layer -> business API`
- `Render Component Layer -> raw contract`
- `Shell Layer -> business runtime`
- `Page Assembly Layer -> backend adapter`
- `Runtime Execution Layer -> heuristic semantic resolver`

## 6. 运行时数据流

核心页面统一采用以下数据流：

```text
Route Context
+ Session Context
+ Scene Ready / Page / Projection / Action Surface Contract
-> Contract Consumption Layer
-> Runtime Execution Layer
-> Page Assembly Layer
-> Render Component Layer
```

contract missing fallback 可以维持壳层可用性，但不得伪造业务 label、grouping、summary、semantic status。

## 7. 目录落地目标

```text
frontend/apps/web/src/
  app/
    shell/
    routing/
    contracts/
    runtime/
    assemblers/
  views/
    ActionViewShell.vue
    HomeViewShell.vue
    RecordViewShell.vue
    SceneViewShell.vue
  sections/
  pages/
  fields/
  blocks/
```

目录语义约束：

- `app/contracts/`：契约消费与归一化
- `app/runtime/`：运行时执行
- `app/assemblers/`：页面 VM 装配
- `views/`：页面壳组件
- `sections/pages/fields/blocks/`：纯渲染层

## 8. `ActionView` 拆分目标

### 8.1 拆分原则

`ActionView` 不再作为超级控制器，收口为页面壳组件。

### 8.2 拆分模块

- `useActionViewContract.ts`：strict mode、surface/projection/action-surface/advanced-view contract 消费。
- `useActionViewListRuntime.ts`：加载、搜索、排序、分组、窗口同步、route preset sync。
- `useActionViewActionRuntime.ts`：header/contract actions、mutation execution、refresh policy、record navigation。
- `useActionViewBatchRuntime.ts`：批量动作、failed preview、retry/idempotency。
- `useActionPageModel.ts`：汇总 contract + runtime 输出统一页面 VM。
- `ActionViewShell.vue`：section 装配与页面渲染，不承载业务解释。

## 9. Wave 执行波次

### Wave A：骨架与边界

- 建立 `contracts/runtime/assemblers` 目录与边界约束。
- 建立 `ActionViewShell + composable` 骨架。
- 增加边界 guard，禁止新增 heuristic。

### Wave B：Action 主链迁移

- 将契约消费迁出 `ActionView.vue`。
- 将 list/action/batch runtime 迁出 `ActionView.vue`。
- strict mode 分支下沉到 contract/runtime 层。
- 页面内移除关键词猜测、动作分组猜测、摘要聚合猜测。

### Wave C：渲染层收口

- 抽 section 渲染组件。
- 页面只消费 VM。
- 页面模板不再解释原始 contract。

### Wave D：模式推广

- 同模式复制到 `HomeView`、`RecordView`、`SceneView`。

## 10. 验收门禁

- Gate 1：核心页面禁止业务 heuristic（关键词推断、字段组合推断、业务摘要聚合、动作分组猜测）。
- Gate 2：strict mode 缺失关键契约时必须显式输出 contract-missing，不允许静默业务 fallback。
- Gate 3：页面层禁止直接消费 `ui.contract.views.*` 与原始深层结构，必须先过 Contract Consumption Layer。
- Gate 4：运行时层禁止文案与业务语义拼装。
- Gate 5：`verify.scene.delivery.readiness` 与 strict-consumption 相关验证必须通过。

## 11. 实施声明模板（每个实现任务必须填写）

- Layer Target: `<Shell / Routing / Contracts / Runtime / Assemblers / Render>`
- Module: `<具体模块路径>`
- Reason: `<为何改动，以及对应架构边界>`
- Input: `<依赖的上游产物>`
- Output: `<向下游提供的标准结果>`
- Forbidden: `<本模块明确禁止承担的职责>`

## 12. 非目标（本轮不做）

- 不新增业务功能。
- 不扩展新 scene。
- 不在页面层新增业务解释逻辑。
- 不在渲染组件中接入业务 API。
- 不引入新的页面级 heuristic 兼容逻辑。

## 13. 迁移成功标志

满足以下条件时，视为本轮重构达成：

1. `ActionView` 不再承担 contract 解释主责。
2. 页面壳组件仅负责装配与渲染。
3. strict mode 真相来源完全来自后端。
4. 页面 VM 成为页面层唯一消费对象。
5. `Contracts / Runtime / Assemblers` 三层边界清晰且可复用。
6. 同模式可复制到 `HomeView / RecordView / SceneView`。

## 14. 禁止捷径

- 禁止以“先跑通”为由在页面层补回业务 heuristic。
- 禁止前端硬编码 scene 列表替代后端 strict policy。
- 禁止将 contract 缺口通过默认文案/默认分组/默认摘要伪装为正常能力。
- 禁止只做目录拆分，不做职责拆分。
- 禁止把 assembler 变成新的超级组件或超级 composable。

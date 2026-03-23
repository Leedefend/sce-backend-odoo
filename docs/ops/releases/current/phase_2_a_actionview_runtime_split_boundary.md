# Phase 2 Batch-A ActionView Runtime Split Boundary

## 批次信息

- 批次：Batch-A
- 目标：把 `ActionView` 从“仍由页面持有运行时总控”推进到“页面只做模板消费 + assembler 接线”
- 范围：
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/app/runtime/actionView*`
  - `frontend/apps/web/src/app/assemblers/action/*`
  - 与 `ActionView` 直接耦合的 contract/runtime verify
- 不做：
  - 不改后端 contract
  - 不扩展新业务功能
  - 不处理 `RecordView` / `SceneView` / `HomeView` 的结构性拆分
  - 不重做 shell / router 总体架构

---

## 背景判断

- `ActionView` 仍是前端结构性瓶颈，但现状已不是“完全未拆”。
- 证据：
  - [ActionView.vue](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/views/ActionView.vue)
  - [useActionPageModel.ts](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts)
  - `app/runtime/actionView*` 已存在大量模块化拆分
- 当前核心问题不再是“有没有 runtime 模块”，而是：
  - 页面仍持有中心状态面
  - 页面仍负责 load/action/batch 多条总控链的接线
  - assembler 已有雏形，但还不是真正的 page assembly 入口

---

## 实施步骤

### Step 1

- 操作：
  - 重新盘点 `ActionView` 的现有职责，按三类归档：
    - page state host
    - runtime orchestration glue
    - pure template binding
  - 输出最新版热点地图，替换旧库存中已失真的行号
- 修改范围：
  - `frontend/apps/web/src/views/ActionView.vue`
  - `docs/architecture/frontend_architecture_violation_inventory_v1.md`
- 输出：
  - `ActionView` 当前职责分区图
  - Phase 2 真正要拆的热点清单

完成判据：
- 不再依赖旧库存里的过时行号
- 明确列出 Batch-A 只处理哪些函数/状态面
- 可进入 Step 2

---

### Step 2

- 操作：
  - 把 `ActionView` 的 `load` 主链总控抽到独立 assembler/runtime 入口
  - 页面只保留：
    - 触发 load
    - 消费 assembler 输出的 VM / 状态
  - 页面不再自己拼装 load 总流程
- 修改范围：
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/app/runtime/actionViewLoad*`
  - `frontend/apps/web/src/app/assemblers/action/*`
- 输出：
  - `ActionView load controller` 或等价 assembler 入口

完成判据：
- `ActionView.vue` 中不再持有 load 总控主干
- load 过程的状态推进可从独立入口追踪
- 页面侧只保留消费接口
- 可进入 Step 3

---

### Step 3

- 操作：
  - 把 `runContractAction` 及 header/quick action 的运行时接线继续外移
  - 页面内按钮点击只调 runtime facade，不直接掌控 mutation/navigation/refresh 细节
- 修改范围：
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts`
  - 相关 action runtime 模块
- 输出：
  - 单一 action facade
  - 页面事件处理函数瘦身

完成判据：
- `ActionView.vue` 不再包含 action 执行主分支
- action runtime 可单独验证
- 可进入 Step 4

---

### Step 4

- 操作：
  - 把 batch 主链收敛到独立 runtime capsule
  - 页面只接 `batch state + batch facade`
- 修改范围：
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/app/runtime/actionViewBatch*`
- 输出：
  - batch facade
  - batch state capsule

完成判据：
- `ActionView.vue` 中 batch 相关状态与流程显著下降
- batch 失败、导出、明细、assign 主链不再在页面内分散组织
- 可进入 Step 5

---

### Step 5

- 操作：
  - 以 `useActionPageModel` 为中心，建立真正的 page assembly 入口
  - 让 `ActionView` 只保留模板绑定、少量路由桥接和生命周期触发
- 修改范围：
  - `frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts`
  - `frontend/apps/web/src/views/ActionView.vue`
- 输出：
  - `ActionView` page assembly 结构定稿
  - 更新后的 architecture closure 文档

完成判据：
- `ActionView` 可被描述为“template consumer + assembly hook”
- 前端库存文档能反映真实结构变化
- Batch-A 完成

---

## 验证步骤

- verify：
  - `make verify.frontend.typecheck.strict`
  - `make verify.product.final_slice_readiness_audit`
- snapshot：
  - 更新 `docs/architecture/frontend_architecture_violation_inventory_v1.md`
  - 如需，补 `ActionView` 职责快照文档
- guard：
  - `make verify.frontend.zero_business_semantics`
  - 与 `ActionView` 相关的 contract/runtime guard
- smoke：
  - `make verify.portal.login_browser_smoke.prod_sim ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
  - 现有 `ActionView` 相关 smoke 如 list/view/render/execute button 按变更面补跑

---

## 风险与回滚

- 风险：
  - 抽 runtime 总控时把现有页面状态依赖打散，导致 list/kanban/advanced 三种模式回归
  - facade 抽象过度，形成新的“runtime 迷宫”
  - assembler 与 runtime 边界不清，变成“换文件不换职责”
- 回滚：
  - 按 Step 颗粒度提交
  - 每步失败只回滚对应模块：
    - load 拆分失败：回滚 `actionViewLoad*` + `ActionView.vue`
    - action 拆分失败：回滚 `actionViewContractActionRuntime.ts` 相关改动
    - batch 拆分失败：回滚 `actionViewBatch*`
    - assembler 失败：回滚 `app/assemblers/action/*`

---

## 停机条件

- `ActionView` 当前 contract 输入面定义不清
- 拆分后 `verify.frontend.typecheck.strict` 失败
- 拆分后 `final_slice_readiness_audit` 不再为绿
- 拆分过程中牵出后端 contract 重构需求
- 发现当前 runtime 模块虽多，但缺失统一 facade 设计，导致本批次范围不足以闭环

---

## 批次结论

- Phase 2 的第一批任务不应再做零碎页面修补
- 正确边界是：`ActionView load/action/batch 总控外移 + page assembly 入口成形`
- 建议执行顺序：
  1. 更新 `ActionView` 热点地图
  2. 先拆 `load`
  3. 再拆 `action`
  4. 再拆 `batch`
  5. 最后收敛到 assembler

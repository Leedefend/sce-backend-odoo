# 后端契约收口阶段验收（v1.1.1）

## 1. 验收范围

- 计划基线：`docs/releases/backend_contract_closure_iteration_plan_v1.md`
- 本阶段目标：P0 + P1 + P2（本轮收口项）
- 验收口径：
  - 契约结构与字段语义
  - 前端启动链与落地消费路径
  - 基础验证（后端语法、前端 strict typecheck）

## 2. 分项验收结果

### P0 启动链路收口

- `P0-1` login 契约边界统一：**通过**
  - `session/user/entitlement/bootstrap/contract` 主干结构已稳定。
  - `contract_mode=default|compat|debug` 已落地，`compat` 支持开关与弃用提示。

- `P0-2` role 真源统一：**通过**
  - 以 `role_surface.role_code` 为真源，镜像到 `workspace_home.record.hero.role_code` 与 `page_orchestration_v1.page.context.role_code`。

- `P0-3` 版本职责统一：**通过**
  - 主链契约统一语义化 `1.0.0`。
  - `ui.contract` 兼容性结构版本下沉为 `payload_schema_version`，避免混淆顶层 `schema_version`。

- `P0-4` 启动链唯一化：**通过**
  - 前端门禁限制“已登录未 init”阶段的意图调用范围。
  - login bootstrap 提供例外白名单提示（`session.bootstrap`、`scene.health`）。

### P1 结构优化

- `P1-1` system.init 四区块拆分：**通过**
  - 输出 `system_init_sections_v1`（`session/nav/surface/bootstrap_refs`）。
  - 保持 `init_contract_v1` 兼容映射。

- `P1-2` workspace_home 按需加载：**通过**
  - 默认 `system.init` 不预加载 `workspace_home`，仅返回 `workspace_home_ref`。
  - 前端新增按需补拉（`loadWorkspaceHomeOnDemand`）。

- `P1-3` intent 目录独立化：**通过**
  - `system.init` 最小化意图面，不再携带 `intents_meta`。
  - 全量目录通过 `meta.intent_catalog` 独立提供。

- `P1-5` default_route 语义补全落地：**通过**
  - 前端 `resolveLandingPath` 优先消费 `default_route.route/scene_key`。

### P2 治理增强（本轮涉及）

- `P2-4` 首页 block 化：**通过（本轮收口）**
  - `HomeView` 对 `hero/metrics/risk/ops` 的运行时消费统一收口为 `workspace_home.blocks`。
  - legacy 回退引用已清理。

## 3. 验证证据

- 后端语法检查：
  - `python3 -m py_compile addons/smart_core/core/system_init_payload_builder.py addons/smart_core/handlers/login.py addons/smart_core/handlers/system_init.py addons/smart_core/handlers/ui_contract.py addons/smart_core/tests/test_v1_intent_smoke.py`
  - 结果：通过

- 前端 strict 校验：
  - `pnpm -C frontend typecheck:strict`
  - 结果：通过

- block-only 额外检查：
  - `rg -n "workspaceHome\.value\.(hero|metrics|risk|ops)" frontend/apps/web/src/views/HomeView.vue`
  - 结果：无命中

## 4. 阶段结论

- 结论：**本阶段达到“验收收口通过（Ready for PR）”**。
- 当前剩余动作：
  - 进行一次改动分类提交（contract/backend/frontend/docs）。
  - 生成 PR 描述并附本验收文档作为审阅入口。


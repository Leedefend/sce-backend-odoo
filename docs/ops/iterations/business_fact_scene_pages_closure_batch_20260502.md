# Batch-Business-Fact-Scene-Pages-Closure

## 1. 本轮变更
- 目标：在业务事实模型完善后，查清并验收本分支新增/改造的场景契约页，并按模拟生产环境收口验证。
- 完成：
  - `workspace.home`：主干已有 scene key，本分支从 `/my-work` 原页面入口改造成 `/s/workspace.home` 场景契约页，intent 为 `workspace.home.enter`。
  - `dashboard.company`：本分支新增 scene key，入口为 `/s/dashboard.company`，intent 为 `dashboard.company.enter`。
  - 两个场景都由后端 `scene_block_schema` 生成 block-grid 契约，前端通过 `SceneContractBlockGridView` 渲染，不依赖 Odoo 原生页面直接支撑主体验。
  - `project.management`、`projects.intake` 属于本轮后续路由显式化/场景身份收口：补齐 `/s/project.management`、`/s/projects.intake` 显式路由与 `meta.sceneKey`，但不是 `main...HEAD` 中新增的 scene registry key。
  - 通用 scene contract block grid 支持 `scene_key`、带 query 的 `route`、block/item target 透传。
  - 指标卡区块支持 `action_key` 点击上抛，避免业务卡片呈现但无法进入下一步。
  - 修复 prod-sim 浏览器初始化失败：业务菜单事实同步不再把 `ir.actions.client` 强写成 `ir.actions.act_window`。
  - 收口场景契约页前端呈现：隐藏两个契约场景的壳层重复标题，指标卡不再重复显示同名标题，`native_view_ref` 不再把 `target` JSON 裸露给用户。
  - 前端验证 guard 已同步到当前的直接场景路由策略，不再只接受旧的 `SceneView -> /pm/dashboard` 桥接模式。
- 未完成：当前 Playwright 宿主缺 CJK 字体，截图中文字形显示为方块；DOM 文本内容与接口数据正确，需在带中文字体的真实浏览器环境下复核最终字形。

## 2. 影响范围
- 模块：smart_construction_core、smart_construction_scene、frontend/apps/web
- 路由：是，新增/改造 `/s/workspace.home`、`/s/dashboard.company` 场景入口；并补充 `/s/projects.intake`、`/s/project.management` 显式路由收口。
- contract：是，新增 `workspace.home.enter`、`dashboard.company.enter` 两个 scene contract intent 与对应 block schema 消费链路。
- public intent：否。
- 数据库：为恢复 prod-sim 验证账号基线，执行过 `sc_prod_sim` 全量隔离重建；随后在 prod-sim 中重放 `sc.business.menu.taxonomy.seed.sync_full_coverage()` 并提交，修复既有坏菜单 action。

## 3. 风险
- P0：无。prod-sim 标准隔离验证已通过。
- P1：`verify.portal.scene_contract_smoke.container` 仍与当前 prod-sim API 基线不完全一致，卡在旧 `app.init` 路径和缺失 action；本轮未将其作为阻断证据。
- P1：当前 Playwright 宿主缺 CJK 字体，截图中文字形为方块；这不是接口/DOM 文本错误，但真实交付机需要确认系统字体或 WebFont 策略。
- P2：通用 block grid 当前支持常见 target 形态，后续若出现复杂 target 协议，需要继续扩展统一 action runtime，而不是在页面内堆分支。

## 4. 验证
- prod-sim 前端构建：
  - `docker run --rm -v /home/odoo/workspace/sce-backend-odoo:/workspace -w /workspace/frontend node:20-bookworm sh -lc "corepack enable && pnpm install --frozen-lockfile && VITE_API_BASE_URL= VITE_ODOO_DB=sc_prod_sim VITE_APP_ENV=prod-sim pnpm build"`
  - 结果：PASS，nginx 静态入口返回 `assets/index-DYxCF4e5.js` 与 `assets/index-B7-6RGIv.css`。
- prod-sim 标准验证：
  - `make verify.prod.sim.isolation.quick`
  - 初次结果：FAIL，`svc_e2e_smoke/demo` 登录 401。
  - `make verify.prod.sim.isolation`
  - 结果：PASS，重建并恢复 `sc_prod_sim` 基线。
  - `make verify.prod.sim.isolation.quick`
  - 结果：PASS。
- 前端静态 guard：
  - `make verify.frontend.project_management.scene_bridge.guard verify.frontend.scene_contract_auto_render.guard verify.frontend.page_block_registry_guard verify.frontend.page_block_renderer_smoke`
  - 结果：PASS。
- prod-sim 场景契约 intent 验收：
  - 登录：`svc_e2e_smoke/demo`，数据库 `sc_prod_sim`。
  - `workspace.home.enter`：HTTP 200，`ok=true`，`scene_key=workspace.home`，标题“工作台”，`block_count=7`，block 类型为 `metric_card/shortcut_grid/todo_list/warning_list/native_view_ref`。
  - `dashboard.company.enter`：HTTP 200，`ok=true`，`scene_key=dashboard.company`，标题“公司驾驶舱”，`block_count=7`，block 类型为 `metric_card/warning_list/shortcut_grid/native_view_ref`。
- prod-sim 浏览器验收：
  - 入口：`http://127.0.0.1/`，数据库 `sc_prod_sim`，用户 `svc_e2e_smoke/demo`，静态资源来自 nginx 挂载的 `frontend/apps/web/dist`。
  - 初始问题：`/s/workspace.home` 与 `/s/dashboard.company` 都卡在“初始化失败”，错误为 `Record: ir.actions.act_window(675,)`。
  - 根因：`action_sc_project_workbench` 是 `ir.actions.client(675)`，但业务菜单事实同步把“我的审批/最近访问”写成了 `ir.actions.act_window,675`。
  - 修复后 `/s/workspace.home`：7 个区块、3 个指标项、4 个入口按钮；无初始化失败、无场景失败、无 `target` JSON 裸露、无指标标题重复。
  - 修复后 `/s/dashboard.company`：7 个区块、4 个指标项、4 个入口按钮；无初始化失败、无场景失败、无 `target` JSON 裸露、无指标标题重复。
  - 截图：`/tmp/workspace-scene-final3.png`、`/tmp/company-scene-final3.png`。
- prod-sim 全量历史数据重放与主线回归：
  - 说明：早先只跑过用户历史子集，不足以作为本轮最终验收；本次补跑完整 `history.continuity.replay` 路线。
  - `RUN_ID=prod_sim_full_history_20260502T204701 HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 MIGRATION_REPLAY_DB_ALLOWLIST=sc_prod_sim MIGRATION_ARTIFACT_ROOT=/tmp/history_continuity/sc_prod_sim/prod_sim_full_history_20260502T204701 make history.continuity.replay`：完整路线完成，结果目录内 80 个 `*result*v1.json` 均可解析，失败计数 0。
  - 覆盖结果包括用户、部门画像、用户项目范围、任务证据、partner/project anchor、角色访问投影、账户主档与流水、材料分类与明细、文件索引、合同/采购/供应商合同、回款/发票/税费、费用报销/保证金、付款执行、结算调整、资金台账与资金对账、融资借款、施工日志、附件保管等历史业务路线。
  - 大量级重放样例：用户 101；用户项目范围 90,871；任务证据 78,822；partner anchor 6,541；project anchor 755；材料分类 130,624；材料明细 2,279,734；文件索引 178,931；合同头 1,492；合同明细 1,441。
  - 完整路线运行时探针产物包括 `history_continuity_usability_probe_result_v1.json`、`history_purchase_contract_runtime_probe_result_v1.json`、`history_material_catalog_runtime_probe_result_v1.json`、`history_invoice_tax_runtime_probe_result_v1.json`、`history_payment_execution_runtime_probe_result_v1.json`、`history_receipt_income_runtime_probe_result_v1.json`、`history_treasury_reconciliation_runtime_probe_result_v1.json`、`history_attachment_custody_probe_result_v1.json` 等，失败计数 0。
  - `make history.business.usable.probe`：PASS，`decision=history_business_usable_visible_but_promotion_gaps`，`gap_count=1`，无 DB 写入。唯一剩余项为 `payment_request_no_pending_runtime_states=true`；其他 runtime/list/form、合同伙伴、付款执行、回款、税务、结算、资金对账、融资、费用、材料、施工日志、采购合同、一般合同、用户访问投影等 gap 均为 false。该结果优于早先用户子集后的 runtime gap，但按生产切换标准仍需单独关闭 promotion gap，不能把它写成正式切换 ready。
  - `make verify.prod.sim.isolation.quick`：PASS。
  - HTTP 点查：真实历史用户 `wutao/123456` 登录 PASS，`system.init` PASS；`svc_e2e_smoke/demo` 登录 PASS，`system.init` PASS；两个用户调用 `workspace.home.enter` 与 `dashboard.company.enter` 均 HTTP 200、`ok=true`、`blocks=7`。
  - 全量历史重放后浏览器复核：真实用户 `wutao/123456` 访问 `/s/workspace.home` 与 `/s/dashboard.company`，页面显示历史业务汇总数据，无场景加载失败、无 console error、无 4xx/5xx 网络响应。
  - 截图：`/tmp/workspace-home-after-full-history.png`、`/tmp/dashboard-company-after-full-history.png`。
- Type/build：
  - `pnpm -C frontend/apps/web typecheck`
  - 结果：PASS。
  - `pnpm -C frontend/apps/web build`
  - 结果：PASS。
- Lint：
  - 本轮改动文件 eslint：PASS。
  - 全量 `pnpm -C frontend/apps/web lint`：FAIL，失败来自既有 `any`/未使用变量/重复 key 等历史问题，非本轮新增。

## 5. 产物
- prod-sim 交付仿真报告：
  - `docs/ops/audit/delivery_simulation_report.md`
  - `artifacts/backend/delivery_simulation_report.json`
- 前端 guard 报告：
  - `docs/ops/audit/frontend_scene_contract_auto_render_guard_report.md`
  - `artifacts/backend/frontend_scene_contract_auto_render_guard_report.json`
- 浏览器截图：
  - `/tmp/workspace-scene-final3.png`
  - `/tmp/company-scene-final3.png`
  - `/tmp/workspace-home-after-full-history.png`
  - `/tmp/dashboard-company-after-full-history.png`

## 6. 回滚
- 回退本批前端路由与通用区块渲染改动。
- 重新执行 prod-sim 前端构建，确保 nginx 挂载的 `frontend/apps/web/dist` 回到上一版本。

## 7. 下一步
- 用带 CJK 字体的真实桌面浏览器复核 `/s/workspace.home`、`/s/dashboard.company` 字形与视觉密度。
- 继续人工点验 `/s/projects.intake`、`/s/project.management`，确认本轮路由显式化没有引入回归。
- 单独处理 `verify.portal.scene_contract_smoke.container` 与当前 `system.init`/action 基线的漂移。

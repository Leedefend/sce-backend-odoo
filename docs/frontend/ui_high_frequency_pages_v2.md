# High-Frequency Business Pages V2

## Goal

本文件用于记录“高频业务页面二次收口专项 v2”的三批目标、范围和已完成结果。

## Batch 1

- 目标：项目详情、任务详情的对象控制台化收口
- 范围：`ContractFormPage`、`DetailShellLayout`、`DetailCommandBar`、`FormSection`
- 不做：首页/工作台、合同/付款/结算页、后端契约、token/base 重做
- 已完成：
  - `PageHeader` 升级为控制台头部容器，补强状态摘要卡与动作层级
  - `ContractFormPage` 概览区改为“主摘要卡 + 次级信息卡”，减少表单堆砌感
  - `DetailCommandBar` 改为“流程阶段 / 下一步动作”双区结构
  - `DetailShellLayout` 与 `FormSection` 统一分区容器、页签、嵌套 section 的秩序
  - relation / chatter / activity 语义统一沉到辅助区卡片
  - `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-A` 已把上述辅助壳层继续收口到 token 基线，补齐 command bar / tab rail / nested shell / mini table 的统一视觉层级
  - `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-B` 已继续收口 `ContractFormPage` support-zone 与 `BlockActivityFeed`，补齐关系/协作卡片、count badge、activity card 的统一视觉节奏
  - `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-C` 已继续收口 structure diagnostics、inline feedback、advanced toggle 与 footer action，使详情页 section 邻接反馈面与 token 体系一致
  - `ITER-2026-04-19-FE-UI-SYSTEM-CONVERGENCE-V2-D` 已把 `RecordView` 与 `MyWorkView` 这两个 legacy list/form wrapper 的 header、summary、filters、retry panel、table shell、chatter timeline 统一到同一 token 基线
- 验证：
  - `pnpm -C frontend/apps/web lint` PASS
  - `pnpm -C frontend/apps/web build` PASS

## Batch 2

- 目标：项目列表、任务列表的效率感与高级感收口
- 范围：`ListPage`、`PageToolbar`、`BlockRecordTable`
- 不做：详情页返工、非目标业务页扩面、后端契约改动
- 已完成：
  - `ListPage` 增加列表摘要带、批量处理摘要区、行级风险/状态强调与负责人/进度信息节奏
  - 列表顶栏、搜索区、分页区、批量动作区层级进一步统一
  - `PageToolbar` 的筛选/分组/高级筛选容器与 chip 语言进一步对齐
  - `BlockRecordTable` 补强区块头部、记录数、副标题和 hover 节奏
- 验证：
  - `pnpm -C frontend/apps/web lint` PASS
  - `pnpm -C frontend/apps/web build` PASS

## Batch 3

- 目标：4 个页面 walkthrough 与截图证据
- 范围：Playwright/host browser evidence、walkthrough 文档、剩余问题清单
- 不做：运行时代码修改、首页/工作台实现
- 已完成：
  - 使用真实用户 `wutao / demo` 拿到项目列表、项目详情、任务入口页三张浏览器截图证据
  - 验证 `项目列表 -> 项目详情 -> 返回` 链路可走通，返回落点与项目列表 action 路由一致
  - 二次验证确认自动点击误入 `action_id=594`，其契约模型为 `mail.activity / 待办提醒`，并非 `project.task`
  - 三次验证进一步确认真实任务入口来自项目详情的 `task_ids` / `tasks` 关系子表，而非头部统计卡
  - `api.data` 已确认项目 `#1` 存在任务 `#1（项目根任务（Project Root Task））`
  - `ui.contract(action_open=457, record=1)` 与 `ui.contract(model=project.task, form, record=1)` 均可正常返回，后端契约与数据已排除
  - 当前仍未形成任务详情证据闭环：内嵌任务子表的页签/行点击未稳定命中，且 `project.task` 详情在自定义前端中的路由消费/装载仍挂起
- 验证：
  - `make verify.portal.host_browser_runtime_probe` PASS
  - `node scripts/verify/high_frequency_pages_v2_walkthrough.mjs` FAIL
    - 原因：`wutao` 项目详情页的自动点击曾命中 `mail.activity` 入口；进一步修正后，当前剩余阻断点为 `task_ids` 关系子表的稳定点击与 `project.task` 详情路由消费挂起
  - `ITER-2026-04-19-FE-PROJECT-TASK-FORM-ROUTE-RECOVERY` 追加结果：
    - `ContractFormPage` 已把 relation hydration 改为非阻塞首屏
    - `pnpm -C frontend/apps/web typecheck:strict` PASS
    - `pnpm -C frontend/apps/web build` PASS
    - 直达任务路由证据仍未闭环：`artifacts/playwright/high_frequency_pages_v2/direct-task-probe/task-route-probe.png` 显示空白 `#app` 壳层，无 `返回`、无错误态、无 `__scFormDebug`
    - 因此下一轮应上移到 startup / router bootstrap 诊断，而不是继续局限在任务详情页模板
  - `ITER-2026-04-19-FE-DIRECT-ROUTE-BOOTSTRAP-RECOVERY` 当前结果：
    - startup overlay 已接管 direct route 的短窗口白屏
    - 8 秒窗口截图：`artifacts/playwright/high_frequency_pages_v2/direct-task-probe/task-route-bootstrap-8s.png`
    - 长等待探针已确认 `project.task` 详情最终能正常挂载
    - 当前剩余问题从“白屏/无法挂载”转成“启动链过慢”
    - shell 计时显示 `system.init` 本身耗时约 `18s~20s`，不主要是前端代理问题

# 全系统用户体验走查 round 1

## 本轮范围

分支：`topic/system-user-experience-coverage`

本轮先完成全系统用户体验专题的基线锁定，并复用现有浏览器验收确认配置工作台、菜单配置、业务列表、业务表单和移动端页面结构是否已经达到继续扩展的前提。

## 已完成证据

### 专题覆盖矩阵

- 文件：`docs/product/system_user_experience_coverage_v1.json`
- 覆盖角色：6 个
- 覆盖旅程：12 条
- 覆盖页面面：11 类
- 覆盖页面模式：6 类
- 覆盖用户动作：56 个
- 自动化证据项：11 个
- 浏览器证据要求：8 条

验证：

```bash
make verify.system_user_experience.coverage_guard
```

结果：

```text
[system_user_experience_coverage_guard] PASS roles=6 journeys=12 surface_types=11 page_modes=6 user_actions=56 automated_evidence=11 browser_evidence=8
```

### 页面结构基线

验证：

```bash
make verify.product.page_structure
```

结果：

```json
{"ok":true,"schema_version":"product_page_structure_guard.v1","shell_files":6,"region_files":8,"page_mode_files":9,"page_modes":6,"region_classes":6,"config_workbench_journeys":10,"config_workbench_actions":19,"config_workbench_assertions":64,"config_workbench_screenshots":9}
```

### 浏览器操作验收

验证：

```bash
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.business_config.config_workbench_operation_acceptance
```

结果：

```json
{
  "ok": true,
  "assertion": "64/64",
  "journeys": "10/10",
  "actions": "19/19",
  "screenshots": "9/9",
  "delivery": "delivery_ready",
  "professional": "professional_ready",
  "consoleErrors": 0,
  "requestFailed": 0,
  "menuTreeHead": "菜单目录\n122 个可配置菜单\n直接拖拽排序"
}
```

浏览器产物：

- `artifacts/playwright/config-workbench-operation/report.json`
- `artifacts/playwright/config-workbench-operation/summary.json`
- `artifacts/playwright/config-workbench-operation/01-selected-from-scan.png`
- `artifacts/playwright/config-workbench-operation/02-switched-page.png`
- `artifacts/playwright/config-workbench-operation/03-direct-selected.png`
- `artifacts/playwright/config-workbench-operation/04-list-search-entry.png`
- `artifacts/playwright/config-workbench-operation/05-approval-entry.png`
- `artifacts/playwright/config-workbench-operation/06-form-designer-entry.png`
- `artifacts/playwright/config-workbench-operation/07-menu-config.png`
- `artifacts/playwright/config-workbench-operation/08-mobile-selected.png`
- `artifacts/playwright/config-workbench-operation/09-mobile-viewport.png`

## 当前判断

### 已稳定

- 配置工作台可以进入并完成 10 条关键旅程。
- 菜单配置页面可配置菜单口径为 `122 个可配置菜单`。
- 配置工作台、菜单配置、业务列表、业务表单均具备运行时页面模式和产品级区域语义。
- 配置工作台、业务列表、业务表单、菜单配置的 Header 与主内容外边界 `maxDelta=0`。
- 移动端 390px 无横向溢出，当前配置区域在首要视口中可见。
- 浏览器健康为 `consoleErrors=0`、`requestFailed=0`。

### 仍需扩展

本轮浏览器证据还偏向低代码配置域，虽然已经覆盖了部分业务列表和业务表单结构，但还不能代表“全系统用户使用视角”完整闭环。下一轮必须扩展到以下用户路径：

| 编号 | 类型 | 目标 | 原因 |
| --- | --- | --- | --- |
| UX-R2-001 | 业务表单保存 | 支付申请、施工日志、材料入库单至少覆盖一个真实保存闭环 | 用户最终感知是能不能办成业务，不只是页面结构正确 |
| UX-R2-002 | 业务详情阅读 | 结算单或合同详情的身份、金额、状态、来源和返回路径 | 详情阅读是查询型用户的高频路径 |
| UX-R2-003 | 经营驾驶舱 | 领导角色 10 秒状态判断和下钻返回 | 当前缺少 dashboard 真实浏览器证据 |
| UX-R2-004 | 支持诊断 | 系统健康、发布版本、配置变更、诊断导出 | 交付后支持人员需要可理解入口 |
| UX-R2-005 | 首页首跳 | 登录后默认任务中心和角色上下文 | 产品第一印象不能只依赖导航菜单 |

## 批量优化方向

后续不要按单页面零散处理，按问题类型批量推进：

1. 任务流：新建、保存、返回、刷新、空态下一步。
2. 数据理解：主字段、状态、金额、来源、附件证据。
3. 页面结构：Header、Toolbar、Summary、Main Surface、Feedback 对齐和职责。
4. 用户语言：清理技术词、模型名、action id、字段技术名。
5. 移动端：390px 首屏任务可达和无横向溢出。
6. 支持路径：只读诊断、发布状态、配置变更、导出证据。

## 下一步

下一轮应新增或扩展浏览器操作验收脚本，优先覆盖：

- 首页首跳。
- 项目台账列表搜索。
- 支付申请或施工日志新建保存。
- 合同或结算详情阅读。
- 经营驾驶舱查看与下钻。

完成后再进入页面和交互批量修复。

## round 2 补充

已将业务表单用户视角验收纳入专题门禁：

```bash
make verify.system_user_experience.business_form_user_perspective
make verify.system_user_experience.full_browser
```

业务表单验收覆盖 20 条办理路径，包含借款、结算、收款、自筹垫付、资金往来、支付申请、收款申请、报销、投标保证金、扣款、还款、材料入库、施工日志、抵扣登记和票税办理。第二轮验收结果：

```text
caseCount=20
failures=0
missing=0
leaked=0
consoleErrors=0
```

本轮同时修正了验收脚本中的旧产品语言：例如“自筹金额”已对齐为“自筹垫付金额”，“调拨金额”对齐为通用“金额”，“项目与报销人”对齐为“项目与往来单位”，“项目与日期”对齐为“项目与日志”。该调整不是降低标准，而是让验收跟随当前产品化后的用户可见文案。

full browser gate 已通过：

```bash
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.system_user_experience.full_browser
```

结果：

```text
[OK] verify.system_user_experience.full_browser done
```

专题级汇总产物：

- `artifacts/playwright/system-user-experience-full-browser/summary.json`

该汇总同时读取配置工作台、shell 路径和业务表单 3 条浏览器报告，统一判断 assertions、journeys、screenshots、shell case、业务表单 case、console error 和 failed request。

## round 3 补充

已新增非表单路径 shell 验收：

```bash
make verify.system_user_experience.shell_acceptance
```

覆盖：

- 首页首跳。
- 我的工作。
- 项目台账列表。
- 发布支持控制台普通用户权限边界。
- 移动端首页。

结果：

```text
caseCount=5
failures=0
consoleErrors=0
requestFailed=0
```

已补充 shell summary guard，固定 5 个 shell 用例的 key、截图证据、横向溢出、技术词泄漏、console error 和 failed request 检查：

```bash
cd frontend/apps/web && node scripts/system_user_experience_shell_summary_guard.mjs
```

本轮发现并确认：首页当前产品语言是“今天先做什么 / 今日优先动作 / 角色能力摘要”，而不是旧验收词“今日待办 / 关键风险”。发布控制台对当前业务配置管理员不可见，会重定向到可访问业务页面，这属于普通用户权限边界。真正的支持人员诊断入口仍需要后续用支持角色或平台管理员账号单独验证。

## round 4 补充

已加固专题验收脚本的仓库根目录定位。`business_form_user_perspective_summary_guard`、`system_user_experience_shell_acceptance`、`system_user_experience_shell_summary_guard`、`system_user_experience_full_browser_summary_guard` 不再依赖调用方当前工作目录，而是基于脚本文件自身位置定位仓库根目录。

复验命令：

```bash
make verify.system_user_experience.quick
node frontend/apps/web/scripts/business_form_user_perspective_summary_guard.mjs
node frontend/apps/web/scripts/system_user_experience_shell_summary_guard.mjs
node frontend/apps/web/scripts/system_user_experience_full_browser_summary_guard.mjs
cd frontend/apps/web && node scripts/business_form_user_perspective_summary_guard.mjs
cd frontend/apps/web && node scripts/system_user_experience_shell_summary_guard.mjs
cd frontend/apps/web && node scripts/system_user_experience_full_browser_summary_guard.mjs
```

结果：

```text
coverage_guard=PASS
page_structure_guard=PASS
business_form_user_perspective=PASS caseCount=20 failures=0 missing=0 leaked=0 consoleErrors=0
system_user_experience_shell=PASS caseCount=5 failures=0 consoleErrors=0 requestFailed=0
system_user_experience_full_browser=PASS
```

## round 5 补充

已加固截图证据链：

- `business_form_user_perspective_acceptance` 每次运行前清空业务表单截图目录，避免旧截图残留影响结论。
- `business_form_user_perspective_summary_guard` 校验每个用例的 `screenshotPath` 必须真实存在且是文件。
- `system_user_experience_shell_summary_guard` 校验每个 shell 用例的 `screenshotPath` 必须真实存在且是文件。

复验命令：

```bash
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.system_user_experience.full_browser
```

结果：

```text
config_workbench=PASS assertions=64/64 journeys=10/10 actions=19/19 screenshots=9/9
system_user_experience_shell=PASS caseCount=5 failures=0 consoleErrors=0 requestFailed=0
business_form_user_perspective=PASS caseCount=20 failures=0 missing=0 leaked=0 consoleErrors=0
system_user_experience_full_browser=PASS
```

## round 6 补充

本轮开始进入真实用户视角走查，不再只看底层数据与脚本门禁。截图重点查看：

- `artifacts/playwright/system-user-experience-shell/home.png`
- `artifacts/playwright/system-user-experience-shell/project_ledger_list.png`
- `artifacts/playwright/config-workbench-operation/07-menu-config.png`
- `artifacts/playwright/business-form-user-perspective/finance_payment_apply_pay.png`
- `artifacts/playwright/business-form-user-perspective/material_inbound.png`

发现问题：

- 主导航品牌区泄漏了后端根菜单名称 `系统菜单`，用户语义不成立。
- 低代码入口区标题仍显示 `配置工作台`，与产品化后的 `配置中心` 入口口径不一致。
- 业务办理表单顶部操作区视觉权重不足，`保存草稿 / 提交 / 表单设置` 混在一起，用户不容易判断主操作。
- 日常开发静态服务 `18081` 曾被错误同步为生产构建产物，导致前端按 `sc_prod` 发起登录；清理 `dist-dev` 目录时如果删除挂载目录本身，还会导致 nginx 容器继续挂在旧 inode 上并返回 403。

已完成修复：

- `AppShell` 对后端根菜单标题做产品化兜底：空值或 `系统菜单` 统一显示应用品牌名。
- `AppShell` 管理快捷区标题统一为 `配置中心`。
- `ContractFormPage` 顶部办理操作区增加 `办理操作` 标签，强化 `提交` 主按钮权重，并把操作区收敛为清晰的页面级 action bar。
- `scripts/dev/frontend_static_build.sh` 在构建前清理输出目录内容，但保留输出目录本身，避免破坏 nginx bind mount；非生产环境继续拒绝精确 `"sc_prod"` 产物。

复验命令：

```bash
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:5174 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.system_user_experience.full_browser
ENV=dev DB_NAME=sc_demo FRONTEND_DIST_DIR=frontend/apps/web/dist-dev bash scripts/dev/frontend_static_build.sh
docker restart sc-backend-odoo-dev-nginx-1
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.system_user_experience.full_browser
```

`5174` 与 `18081` 均已通过：

```text
config_workbench=PASS assertions=64/64 journeys=10/10 actions=19/19 screenshots=9/9
system_user_experience_shell=PASS caseCount=5 failures=0 consoleErrors=0 requestFailed=0
business_form_user_perspective=PASS caseCount=20 failures=0 errors=0 consoleErrors=0
system_user_experience_full_browser=PASS
```

本轮结论：

- 本地 Vite 服务与日常开发静态服务的用户体验门禁已对齐。
- 真实走查首批问题已进入代码修复，不再停留在标准设计层。
- 后续继续按“截图走查 -> 批量归类 -> 修复 -> 双服务浏览器验收”的闭环推进。

## round 7 补充

本轮按用户反馈从“单点修补”调整为“批量结构治理”。横向查看列表页、配置页、业务表单页后，确认主要问题不是某个按钮，而是页面外壳、页面标题区、配置工作区和办理操作区的职责表达不够统一。

批量调整：

- `PageHeader` 统一升级为页面级标题和操作区，默认具备边界、背景、阴影、内边距和 action 对齐能力。
- `AppShell` 内容区统一 gutter，顶部栏吸顶，活动页签尺寸和点击区加固。
- `MenuConfigView` 配置树、编辑区、右侧操作区统一边界与宽度；继续遵守已锁定的 `--sc-product-workspace-gap: 0px`，不破坏主导航与配置工作区的无缝结构边界。
- 回收右侧操作栏吸顶方案。浏览器截图发现吸顶会覆盖底部批量维护表格，这类遮挡与用户之前反馈一致，已改为不吸顶。

复验：

```bash
make verify.system_user_experience.quick
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:5174 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.system_user_experience.full_browser
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:5174 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.business_config.config_workbench_operation_acceptance verify.business_config.config_workbench_operation_summary_guard
```

结果：

```text
quick=PASS
config_workbench=PASS assertions=64/64 journeys=10/10 actions=19/19 screenshots=9/9
system_user_experience_shell=PASS caseCount=5 failures=0 consoleErrors=0 requestFailed=0
business_form_user_perspective=PASS caseCount=20 failures=0 errors=0 consoleErrors=0
```

本轮判断：

- 这次不是扩大功能范围，而是把全系统用户页面结构向统一产品工作台推进。
- 门禁中途拦截了错误方向：配置页分栏 gap 不能私自改为 10px，必须继续走统一 0 gap 边界。
- 截图复查拦截了第二个错误方向：右侧操作栏不能吸顶覆盖底部表格。

## round 8 补充

本轮继续从“用户进入系统后是否知道该做什么”推进，不再只看外壳结构。

发现问题：

- 首页 `今天先做什么` 在风险区未显示时仍只占左侧窄列，右侧大面积留白。
- 首页今日待办卡片三列过挤，`查看详情` 被拆成竖排，影响成熟产品观感。
- 我的工作页面直接暴露 `Delivery Action Smoke / admin / TIER_REVIEW_PENDING` 等测试和技术语义。

已完成修复：

- `PageRenderer` 的角色首页 `today_focus` 区域在只有一个子块时自动跨列。
- 首页今日待办列表宽屏优先两列，按钮不换行，避免卡片压缩。
- `HomeView` 和 `MyWorkView` 增加展示层净化：付款待办统一显示为 `付款申请待审批 · PRQ...`，技术原因码转为 `待审批复核`。
- 我的工作筛选、表格和统一 PageRenderer 数据源统一改为业务化状态文案。

复验：

```bash
npm run build
make verify.system_user_experience.quick
DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:5174 E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.system_user_experience.shell_acceptance
```

结果：

```text
shell=PASS caseCount=5 failures=0 consoleErrors=0 requestFailed=0
```

截图复查：

- 首页今日待办已横向铺开，卡片两列显示，按钮不再竖排。
- 我的工作待办标题和动态标题不再泄漏测试/技术语义。

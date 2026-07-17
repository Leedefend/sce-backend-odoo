# LC-AUDIT-01 低代码产品表面全量审计

## 裁决

```text
LOW_CODE_PRODUCTIZATION = INCOMPLETE
LC-AUDIT-01 = COMPLETE_WITH_RUNTIME_AND_GOVERNANCE_BLOCKERS
LC-PRO-01 = READY_FOR_SCOPE_DEFINITION
PROD-IMG-01 = PAUSED
```

审计基线为 GitHub `main` 的 `cece6666b39cd8e7071b336f5289e440e2efde25`。本轮只增加审计工具、报告与证据，不修改前端产品代码、后端契约、权限、数据库或生产服务器。

底层能力已具备工程完整性，但管理员表面尚未形成统一的页面设计产品。现有验收可证明入口和若干编辑动作可用，不能证明统一草稿、草稿预览、影响分析、发布与回滚闭环。

## 冻结分母

后续 LC-PRO 分支不得再以四业务角色的 70 个导航叶节点代替低代码管理员分母。管理员产品分母冻结为以下内容。

### 管理员身份与权限

| 身份 | 权限来源 | 定位 | 低代码入口 |
| --- | --- | --- | --- |
| 业务配置管理员角色 | `group_sc_role_business_admin` | 可分配给用户的正式业务角色 | 通过 capability 进入工作台 |
| 业务配置管理员能力 | `group_sc_cap_business_config_admin` | 覆盖业务域 manager，明确不继承 Odoo 系统管理员 | 工作台、表单、菜单、审批及业务基础配置 |
| 行业配置管理员 | `group_sc_cap_config_admin` | 历史 XML-ID，继承业务配置管理员，承载行业/迁移治理 | 兼容身份，不作为新产品命名 |
| Smart Core 配置管理员 | `group_smart_core_business_config_admin` | P0 配置合同、版本及策略 ACL | 工作台与平台配置机制 |
| Smart Core 管理员 | `group_smart_core_admin` | 平台管理员，隐含 Smart Core 配置管理员 | 工作台和平台管理表面 |

`/admin/business-config`、`/admin/menu-config` 和 `/admin/form-field-config` 没有使用路由 `adminOnly` 元数据；其正式授权依赖菜单/action 权威和后端 intent/ACL。该设计并非直接越权，但未来验收必须同时验证“入口不可见”和“直达 API 拒绝”，不能只验证客户端路由。

### 正式入口和编辑器

| 配置对象 | 正式入口 | 实际编辑表面 | 草稿 | 预览 | 发布 | 回滚 |
| --- | --- | --- | --- | --- | --- | --- |
| 表单字段与布局 | 工作台卡片 | 跳到运行表单中的设计模式 | 组件局部 draft | 有改动时先保存发布，再回同一路由看结果 | 保存固定 `publish: true` | 工作台版本面板/表单合同版本 |
| 列表列 | 工作台内部面板 | chip 编辑器 | 面板局部 draft | 有改动时先保存发布，再打开运行页 | 保存固定 `publish: true` | 工作台版本面板 |
| 搜索/默认分组 | 工作台内部面板 | 与列表共用面板 | 面板局部 draft | 同上 | 保存固定 `publish: true` | 工作台版本面板 |
| 分析 | 工作台内部面板 | pivot/graph chip 编辑器 | 面板局部 draft | 有改动时先保存发布，再打开运行页 | 保存固定 `publish: true` | 工作台版本面板 |
| 菜单 | 独立 `/admin/menu-config` | 三栏目录/编辑器 | 页面局部 `drafts` | 以刷新正式导航验证，无隔离草稿预览 | 保存后立即刷新导航 | 独立版本面板，回滚后立即刷新导航 |
| 审批 | 工作台内部简化编辑器；另有“完整规则” | 开关、模式、步骤编排和原生完整规则两套表面 | 面板局部 draft | 展示运行状态，不提供草稿角色预览 | `configSet`/`stepsSet` 直接写正式策略 | 未形成与六类配置一致的统一版本入口 |

结论：六类配置有至少四种进入/返回模式，草稿状态分别存在于表单设计器、列表搜索、分析、审批和菜单页面；不存在工作台级 change set。当前“预览”对表单、列表和分析本质是“先发布，再查看正式运行页”，不能作为草稿预览。

### 治理能力

冻结治理分母为：页面覆盖扫描与缺口补齐、配置版本与回滚、快照导出/对比/整改计划、交付状态、运行页预览。它们均已存在，但分散在高级面板、版本面板和各独立编辑器，尚未围绕一次管理员变更形成发布任务。

## 表面与复杂度

主要实现规模：

| 文件 | 行数 | 审计结论 |
| --- | ---: | --- |
| `BusinessConfigSurfaceView.vue` | 1486 | 同时装配扫描、选择、编辑器、审批、版本、快照和导航 |
| `businessConfigSurface/style.css` | 1727 | 工作台自有完整视觉系统 |
| `MenuConfigView.vue` | 3684 | 目录、编辑、批量、版本、审计、创建/删除及全部样式同文件 |
| `ContractFormPage.vue` | 1778 | 运行表单与表单设计入口共存 |
| `useBusinessConfigFieldEditors.ts` | 533 | 列表、搜索与分析各自草稿协调 |

静态审计在低代码核心表面统计到 96 个原始 `<button>`、29 个原始 `<input>`、10 个原始 `<select>`、1 个 `<textarea>`，`Sc*` 设计系统组件使用为 0。硬编码颜色没有新增证据，但 raw control、`.ghost`、`.status`、自有 dialog/三栏布局说明 FE-PRO-04 组件目录尚未覆盖管理员表面。

工作台默认路径能隐藏部分技术词，但“高级设置”和治理面板仍直接暴露业务对象编码、action ID、view ID、role key、boundary、runtime evidence、contract count、snapshot JSON 等概念。它们应进入明确的开发者/诊断模式，并用适用页面、角色、公司、当前版本、修改人、影响用户和回滚点作为管理员主语言。

## 正式与兼容路径

正式运行权威是 `ui.business.config.contract` 及其 version，菜单运行来源同时支持正式 `ui.business.config.contract.menu_orchestration` 和兼容 `ui.menu.config.policy`。`group_sc_cap_config_admin` 是明确标注的历史 XML-ID。`/admin/form-field-config` 是兼容入口，会解析实际 action 后重定向；表单配置的正式产品入口来自工作台卡片并进入运行表单设计模式。

以下内容不得因名称含 legacy 就删除：行业配置管理员 XML-ID、菜单 policy 兼容读取和表单配置重定向仍有调用方。LC-PRO-01 只统一产品表面，不改变这些后端兼容语义。

## 高风险操作

| 操作 | 当前行为 | 产品缺口 |
| --- | --- | --- |
| 批量补齐缺失配置 | 对 form/list/search/analysis 使用 `publish: true` | 缺少统一影响清单、角色/公司范围、一次发布确认和回滚点 |
| 菜单隐藏、移动、删除、新增 | 保存后刷新正式导航 | 缺少草稿导航树、多角色预览和统一发布摘要 |
| 审批开关和步骤变化 | 直接写行业策略运行记录 | 缺少与其他配置统一的版本、差异、影响角色及发布确认 |
| 表单新增字段和字段布局 | 运行页设计器保存并发布 | 缺少草稿快照、多设备/多角色预览和跨编辑器 change set |
| 配置回滚 | 回滚立即发布为新的当前配置 | 已有确认文案，但未统一呈现发布影响和运行态验证结果 |
| 快照比较/整改计划 | JSON 输入/导出和计划下载 | 面向交付工具，未形成管理员可执行的受控导入发布流程 |

## 真实运行时证据

2026-07-17 在日常开发栈 `sc_demo`、`http://127.0.0.1:18081` 使用现有正式命令运行配置工作台操作级验收。浏览器加载入口为 `index-B6bFBa3Z.js`，HTML SHA-256 为 `d47a6db8ecce3b305dbb61971f0afaf1c39197e476460416a0eaaf10dbd64cdc`：

```text
make verify.business_config.config_workbench_operation_acceptance
```

结果为 `FAIL`：工作台可登录、选择“项目合同汇总”、切换“合同办理”并直达已选页面，四张配置卡片均存在；无 console error、无 requestfailed。但跳转到 action 562 后 60 秒内未出现 `.page .list-toolbar` 或 `.page .list-empty-state`，因此只有 3/9 截图，10 条旅程、19 个动作、64 个最终断言均未完成。独立浏览器检查确认工作台 CSS chunk 已加载、scope ID 一致，根节点计算样式为 `display:grid`、header 为 `display:flex`；截图中的工具集合观感不是 CSS 丢失造成的假象。原始证据位于：

```text
artifacts/playwright/config-workbench-operation/report.json
artifacts/playwright/config-workbench-operation/summary.json
artifacts/playwright/config-workbench-operation/01-selected-from-scan.png
artifacts/playwright/config-workbench-operation/02-switched-page.png
artifacts/playwright/config-workbench-operation/03-direct-selected.png
```

该失败不能被解释为 console/HTTP 故障，也不能据此断言具体业务根因；它证明当前日常开发站点上“工作台 → 正式运行页 → 返回/继续编辑”的完整管理员旅程没有可重复通过。LC-PRO-01 开始前应先把运行页加载超时分类为部署构建漂移、action 契约加载状态或验收等待条件之一，并保留失败证据。

现有操作级验收覆盖 1440 桌面和 390 移动端的部分路径，但没有冻结业务配置管理员的全量导航分母，也没有六编辑器 × 响应式 × light/dark × axe 的矩阵。当前不能声称低代码管理端已继承 FE-PRO-04 的宽度、无障碍和视觉专业化结论。

## 验收工具可信度

最新 main 上的低代码总入口目前不能作为可信绿色门禁：

| 检查 | 结果 | 事实 |
| --- | --- | --- |
| `verify.business_config.guard_inventory` | FAIL | 仍只解析旧 Makefile/旧单文件标记，不能识别 `make/runtime_ops.mk` 和拆分后的工作台子组件 |
| `verify.business_config.unit` | FAIL before tests | 依赖已不存在的 `scripts/verify/frontend_product_language_guard.py` |
| `business_config_user_language_guard.py` | FAIL | 仍要求 ContractFormPage 拆分前的函数片段 |
| `lowcode_config_boundary_guard.py` | FAIL | 对 Make 目标、拆分后 marker 和恢复菜单的定位仍是旧结构 |
| `backend_contract_boundary_guard.py` | PASS | 9 类允许 writer 边界清晰，无未授权 writer |
| 业务配置合同 schema | 6/6 PASS | P0 合同 schema 单测正常 |
| business config surface | 17/17 PASS | 后端 surface 单测正常 |
| menu configuration audit | 45/45 PASS | 菜单配置后端单测正常 |
| approval policy handler | 5/5 PASS | 审批配置 handler 单测正常 |

因此当前状态是“核心边界单测通过，组合门禁和源结构 guard 漂移”。LC-PRO-01 的首个前置工作应修复 guard 的文件发现与 Make include 解析，但不得通过删除断言或把失败目标变成空操作来取得绿色结果。

## 当前可完成的管理员任务

源码和既有历史验收共同证明以下能力存在：选择页面；打开四类主要配置卡片；进入表单设计；编辑列表、搜索和分析；编辑菜单和审批；查看版本；回滚配置；扫描覆盖；导出/比较快照。当前 HEAD 的真实运行时只重复证明到“选择页面和四卡片可见”，后续运行页闭环阻塞，因此本报告不把其余任务标为当前环境 PASS。

## 成熟度缺口

### P0

1. 没有统一 change set 和统一状态机：未修改、草稿、待发布、发布中、已发布、失败、回滚、运行态漂移。
2. “预览草稿”实际上会先发布，无法安全比较线上、草稿和预计发布效果。
3. 高风险操作没有跨配置对象的统一影响分析、发布确认、运行态验证和回滚点。
4. 当前日常开发站点的工作台到正式运行页旅程无法重复完成。
5. 低代码组合门禁和产品语言/边界 guard 已与拆分后的 main 源结构漂移，不能可靠证明发布就绪。

### P1

1. 六类编辑器入口、返回和保存模式不统一。
2. 技术诊断信息仍进入普通管理员信息架构。
3. 菜单与审批的版本/发布心智没有与表单、列表、搜索、分析统一。
4. 管理员导航、全表面、响应式、dark、axe、键盘操作和焦点恢复分母未冻结为机器矩阵。
5. 工作台和菜单配置未证明采用正式设计系统组件。

### P2

1. `BusinessConfigSurfaceView`、`MenuConfigView` 和工作台 CSS 仍是巨型协调/样式表面。
2. 拖拽虽有按钮替代的局部证据，但六编辑器键盘等价路径没有统一验收。
3. 快照 JSON、runtime evidence 等交付工具可用性需要独立开发者模式。

## LC-PRO-01 冻结输入

LC-PRO-01 应只做统一信息架构和编辑器容器，不改变后端配置语义：

1. 一级结构冻结为页面目录、我的草稿、待发布变更、已发布版本、配置检查。
2. 单页工作区冻结为页面目录、真实预览、属性面板、角色/公司/设备上下文和全局草稿状态。
3. 六类配置必须共享选择页面、离开保护、保存草稿、放弃、返回和状态反馈契约。
4. 技术字段迁入开发者模式；普通模式只展示适用范围、版本、修改人、时间、影响用户和回滚能力。
5. 本分支不实现统一发布；LC-PRO-02 再引入 change set、草稿预览、影响分析、发布和回滚闭环。
6. 管理员验收分母必须新增两种正式管理员身份、全部入口与六编辑器，不能复用四业务角色 70 叶结论代替。

## 可复现命令

```bash
python3 scripts/verify/low_code_product_surface_audit.py
ENV=dev DB_NAME=sc_demo make ps
ENV=dev DB_NAME=sc_demo WORKFLOW_CONTRACT_FRONTEND_URL=http://127.0.0.1:18081 \
  make verify.business_config.config_workbench_operation_acceptance
```

静态机器清单输出到 `artifacts/frontend-professional/lc-audit-01/static-inventory.json`。运行态失败不应通过修改报告或降低等待条件掩盖。

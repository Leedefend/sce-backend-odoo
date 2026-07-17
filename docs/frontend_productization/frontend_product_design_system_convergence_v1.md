# FE-PRO-04 设计系统收敛记录

## 范围与裁决

本分支只收敛视觉语义、组件责任、可访问性和正式渲染路径，不改变 ACL、record rule、角色权限、导航分母、金额公式、状态机或业务字段。共享层继续只消费正式契约；角色码、模型名、XML ID 和行业字段启发式均不得进入设计组件。

## 复杂度事实

| 文件 | 修改前 | 当前目标 | 当前结果 |
| --- | ---: | ---: | ---: |
| `AppShell.vue` | 2140 | ≤1600 | 1293 |
| `ListPage.vue` | 3222 | ≤2300 | 2086 |
| `ActionView.vue` | 3684 | 不增长 | 3684 |
| `ContractFormPage.vue` | 5587 | ≤1800 | 1778（含稳定装配与样式引用） |
| `ContractFormRoute.vue` | 不存在 | ≤800 | 18（只生成路由实例标识并装配正式页面） |
| `MyWorkApprovalWorkspace.vue` | 311 | 稳定组件迁移 | 323 |

`ContractFormPage` 的下降来自真实责任拆分：协同展示、契约语义、字段 schema、布局、表单状态、设计器状态/展示/持久化、关系字段/搜索/导航、操作 presentation、权威加载生命周期、保存与冲突动作分别进入独立模块。`RecordView` 和 `ModelFormPage` 两个无调用方代理已删除；正式 `/r` 与 `/f` 路由先进入只负责路由实例身份的 `ContractFormRoute`，随后装配同一个 1778 行正式页面。复杂度报告始终单独记录 `ContractFormPage`，不以 17 行路由组件代替核心实现规模。

整体机器指标以 FE-PRO-03 完成点 `86f9b29eb` 为基线：最大 Vue 文件 5587→3684；超过 600/1000 行 Vue 文件仍为 16/10，未伪报关闭；设计系统组件 0→23（22 个规定组件加正式 SVG 图标组件）；宽范围 `:is` 21→6；包含 raw button/status/dialog 实现的文件分别 58→57、21→20、6→4；硬编码颜色 0→0，页面 inline style literal 0→0，model-specific CSS 138→138，金额格式化实现文件 3→3。后四项只证明未增长，仍是后续按真实修改热点处理的存量债务。

## Legacy 路径裁决

| 入口 | 正式调用方 | 裁决 | 依据 |
| --- | --- | --- | --- |
| `HomeView` shared role home | 四正式角色 | KEEP_COMPATIBILITY | 薄路由入口，正式内容只有 `ContractRoleHome` |
| `MyWorkView` | 正式 `/my-work` 与 scene route | KEEP_COMPATIBILITY | 两个正式 URL 共用同一任务中心，不存在旧工作台切换参数 |
| `RecordView.vue` | 无 | REMOVE | router 已直接指向 `ContractFormPage` |
| `ModelFormPage.vue` | 无 | REMOVE | router 已直接指向 `ContractFormPage` |
| `PageRenderer` | 合法声明式页面 | KEEP_COMPATIBILITY | 仍有正式页面调用，安全 fallback 只显示产品化错误 |
| `/a/:actionId` 与 `ModelListPage` | 70 个正式叶节点 | KEEP_COMPATIBILITY | 正式 action/list 入口仍依赖，缺少 action_id 时只进入产品化错误状态 |
| `/f/:model/:id` 与 `/r/:model/:id` | J12/J13 与正式 deep link | KEEP_COMPATIBILITY | 两条 URL 统一装配 `ContractFormRoute`/`ContractFormPage`，不再切换旧 renderer |
| query 参数切换旧 Home/My Work/Record/Form | 无 | REMOVE | 正式 router 不存在 legacy renderer query switch，守卫禁止回流 |
| `/workbench` | 诊断人员显式直达 | KEEP_INTERNAL_ONLY | 不在四正式角色导航与 70 叶节点中出现，保留诊断用途 |
| 管理员诊断入口 | 显式管理员开关 | KEEP_INTERNAL_ONLY | 普通角色默认不加载原始诊断数据 |
| 旧按钮、状态、dialog、empty state | 分散正式调用方 | KEEP_COMPATIBILITY | 本分支迁移稳定高频路径；剩余 raw 实现按机器指标登记，不在缺少逐页视觉证据时批量删除 |

## 自定义金额字段

字段契约 `required=true` 现在映射为可见输入的 `aria-required=true`；校验失败映射 `aria-invalid=true`，并通过 `aria-describedby` 同时关联帮助与错误。错误摘要使用稳定 field key 聚焦真实金额输入。`0` 保持合法数值，`null` 表示未填写；未增加隐藏 required input，也未在前端重算金额。

## 证据

- 静态边界：`scripts/verify/frontend_style_system_guard.py`
- Legacy 守卫：`scripts/verify/frontend_page_legacy_renderer_residue_guard.py`
- 视觉矩阵：`artifacts/frontend-professional/fe-pro-04/final-report.json`
- 视觉结构比较：`artifacts/frontend-professional/fe-pro-04/visual-regression-report.json`
- 复杂度与重复实现：`artifacts/frontend-professional/fe-pro-04/complexity-report.json`
- 金额 required 探针：`artifacts/frontend-professional/fe-pro-03/final-report.json`

视觉报告记录 route、role、company、viewport、theme、组件契约版本、git SHA、截图 hash、console/pageerror、axe 和横向溢出。动态文本不以整图字节相等作为唯一判定。

## 验收结论

- required 金额探针：付款申请 create 从 `NOT_APPLICABLE` 收敛为真实 `PASS`，覆盖 required、invalid、describedby、错误摘要聚焦、0/null。
- 正式设计契约：语义色彩、字体、4/8 像素间距、圆角/阴影/边框和单一 SVG 图标来源由 design-system token 与 style guard 冻结。
- 正式组件目录：规定的 22 个 `Sc*` 产品组件均存在并有正式页面消费者，另有 `ScIcon` 作为受控图标入口；组件不读取角色码、模型名或 XML-ID。
- 视觉矩阵：18 个代表页面覆盖 1440、1280、768、390 四种尺寸和 light；dark 采样覆盖首页、My Work、列表、详情、表单、dialog、错误状态。
- 页面质量：一个 H1、一个 main、技术词、横向溢出、console/pageerror 与 axe critical/serious 均作为阻断字段记录。
- 回归旅程：J02–J13 全部通过；70/70 导航保持 finance 42、project member 9、PM 14、owner 5；action 876/menu 606 继续拒绝。

分支最终 CI、双远端同步、PR quality gate 和 merge SHA 属于交付态事实，在合并完成后由 PR 与最终交付报告记录，不在合并前预写占位值。

## 已知存量债务

超过 600/1000 行的 Vue 文件数量仍为 16/10，`ActionView.vue` 仍为 3684 行，model-specific CSS 与重复金额格式化实现仅做到不增长。它们是明确登记的存量债务，不影响本分支的强制前置项关闭，也不得用薄代理文件宣称已经消失。

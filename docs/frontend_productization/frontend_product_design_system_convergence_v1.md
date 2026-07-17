# FE-PRO-04 设计系统收敛记录

## 范围与裁决

本分支只收敛视觉语义、组件责任、可访问性和正式渲染路径，不改变 ACL、record rule、角色权限、导航分母、金额公式、状态机或业务字段。共享层继续只消费正式契约；角色码、模型名、XML ID 和行业字段启发式均不得进入设计组件。

## 复杂度事实

| 文件 | 修改前 | 当前目标 | 当前结果 |
| --- | ---: | ---: | ---: |
| `AppShell.vue` | 2140 | ≤1600 | 1292 |
| `ListPage.vue` | 3222 | ≤2300 | 2083 |
| `ActionView.vue` | 3684 | 不增长 | 3684 |
| `ContractFormPage.vue` | 5587 | ≤1800 | 1779（含稳定装配与样式引用） |
| `MyWorkApprovalWorkspace.vue` | 311 | 不增长 | 311 |

`ContractFormPage` 的下降来自真实责任拆分：协同展示、契约语义、字段 schema、布局、表单状态、设计器状态/展示/持久化、关系字段/搜索/导航、操作 presentation、权威加载生命周期、保存与冲突动作分别进入独立模块。`RecordView` 和 `ModelFormPage` 两个无调用方代理已删除；正式 `/r` 与 `/f` 路由均直接进入同一页面实现。

## Legacy 路径裁决

| 入口 | 正式调用方 | 裁决 | 依据 |
| --- | --- | --- | --- |
| `HomeView` shared role home | 四正式角色 | KEEP_COMPATIBILITY | 薄路由入口，正式内容只有 `ContractRoleHome` |
| `MyWorkView` | 正式 `/my-work` 与 scene route | KEEP_COMPATIBILITY | 两个正式 URL 共用同一任务中心，不存在旧工作台切换参数 |
| `RecordView.vue` | 无 | REMOVE | router 已直接指向 `ContractFormPage` |
| `ModelFormPage.vue` | 无 | REMOVE | router 已直接指向 `ContractFormPage` |
| `PageRenderer` | 合法声明式页面 | KEEP_COMPATIBILITY | 仍有正式页面调用，安全 fallback 只显示产品化错误 |
| 管理员诊断入口 | 显式管理员开关 | KEEP_INTERNAL_ONLY | 普通角色默认不加载原始诊断数据 |

## 自定义金额字段

字段契约 `required=true` 现在映射为可见输入的 `aria-required=true`；校验失败映射 `aria-invalid=true`，并通过 `aria-describedby` 同时关联帮助与错误。错误摘要使用稳定 field key 聚焦真实金额输入。`0` 保持合法数值，`null` 表示未填写；未增加隐藏 required input，也未在前端重算金额。

## 证据

- 静态边界：`scripts/verify/frontend_style_system_guard.py`
- Legacy 守卫：`scripts/verify/frontend_page_legacy_renderer_residue_guard.py`
- 视觉矩阵：`artifacts/frontend-professional/fe-pro-04/final-report.json`
- 金额 required 探针：`artifacts/frontend-professional/fe-pro-03/final-report.json`

视觉报告记录 route、role、company、viewport、theme、组件契约版本、git SHA、截图 hash、console/pageerror、axe 和横向溢出。动态文本不以整图字节相等作为唯一判定。

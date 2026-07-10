# 页面模式规范 v1

## 1. 目的

统一页面语义，避免所有场景都呈现为“万能页面”。本规范服从 `docs/product/product_page_structure_design_v1.md`，页面模式只表达产品任务意图，不能混入实现组件、路由路径或布局类型。

页面模式固定为六类：

| 模式 | 产品目标 | 典型页面 |
| --- | --- | --- |
| `dashboard` | 10 秒内看清状态、风险、下一步 | 角色首页、项目驾驶舱、经营分析 |
| `workspace` | 在一个业务域内连续处理任务 | 我的工作、风险中心、配置工作台、项目台账工作区 |
| `list` | 高效浏览、筛选、排序、批量处理 | 合同台账、任务列表、业务基础数据 |
| `form` | 完成单据录入、审批、保存 | 合同办理、支付申请、项目立项 |
| `detail` | 阅读单个对象详情和历史 | 项目详情、合同详情、附件详情 |
| `admin` | 配置系统规则和发布结果 | 菜单配置、配置中心、发布管理 |

## 2. 模式边界

### 2.1 dashboard

- 产品目标：在 10 秒内回答“现在状态如何、风险在哪、下一步做什么”。
- 页面骨架：Page Header + Summary Strip + 分区卡片。
- 不承载连续编辑任务，不把配置动作放进驾驶舱。

### 2.2 workspace

- 产品目标：支持角色在一个业务域内连续处理任务。
- 页面骨架：Page Header + 范围动作 + 工作区。
- `layout.kind=ledger` 只表示工作区内部布局，不是页面模式；页面模式仍归为 `workspace`。

### 2.3 list

- 产品目标：稳定、高效地进行台账式浏览、筛选、排序与批量处理。
- 页面骨架：Page Header + Toolbar + Table + Pagination。
- 批量动作靠近列表，不进入 Header。

### 2.4 form

- 产品目标：完成业务录入、审批、保存或提交。
- 页面骨架：Page Header + 状态/主动作 + 表单分区。
- 配置态动作不能混入业务办理表单。

### 2.5 detail

- 产品目标：阅读单个对象详情、状态、历史和关联信息。
- 页面骨架：Page Header + Summary + Tabs/Sections。
- 不承担批量管理和系统配置职责。

### 2.6 admin

- 产品目标：配置系统规则、检查发布结果、支持回滚。
- 页面骨架：Page Header + 管理工具区 + 可审计主内容。
- 配置动作必须携带配置对象，例如“保存菜单配置”，不能使用泛化动作。

## 3. 核心页面归类

- `project.management` -> `dashboard`
- `my_work.workspace` -> `workspace`
- `risk.center` -> `workspace`
- `projects.ledger` -> `workspace`，其中 `layout.kind=ledger` 只驱动项目群台账布局和概览条。
- `projects.list` / `task.center` / `cost.project_boq` -> `list`
- 合同办理、支付申请、项目立项等业务录入页 -> `form`
- 单对象详情页 -> `detail`
- 菜单配置、配置中心、发布管理 -> `admin`

## 4. 前端消费方式

### 4.1 归一化来源

前端使用 `resolvePageMode(sceneKey, layoutKind)` 归一化页面模式：

- `project.management` / `projects.dashboard` -> `dashboard`
- `layout.kind=list` -> `list`
- `layout.kind=ledger|workspace` -> `workspace`
- 默认 -> `workspace`

`ledger` 不允许作为 `PageMode` 返回值。需要项目台账特殊视觉时，应读取 `layout.kind=ledger`，不能扩展页面模式。

### 4.2 DOM 证据

正式页面必须在运行时 DOM 暴露 `data-product-page-mode`。允许值只能是：

```text
dashboard / workspace / list / form / detail / admin
```

该证据由 `make verify.product.page_structure` 和配置工作台浏览器验收共同守住。

## 5. 后续演进

- 在 scene payload 的 page 节点中统一补充 `page_mode`，减少推断。
- 在 page contract 里补充 mode-specific render hints。
- 将模式作为页面结构、操作验收和专业产品 ready 结论的共同输入。

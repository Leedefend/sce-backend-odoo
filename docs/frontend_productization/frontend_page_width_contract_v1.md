# FE-PRO-04W 页面宽度契约验收

## 结论

列表、详情、表单和工作台原先由多个页面层分别决定宽度，导致相同主内容区的利用率不一致。FE-PRO-04W 将页面宽度收敛为设计系统能力：页面编排只能选择通用宽度模式，页面组件不再私有决定页面级 `max-width`。

## 正式契约

| 模式 | 通用页面语义 | 上限 |
| --- | --- | ---: |
| `data` | list、report、table、workbench | 1920px |
| `standard` | record detail、record edit、未知页面 | 1440px |
| `focused` | record create、聚焦录入 | 1080px |
| `fluid` | 契约明确声明的特殊可视化 | 无上限 |

解析优先级为：后端正式 `layout.width_mode` → 路由通用 `page kind` → 安全默认 `standard`。实现不读取模型名、XML-ID、菜单文案、字段、角色、公司或账号。

`ScPage` 与 `LayoutShell` 共同消费 `PageWidthMode`，唯一 CSS 页面框架权威为 `styles/product-patterns.css:.sc-page-frame`。响应式页面 padding 使用 32px、24px、16px token；页面框架统一负责宽度、居中和 `min-width: 0`。

## 宽度证据

带 236px 侧栏时的最终结果：

| viewport | data | standard | focused | mobile |
| --- | ---: | ---: | ---: | ---: |
| 1440×900 | 1160 / 100% | 1160 / 100% | 1080 / 93.10% | — |
| 1920×1080 | 1640 / 100% | 1440 / 87.80% | 1080 / 65.85% | — |
| 2560×1440 | 1920 / 84.21% | 1440 / 63.16% | 1080 / 47.37% | — |
| 390×844 | 350 / 100% | 350 / 100% | 350 / 100% | 16px 内容 padding |

表中数据为 `frame width / main region utilization`。2560 下各受限模式左右留白对称：data 180/180px、standard 420/420px、focused 600/600px。

## 表格与嵌套宽度

列表标题、筛选、批量操作、表格和分页共享同一 data frame。表格容器由无条件 `overflow-x: scroll` 改为 `auto`，页面级横向溢出为 0；宽列仅在表格容器内按内容产生局部滚动，390px 移动卡片模式不泄漏桌面表格。

嵌套宽度审计结果：PAGE_FRAME 3、COMPONENT_INTERNAL_WIDTH 31、LEGACY_OVERRIDE 0、UNRESOLVED 0。说明文字和 dialog/drawer 等内部尺寸不拥有页面框架宽度。

## 视觉与运行时验收

最终矩阵覆盖 10 个代表页面 × 4 个 viewport，共 40 张 light 截图；另采集 5 张 dark 截图。结果：

- axe critical/serious：0；
- 页面级横向溢出：0；
- console/pageerror：0；
- 非预期 HTTP 错误：0；
- 40 个 light 场景的 width mode、frame、内容宽度、表格滚动和截图 hash 均已记录。

证据位于 `artifacts/frontend-professional/fe-pro-04w/baseline-report.json`、`artifacts/frontend-professional/fe-pro-04w/final-report.json` 和对应截图目录。

## 架构守卫

`frontend_page_width_contract_guard.py` 阻止重复页面宽度权威、按模型或角色推断模式、列表固定 1440px、无条件表格滚动、页面级隐藏溢出以及未知值回退为 fluid。未知模式始终回退到 `standard`。

## 回归结果

- J02–J13：PASS；
- 导航与角色计数：70/70，finance 42、project member 9、PM 14、owner 5；
- action 876 / menu 606 拒绝、A→B→A、Project A 隔离：PASS；
- required 金额探针：PASS，`aria-required=true`、`aria-invalid=true`、错误描述关联和错误摘要聚焦均有效；
- delivery hardening：72 个响应式场景 PASS，原性能预算复跑 PASS；
- frontend lint、strict typecheck、production build、`git diff --check`：PASS；
- `make ci.local.quick`：PASS；
- 唯一一次完整 `make ci`：PASS，CI 后生成物独立 stale 守卫 PASS。

复杂度约束：AppShell 1293（不变）、ListPage 2085（-1）、ActionView 3684（不变）、ContractFormPage 1778（-1）、MyWorkApprovalWorkspace 323（不变）。没有新增大型组件或巨型替代文件。

## 范围

本分支未修改 ACL、record rule、导航分母、角色权限、业务字段、金额公式、状态机、列表查询、表格业务列、fixture 或生产服务器，也未新增 model-specific CSS、硬编码颜色或 inline style。

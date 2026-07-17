# FE-PRO-04WR 统一业务工作区与核心内容宽度

## 结论

FE-PRO-04W 统一了宽度计算机制，但仍让列表、详情/编辑、创建分别选择 1920、1440、1080 的外框，因此用户在页面切换时仍会看到主体边界跳动。FE-PRO-04WR 将契约修正为两层：统一 Workspace Frame 决定页面可见外框，Content Layout 只决定工作区内部排布。

日常开发站点在修改前已证明加载最新 main：source SHA `95a90d8964013bc375f7807230d06f7554d7b492`，index SHA256 `a8948c68847aa777f6c14e77de2204f7bac0f366bb106e736d3c79bbbab2eeca`，浏览器 chunk `assets/index-Bop99CdW.js`。因此根因是正式契约，不是部署缓存。

## 实际 DOM 基线

1920×1080、236px 展开侧栏下，修改前的外框为：

| 页面类型 | x | right | width |
| --- | ---: | ---: | ---: |
| 列表 | 258 | 1898 | 1640 |
| 详情/编辑 | 358 | 1798 | 1440 |
| 付款申请创建 | 538 | 1618 | 1080 |

基线来自真实浏览器 bounding box，而非源码推测。证据位于 `artifacts/frontend-professional/fe-pro-04wr/baseline-dom.json` 和 `baseline/`。

## 两层正式契约

第一层 `WorkspaceFrameMode = 'business'`：所有 Home、My Work、Action/List、Record detail/edit/create 和产品状态页统一使用 `width: 100%`、`max-width: 1920px`、相同响应式 padding、居中规则与 `min-width: 0`。`ScPage` 与 `LayoutShell` 不再接收或解析外框宽度模式。

第二层 `ContentLayoutMode`：

| 模式 | 内部责任 |
| --- | --- |
| `data-grid` | 工具栏和表格使用全部工作区 |
| `record-grid` | 详情事实区响应式排布 |
| `form-grid` | 编辑表单响应式分组网格 |
| `focused-form` | 操作聚焦；分组画布保持全宽，字段在响应式 2–3 列网格中控制可读宽度 |
| `reading` | 只限制长文本阅读行宽 |

正式 `layout.content_layout_mode` 优先，其次使用通用 page kind，未知页面安全回退 `record-grid`。实现不读取模型、XML-ID、角色、公司、账号、中文标签或字段名来决定布局。

## 列表和表单布局

列表采用 `table used width = max(container width, required columns width)`。列宽角色来自 presentation contract 的 primary identity、`cellRole` 与字段类型；identity/description 吸收剩余空间，status/date/money/actions 保持稳定宽度。最小所需列宽施加在滚动容器内部的 `<table>`，滚动容器自身保持工作区宽度；少列填满容器，多列只产生局部横向滚动。

表单外框、标题、错误摘要、主 surface、分组画布和操作栏与列表同边界。FE-PRO-04WR2 起，`focused-form` 不再对整个字段 canvas 设置 1080px 上限；分组内部按容器宽度使用 2–3 列，字段跨度来自正式 layout/presentation 契约，390px 统一单列。阅读行宽限制只用于长说明或明确的 reading 内容。

全局 `.router-host` 不再使用 `overflow-x: clip`。验收脚本直接检查 document 与 router 内所有可见子元素；只豁免具有明确 `overflow-x:auto|scroll` 的局部表格容器，不能把裁切视为通过。

## 最终 DOM 对齐

八个正式页面在相同 Shell 状态下的外框、标题和主内容左右边界差值均为 0px：

| viewport / 侧栏 | frame width | frame x/right spread | header x/right spread | primary x/right spread | overflow |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1440×900 / 展开 | 1160 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| 1920×1080 / 展开 | 1640 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| 1920×1080 / 折叠 | 1876 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| 2560×1440 / 展开 | 1920 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| 390×844 | 350 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |

1920 展开侧栏时，八页 frame 均为 x=258、right=1898；标题与主内容均为 x=290、right=1866。2560 下 frame 上限 1920 且左右留白对称。document overflow 与 router child overflow 均为 0。

## 视觉和回归证据

最终矩阵为八页 × 1440/1920/2560/390，加八页 1920 折叠侧栏，共 40 张 light；另有列表、详情、编辑、创建、错误状态 5 张 dark。axe critical/serious、console/pageerror、非预期 HTTP、页面溢出、router 子元素溢出、边界对齐失败和表格利用率失败均为 0。证据位于 `artifacts/frontend-professional/fe-pro-04wr/final-report.json` 和 `final/`。

回归结果：J02–J13 PASS；70/70（finance 42、project member 9、PM 14、owner 5）；action 876/menu 606 拒绝、公司 A→B→A、Project A 隔离、required 金额探针、409、dirty guard 与关系链均 PASS。required 金额探针记录 `aria-required=true`、`aria-invalid=true`、错误关联和聚焦成功。

工程门禁：frontend lint、strict typecheck、production build、`git diff --check`、`make ci.local.quick` 及唯一一次完整 `make ci` 均 PASS；完整 CI 后 generated reports stale 守卫单独 PASS。

## 范围与已知问题

本轮未修改 ACL、record rule、角色权限、导航分母、业务字段、金额公式、状态机、列表查询、表格业务列、fixture 或生产服务器；未新增 model-specific CSS、硬编码颜色或按模型/角色布局推断。

兼容纠正：PR #1093 合并时虽然存在旧值映射表，但契约提取函数尚未读取 `layout.width_mode`，所以当时“旧字段已兼容”的表述不成立。FE-PRO-04WR1 才真正从 root/page/presentation 三个 layout 位置读取旧字段；新 `content_layout_mode` 始终优先，旧字段只解释为内部 Content Layout，永远不能改变 Workspace Frame。

该兼容层不是永久正式 API。后端契约应逐步改发 `layout.content_layout_mode`；退出条件是受支持历史数据库完成契约迁移、只读扫描连续两个发布周期为零，并且仓库与外部部署自动化不再依赖 `width_mode`。局部关系表在移动端仍可在自身容器内滚动，但不会越出 router 或产生页面级滚动。

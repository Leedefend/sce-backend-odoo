# FE-PRO-04WR2 宽屏表单画布契约

## 结论

FE-PRO-04WR2 只修复统一 Workspace Frame 内部的表单画布。外层 `business` Workspace Frame、列表页面和表格列宽算法均保持不变。

修改前，`focused-form` 通过 `--sc-content-focused-form-max: 1080px` 限制整个创建表单画布。1920/2560 展开侧栏时，付款申请和合同创建画布利用率分别只有 70.13%/59.34%，右侧无意义空白为 459/739px。

修改后，表单画布和业务分组使用全部主内容可用宽度；字段格控制单字段可读宽度：

| 可用容器宽度 | 默认布局 |
| --- | --- |
| 小于 680px | 1 列 |
| 680px–1239px | 最多 2 列 |
| 1240px 及以上 | 最多 3 列 |

列数上限继续消费正式分组 `columns` 契约，不按模型、角色、字段名或中文标签推断。

## 字段跨度

正式字段布局语义为 `compact / normal / wide / full`：`compact` 与 `normal` 占一列，`wide` 在多列容器占两列，`full` 占整行。历史 `large` 保留为 full-span 大输入兼容语义。契约缺失时，普通单行控件使用 `normal`；text/html、x2many 使用通用控件类型的 `full` 安全默认。

## 浏览器证据

当前 HEAD 生成 48 张 light 截图（8 页面 × 5 尺寸，加 8 张 1920 侧栏折叠证据）和 5 张 dark 截图。机器报告位于 `artifacts/frontend-professional/fe-pro-04wr2/final-report.json`。

代表性结果：

| viewport | canvas utilization | section utilization | 默认列数 | 最大普通字段 wrapper | 右侧空白 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1440×900 | 99.81% | 97.16% | 2 | 502px | 1px |
| 1920×1080 | 99.87% | 98.05% | 3 | 486.67px | 1px |
| 2560×1440 | 99.89% | 98.35% | 3 | 580px | 1px |
| 768×1024 | 99.70% | 96.12% | 1 | 644px | 1px |
| 390×844 | 99.32% | 内边距内 100% | 1 | 266px | 1px |

所有采样的 document overflow、业务内容 router child overflow、axe critical/serious、console/pageerror 和非预期 HTTP 均为 0。固定定位 dialog overlay 不计为 router 内容越界；其面板继续由 `ScDialog` 自身管理。

## 守卫

`verify.frontend.form_canvas_layout.guard` 阻止 1080px 画布限制回归、字段名跨度猜测、模型/角色列数判断和 overflow 掩盖。浏览器审计同时门禁画布利用率、桌面分组利用率、普通字段 720px 上限、390 单列与运行时错误。

列表生产文件在本分支保持零 diff；低记录数产生的视觉空余仍分类为 `LOW_ROW_COUNT_VISUAL_STATE`，不通过改变列表宽度或伪造数据处理。

## 回归结果

- J02–J13：PASS。
- 导航叶节点：70/70（finance 42、project member 9、PM 14、owner 5）。
- required 金额、409 恢复、dirty guard、关系搜索、x2many、公司 A→B→A 和 logout/login 隔离：PASS。
- lint、strict typecheck、production build、`make ci.local.quick`、单次完整 `make ci`：PASS。
- `ListPage.vue` / `ListPage.css` 相对本分支基线：零生产 diff。

## WR3：单列 wide 隐式轨道修复

WR2 最初在 `min-width: 680px` 容器查询中使用未限定父 grid 的 `.field--wide { grid-column: span 2; }`。当正式分组声明 `columns=1` 时，浏览器为 wide 字段创建第二条0px隐式轨道。WR3把该规则限定为 `columns-2/columns-3 > field--wide`，并显式保护columns-1的wide/full始终使用 `1 / -1`。生产CSS改动为新增6行、删除3行，断点、Workspace Frame和业务页面均未改变。

1920宽度下的12项正式矩阵：

| columns | span | computed tracks | computed column | implicit tracks | overflow |
| ---: | --- | ---: | --- | ---: | ---: |
| 1 | compact | 1 | span 1 | 0 | 0 |
| 1 | normal | 1 | span 1 | 0 | 0 |
| 1 | wide | 1 | 1 / -1 | 0 | 0 |
| 1 | full | 1 | 1 / -1 | 0 | 0 |
| 2 | compact | 2 | span 1 | 0 | 0 |
| 2 | normal | 2 | span 1 | 0 | 0 |
| 2 | wide | 2 | span 2 | 0 | 0 |
| 2 | full | 2 | 1 / -1 | 0 | 0 |
| 3 | compact | 3 | span 1 | 0 | 0 |
| 3 | normal | 3 | span 1 | 0 | 0 |
| 3 | wide | 3 | span 2 | 0 | 0 |
| 3 | full | 3 | 1 / -1 | 0 | 0 |

浏览器计算同时覆盖639、680、1239、1240、1920五个容器宽度，共60项，失败0。基线在680及以上的四个columns=1+wide场景均检测到1条隐式轨道；修复后均为0。测试fixture生成columns=1 wide/full、columns=2 wide、columns=3 wide及390单列截图，不进入生产模块或数据库。

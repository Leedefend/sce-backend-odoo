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

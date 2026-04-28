# 应收应付报表（项目）最终可用性复核 Batch-N

## 1. 批次定位

- Layer Target：Domain Projection / Frontend Contract Audit
- Module：`addons/smart_construction_core`、`frontend/apps/web`
- Reason：Batch-L/M 已修复 `SJKYYE` 项目级余额覆盖和 `SF` 项目级抵扣比例口径，需要确认旧库 27 字段在模拟生产运行库与自定义前端契约消费链中均可查看、可解释、可重建。

## 2. 运行库覆盖结论

运行库：`sc_prod_sim`

- 报表行数：`11696`
- 覆盖项目：`814`
- 覆盖往来单位键：`7258`
- 旧库项目资金余额事实缺失项目：`0`
- “项目级余额”补漏行：`56`
- 非零项目级抵扣比例行：`7471`
- 非零项目级抵扣比例项目：`315`

27 字段结论：

- 字段承载：已闭环
- 项目级余额覆盖：已闭环
- 抵扣比例旧库口径：已闭环
- 当前剩余风险：比例和实际可用余额是项目级指标，不应在透视或导出后按行简单求和

## 3. 关键字段覆盖

| 字段 | 覆盖结果 |
| --- | ---: |
| 收入合同金额 | `744` 行，合计 `3142399070.99` |
| 已开票 | `671` 行，合计 `47602317362.22` |
| 已收款 | `814` 行，合计 `480379794.04` |
| 未收款 | `1555` 行，合计 `2662019276.95` |
| 已开票未收款 | `664` 行，合计 `47472912552.33` |
| 已收款未开票 | `775` 行，合计 `350974984.15` |
| 应付合同金额 | `3881` 行，合计 `2402859650.36` |
| 计价方式 | `3412` 行 |
| 已付款 | `5950` 行，合计 `2147431936.05` |
| 已收供应商发票 | `7206` 行，合计 `2642686733.21` |
| 未付款 | `2481` 行，合计 `623636160.51` |
| 付款超票 | `634` 行，合计 `128381363.35` |
| 销项税额 | `734` 行，合计 `177414371.67` |
| 进项税额 | `3780` 行，合计 `114112494.93` |
| 抵扣税额 | `1864` 行，合计 `56009185.14` |
| 抵扣比例 | `7471` 行，覆盖 `315` 个项目 |
| 实际可用余额 | `10498` 行，覆盖 `513` 个非零余额项目；另有 `56` 条项目级余额补漏行 |
| 自筹收入金额 | `569` 行，合计 `219525590.83` |
| 自筹退回金额 | `370` 行，合计 `143229174.39` |
| 自筹未退金额 | `415` 行，合计 `76296416.44` |
| 销项附加税 | `730` 行，合计 `20595859.4964` |
| 进项附加税 | `3594` 行，合计 `13328329.2112` |
| 抵扣附加税 | `592` 行，合计 `1759613.9436` |

## 4. 自定义前端契约消费复核

使用真实业务配置管理员 `wutao` 验证：

- `load_view(model=sc.ar.ap.project.summary, view_type=tree)`：PASS
- 列数：`25`
- 权限：`read=true, write=false, create=false, unlink=false`
- 关键列存在：
  - `partner_name`
  - `payable_pricing_method_text`
  - `tax_deduction_rate`
  - `actual_available_balance`
- 关键字段标签存在：
  - `往来单位`
  - `计价方式`
  - `抵扣比例`
  - `实际可用余额`
- `api.data` 可读取项目级余额行：`56` 条
- `api.data` 可读取非零抵扣比例行：`7471` 条

前端代码路径复核：

- `ActionView.vue` 将后端契约列传入 `ListPage`
- `ListPage.vue` 按 `columns` 和 `column-labels` 通用渲染
- `actionViewLoadViewFieldStateRuntime.ts` 按契约列生成读取字段
- `actionViewRequestRuntime.ts` 将契约列、隐藏列和用户偏好合并为请求字段
- 未发现针对应收应付项目报表的字段硬编码

## 5. 验证命令

- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec`：PASS，输出 `AR_AP_PROJECT_FINAL_COVERAGE`
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim MVP_MODEL=sc.ar.ap.project.summary E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.portal.tree_view_smoke.container`：主链 PASS，通用分组基线 mismatch；原因是该 target 固定对比 `project.project` 基线，不适合作为本报表阻断项
- `corepack pnpm -C frontend/apps/web typecheck:strict`：PASS
- `corepack pnpm -C frontend/apps/web build`：PASS，存在 Vite chunk size warning
- 直接 `load_view + api.data` 契约审计：PASS

## 6. 剩余风险

- P2：`actual_available_balance` 和 `tax_deduction_rate` 都是项目级指标，在多往来单位行上重复展示；列表可读，透视/导出后不应按行简单求和。
- P2：通用 `verify.portal.view_contract_shape.container` 对 tree 视图按 form layout 断言，会误报 `layout missing`；后续应补专门的 tree/list contract shape target。
- P2：`verify.portal.tree_view_smoke.container` 的 grouped signature baseline 仍绑定 `project.project` 样本，应用于新报表会误报 baseline mismatch；后续应支持按模型生成独立基线。

## 7. 结论

应收应付报表（项目）已达到旧库 27 字段业务事实层可用：字段可见、数据可读、缺口可解释、历史事实可重建。下一步建议进入用户可读性优化：对项目级指标增加页面说明或列提示，并为该报表补专用前端契约 smoke。

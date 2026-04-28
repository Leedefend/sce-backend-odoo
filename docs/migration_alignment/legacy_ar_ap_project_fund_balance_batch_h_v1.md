# 应收应付报表（项目）实际可用余额 Batch-H

## 1. 批次定位

- Layer Target：业务事实分析层 / Domain Projection
- Module：`addons/smart_construction_core`、`scripts/migration`
- Reason：旧库“应收应付报表（项目）”包含 `SJKYYE` 实际可用余额。该字段来源于项目资金汇总视图，不属于往来单位维度明细，必须先作为项目级资金余额事实承载，再投影到报表。

## 2. 旧库事实

旧库字段来自 `View_Select_XMCKXX_BS`：

- `SJKYYE = LJSK_SJ + WLZJ - LJFK - ZTZJ`
- `ZMYE` 与 `SJKYYE` 在旧视图中公式一致
- `UP_USP_SELECT_YSYFHZB_XM` 通过 `TOP 1` 按项目取 `SJKYYE`，并在往来单位行上重复展示

旧库抽取结果：

- 项目行数：755
- `SJKYYE` 合计：`-2,586,337.86`
- `LJSK_SJ` 合计：`2,213,547,483.45`
- `WLZJ` 合计：`60,349,762.95`
- `LJFK` 合计：`2,266,667,336.33`
- `ZTZJ` 合计：`9,816,247.93`

## 3. 新系统承载判断

`project.project.funding_remaining_amount` 不是旧库 `SJKYYE`：

- 新字段口径：资金计划/额度 - 待支付/已支付保留
- 旧字段口径：实际收款 + 外来资金 - 累计付款 - 在途资金

因此本批新增 `sc.legacy.project.fund.balance.fact`，作为项目资金余额历史事实载体，并保留旧库拆分金额，避免把旧库公式硬塞到项目主模型。

## 4. 报表投影规则

`sc.ar.ap.project.summary.actual_available_balance` 从项目资金余额事实按 `project_id` 关联。

该字段是项目级属性，在旧报表中只是跟随往来单位行重复展示，所以：

- 列表显示 `实际可用余额`
- 搜索支持 `实际可用余额为负`
- tree 字段不设置 `sum`，避免按往来单位重复求和

## 5. 重建链路

新增可重复执行入口：

```bash
make fresh_db.legacy_project_fund_balance.replay.adapter
make fresh_db.legacy_project_fund_balance.replay.write
```

一键重建链路新增 step：

- `legacy_project_fund_balance_adapter`
- `legacy_project_fund_balance_replay`

支持断点执行：

```bash
DB_NAME=<target_db> HISTORY_CONTINUITY_START_AT=legacy_project_fund_balance_adapter \
  HISTORY_CONTINUITY_STOP_AFTER=legacy_project_fund_balance_replay \
  make history.continuity.replay
```

## 6. 模拟生产验证

- adapter：PASS，抽取 755 行，`actual_available_balance=-2,586,337.86`
- write：PASS，写入 755 行，缺项目 0 行
- fact 校验：
  - 事实行数：755
  - 非零项目：513
  - `actual_available_balance` 合计：`-2,586,337.86`
- AR/AP 投影校验：
  - 报表非零余额行：10132
  - 项目级去重后覆盖：512 个项目
  - 与事实表共同项目金额一致，差异项目 0 个

未进入 AR/AP 投影的 1 个项目：

- `德新镇污水处理厂及污水收集主管网建设（德新镇污水处理厂工程）`
- 旧项目 ID：`b68df914cf3b47b888e43028b1057da1`
- 实际可用余额：`189,710.57`
- 原因：项目资金余额事实存在，但当前应收应付项目报表没有该项目的往来单位业务行作为明细承载。

## 7. 风险与回滚

- P1：AR/AP 报表是往来单位明细报表，项目级余额在多行重复展示，用户导出后自行求和会得到错误结果。
- 缓解：tree 不提供 sum；后续如需要总余额，应在项目资金报表或资金看板中按项目汇总展示。
- 回滚：删除 `sc.legacy.project.fund.balance.fact` 中 `import_batch=legacy_project_fund_balance_v1` 行，回退本批提交并升级 `smart_construction_core`。

## 8. 下一批次

继续拆旧库“应收应付报表（项目）”剩余字段，优先判断字段是真正往来单位维度、项目维度，还是需要独立资金/经营分析报表承载。

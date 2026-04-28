# 账户收支统计表承载审计 Batch-Q

## 1. 报表定位

- 旧报表：账户收支统计表
- 优先级：P0
- 使用证据：1549 clicks，10 users，last 2026-04-10
- 旧过程：`Report_SP_USP_Select_ZHSZTJB_GS_Tree`
- Layer Target：Domain Projection Audit
- Module：`docs/migration_alignment`
- Reason：该报表是旧库第二高频统计报表，当前清单标记为 `partial`，需要先确认数据条件和限制，再决定是否建新聚合。

## 2. 旧过程事实

旧过程参数：

- `@StartDate`
- `@EndDate`
- `@ZHID`
- `@XMID`
- `@ZHLX_ONE`

旧过程输出是树形结构：

- 一级：账户类型 `ZHLX`
- 二级：账户 `ZHMC + ZHHM`
- 指标：
  - `ZCJE`：支出金额
  - `SRJE`：收入金额
  - `QCYE`：期初余额
  - `LJSK`：累计收款
  - `LJZC`：累计支出
  - `ZHWL`：账户往来，旧过程为 `SRJE - ZCJE`
  - `DQZHYE`：当前账户余额，旧过程为 `SRJE - ZCJE + QCYE + LJSK - LJZC`

旧账户主数据表 `C_Base_ZHSZ` 字段包含：

- `Id`
- `ZHMC`
- `ZHHM`
- `ZHLX`
- `CQYE`
- `SFGDZH`
- `ZH_State`
- `DEL`

旧库样例账户：

| 账户 | 账号 | 类型 |
| --- | --- | --- |
| 保盛安州制种大县项目（农民工专户） | 27150120000029352 | 农民工专户 |
| 堆龙德庆区乃琼亲子公园建设农 民工工资专户 | 200000847400003 | 农民工专户 |
| 保盛广州银行 | 810259588880010129 | 一般账户 |
| 保盛安州制种（共管户） | 27150120000028650 | 项目专户 |

旧表规模审计：

| 旧表 | 行数 |
| --- | ---: |
| `C_Base_ZHSZ` | 117 |
| `C_CWSFK_GSCWSR` | 4702 |
| `C_CWSFK_GSCWZC` | 2726 |
| `C_JFHKLR` | 7412 |
| `C_ZFSQGL_FKZH_CB` | 0 |
| `C_FKGL_ZHJZJWL` | 431 |
| `BGGL_JHK_HKDJ` | 25 |
| `T_KK_SJTHB` | 1206 |

## 3. 新系统现状

模拟生产库现有承载：

| 新模型/表 | 状态 | 行数/覆盖 |
| --- | --- | --- |
| `sc.treasury.ledger` | 已有资金流水投影 | 16047 行 |
| `sc.treasury.ledger` 收入 | `legacy_receipt` | 3055 行，2041557534.27 |
| `sc.treasury.ledger` 支出 | `legacy_actual_outflow` | 12992 行，2147431936.05 |
| `sc.legacy.fund.daily.line` | 已有账户日报明细 | 7754 表行；默认 active 口径 7454 行 |
| `sc.legacy.fund.daily.line` 账户覆盖 | 账户名称/原编号 | 38 个账户名称，39 个账户原编号 |
| `sc.fund.daily.summary` | 已有日报汇总报表 | 7454 行 |
| `sc_receipt_income` | 已有收款事实 | 9543 行 |
| `payment_request` | 已有付款/收款申请 | 28569 行 |
| `sc_payment_execution` | 已有付款执行 | 1192 行 |
| `sc_treasury_reconciliation` | 已有对账事实 | 19976 行 |

## 4. 缺口判断

该报表不能直接复用 `sc.treasury.ledger`：

- `sc.treasury.ledger` 是项目+往来单位资金流水，缺账户主数据维度。
- 旧过程的账户维度来自 `C_Base_ZHSZ`，并按账户类型汇总成树。
- 旧过程的收入/支出并不只来自资金台账，还包含收款、付款、退款、借款、贷款、保证金、公司财务收入/支出、账户间往来等多来源。
- `DQZHYE` 依赖 `CQYE + 本期往来 + 累计收支`，不是单纯当前流水求和。

当前具备的基础：

- 账户名称、账号、当日收入/支出、当前账面余额已在资金日报明细中部分承载。
- 收付款主事实和资金流水已能覆盖一部分收入/支出口径。

当前不具备的基础：

- 尚无独立账户主数据模型，`C_Base_ZHSZ` 117 个账户未完整承载为可复用业务维度。
- 尚无账户收支统计专用聚合，不能按旧过程字段直接输出树形结果。
- 公司财务收入/支出、借款/贷款、保证金、账户往来等口径需要逐项确认是否已迁移到正式事实表。

## 5. 结论

`账户收支统计表` 当前应维持 `partial`，不能标记 ready。

合理下一步：

1. 新增账户主数据承载，至少包含旧账户 ID、账户名称、账号、账户类型、期初余额、状态。
2. 建只读账户收支统计聚合，优先复用已有 `sc.treasury.ledger` 与 `sc.legacy.fund.daily.line`，缺口来源先保留为可解释字段。
3. 新增菜单入口到报表中心，不替代资金日报和资金台账。
4. 补专用 smoke：验证账户类型一级行、账户二级行、收入/支出/当前余额字段。

## 6. 验证记录

- `docker exec legacy-mssql-restore sqlcmd OBJECT_DEFINITION(Report_SP_USP_Select_ZHSZTJB_GS_Tree)`：PASS
- `docker exec legacy-mssql-restore sqlcmd table counts`：PASS
- `ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec`：PASS
- `make verify.restricted`：SKIP，当前仓库无该 target

补充：在还原库直接执行旧过程时触发 SQL Server collation conflict，审计采用过程定义、表规模和新库事实覆盖判断；不影响字段和来源表拆解。

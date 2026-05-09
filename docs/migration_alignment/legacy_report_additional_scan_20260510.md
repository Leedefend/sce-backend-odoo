# 旧库统计报表追加扫描 2026-05-10

## 扫描范围

- 旧库容器：`legacy-mssql-restore`
- 旧库：`LegacyDb`
- 对象规模：`INFORMATION_SCHEMA.TABLES = 4793`
- 报表候选对象：
  - 存储过程：`415`
  - 用户表：`6`
  - 主键约束：`3`
- 点击来源：`ts_function_RecordUserClick`

## 高频入口

| 优先级 | 旧入口 | 点击 | 用户 | 最近点击 | 当前承载判断 |
| --- | --- | ---: | ---: | --- | --- |
| P0 | 应收应付报表（项目） | 8243 | 18 | 2026-04-10 | 已有 `sc.ar.ap.project.summary`，仍为部分字段承载 |
| P0 | 账户收支统计表 | 1549 | 10 | 2026-04-10 | 已有 `sc.account.income.expense.summary`，需继续对账旧过程过滤条件 |
| P0 | 资金日报表 | 926 | 8 | 2026-04-10 | 已有资金日报表、汇总和明细 |
| P0 | 项目经营统计表 | 866 | 8 | 2026-04-10 | 有入口和 `sc.operating.metrics.project`，需补旧过程字段对齐 |
| P0 | 应收应付报表 | 752 | 10 | 2026-04-08 | 已有 `sc.ar.ap.company.summary`，仍为部分字段承载 |
| P0 | 公司经营情况表 | 726 | 7 | 2026-04-08 | 缺正式交付入口和聚合模型 |
| P1 | 保证金统计表 | 198 | 15 | 2023-07-04 | 已有投标保证金报表，但需核对旧保证金统计全口径 |
| P1 | 资金明细 | 163 | 7 | 2023-02-14 | 已有资金台账，需核对旧 `ZJMX` 字段 |
| P1 | 进项发票明细表 | 127 | 14 | 2023-05-23 | 已有发票相关事实，需单独对齐明细字段 |
| P1 | 供应商合同台账 | 126 | 9 | 2023-08-11 | 已有供货合同分析，需核对台账字段 |
| P1 | 成本发票明细表 | 112 | 12 | 2023-03-31 | 有发票成本进度入口，需补成本发票明细口径 |
| P1 | 发票分类汇总表 | 86 | 12 | 2023-01-05 | 缺分类汇总聚合入口 |
| P1 | 工资统计表 | 73 | 3 | 2026-03-30 | 缺工资统计承载 |
| P1 | 报销统计 | 68 | 4 | 2026-04-09 | 缺费用报销统计承载 |
| P1 | 合同执行分析 | 65 | 10 | 2023-08-01 | 缺合同执行分析聚合 |
| P1 | 贷款统计表 | 61 | 11 | 2023-08-02 | 已有融资台账，需核对贷款统计字段 |

## 旧过程依赖补充

### 项目经营统计表

- 旧过程：`SELECT_XMJYTJB`
- 参数：`@XMID`
- 依赖表：
  - `BASE_SYSTEM_PROJECT`
  - `C_JXXP_DKDJ_New`, `C_JXXP_DKDJ_CB`
  - `C_JXXP_XXKPDJ`, `C_JXXP_XXKPDJ_CB`
  - `C_JXXP_YJSKDJ`, `C_JXXP_YJSKDJ_CB`
  - `C_JXXP_ZYFPJJD`, `C_JXXP_ZYFPJJD_CB`
  - `T_KK_SJDJB`, `T_KK_SJDJB_CB`
  - `ZJGL_SZQR_DKQRB`, `ZJGL_SZQR_DKQRB_CB`

### 公司经营情况表

- 旧过程：`Report_GSJYQKB_BSJZ`
- 参数：`@YEAR`, `@KSSJ`, `@JSSJ`
- 依赖表：
  - `C_CWSFK_GSCWSR`, `C_CWSFK_GSCWZC`
  - `C_JFHKLR`, `C_JFHKLR_CB`
  - `CWGL_FYBX`, `CWGL_FYBX_CB`
  - `BGGL_XZ_GZ`, `BGGL_XZ_GZ_CB`
  - `T_ProjectContract_Out`, `T_ProjectContract_Out_CB`
  - `T_KK_SJDJB`, `T_KK_SJDJB_CB`
  - `T_KK_SJTHB`, `T_KK_SJTHB_CB`
  - `ZJGL_SZQR_DKQRB`, `ZJGL_SZQR_DKQRB_CB`

## 缺口源表规模

| 旧表 | 行数 |
| --- | ---: |
| `C_CWSFK_GSCWSR` | 4702 |
| `C_CWSFK_GSCWZC` | 2726 |
| `CWGL_FYBX` | 1866 |
| `CWGL_FYBX_CB` | 3589 |
| `BGGL_XZ_GZ` | 115 |
| `BGGL_XZ_GZ_CB` | 3458 |
| `C_JXXP_YJSKDJ` | 1290 |
| `C_JXXP_YJSKDJ_CB` | 5455 |
| `T_KK_SJDJB` | 2636 |
| `T_KK_SJDJB_CB` | 13521 |
| `T_KK_SJTHB` | 1206 |
| `T_KK_SJTHB_CB` | 1784 |

## 当前开发库承载快照

| 新模型 | 行数 |
| --- | ---: |
| `sc.ar.ap.project.summary` | 10181 |
| `sc.ar.ap.company.summary` | 788 |
| `sc.account.income.expense.summary` | 120 |
| `sc.fund.daily.summary` | 3750 |
| `sc.legacy.fund.daily.line` | 7454 |
| `sc.treasury.ledger` | 18347 |
| `sc.legacy.financing.loan.fact` | 318 |
| `sc.legacy.expense.deposit.fact` | 11167 |

## 下一轮建议顺序

1. 先补 `公司经营情况表`：旧库仍有 2026-04 使用记录，当前承载状态是明确缺口，且源表覆盖营收、支出、费用、工资、税费，最能解释用户感觉统计报表不足的问题。
2. 收敛 `项目经营统计表`：当前已有入口，但必须按 `SELECT_XMJYTJB` 的字段拆解补齐抵扣、预缴、扣款和税费指标，避免空壳或错口径。
3. 扩展发票类报表：补 `进项发票明细表`、`成本发票明细表`、`发票分类汇总表`，复用现有发票事实，优先做只读明细和分类聚合。
4. 扩展费用和工资统计：补 `报销统计`、`工资统计表`，先确认 `CWGL_FYBX*` 与 `BGGL_XZ_GZ*` 已迁移事实。
5. 对账已有入口：`账户收支统计表`、`应收应付报表`、`投标保证金报表`、`资金台账` 不再只判断“有入口”，必须逐项对照旧过程参数和字段。

## 本轮证据文件

- `artifacts/function-usability-proof/current/legacy_report_object_candidates_20260510.txt`
- `artifacts/function-usability-proof/current/legacy_report_click_rank_20260510.txt`
- `artifacts/function-usability-proof/current/legacy_report_proc_dependencies_20260510.txt`
- `artifacts/function-usability-proof/current/legacy_report_gap_source_counts_20260510.txt`

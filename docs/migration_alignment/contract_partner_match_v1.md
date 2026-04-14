# 合同 Partner 匹配重算 v1

任务：`ITER-2026-04-13-1841`

## 范围

- 数据源：`tmp/raw/contract/contract.csv`
- 合同记录数：1694
- 当前 partner baseline：`artifacts/migration/contract_partner_baseline_v1.json`
- baseline partner 数：85
- 运行方式：只读 dry-run，不调用 ORM，不写数据库，不创建 partner。

## 匹配口径

相对方文本按合同方向推断：

- `CBF` 为本公司且 `FBF` 非本公司：方向为 `out`，相对方取 `FBF`
- `FBF` 为本公司且 `CBF` 非本公司：方向为 `in`，相对方取 `CBF`
- 其他情况：方向为 `defer`

partner 匹配分层：

- `exact`：相对方文本与 partner `display_name/name` 精确一致
- `normalized`：清洗常见标点、空格和组织后缀后唯一一致
- `fuzzy_candidate`：仅输出候选，不自动确认为可写 partner
- `defer`：无法确认唯一 partner

## 重算结果

| 指标 | 数量 |
|---|---:|
| 合同行数 | 1694 |
| 去重相对方文本 | 568 |
| partner baseline 数 | 85 |
| exact | 0 |
| normalized | 0 |
| fuzzy_candidate | 0 |
| defer | 1694 |

方向分布：

| 方向 | 数量 |
|---|---:|
| out | 1554 |
| in | 1 |
| defer | 139 |

## 高频未匹配相对方

| 相对方文本 | 行数 |
|---|---:|
| 德阳市供水安装工程队 | 226 |
| 四川工程职业技术学院 | 110 |
| 中国第二重型机械集团德阳万航模锻有限责任公司 | 103 |
| 二重（德阳）重型装备有限公司 | 94 |
| 中国建筑第四工程局有限公司 | 23 |
| 德阳经开建设工程有限公司 | 17 |
| 四川工程职业技术大学 | 14 |
| 德阳市旌阳区八角井镇卫生院 | 14 |
| 四川建筑职业技术学院 | 14 |
| 四川纹江致远建筑开发工程有限公司 | 14 |
| 德阳市城市管理行政执法局 | 14 |
| 德阳旌信城市管理服务股份有限公司 | 11 |

## 结论

当前不具备自动写入 `partner_id` 的条件。所有 1694 行合同相对方均为 `defer`，必须先进入 partner 主数据准备或人工确认批次。


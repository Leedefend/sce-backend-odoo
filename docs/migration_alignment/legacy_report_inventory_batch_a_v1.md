# 旧库高频报表承载基线 Batch-A

## 批次边界

- Layer Target：业务事实分析层 / Domain Layer
- Module：`addons/smart_construction_core`
- Reason：把旧库真实高频统计分析报表落成可审计承载清单，为后续报表中心实现提供事实基线。

## 本批目标

新增 `sc.legacy.report.inventory` 只读清单，承载旧库高频报表的名称、使用证据、旧实现方式、依赖旧表、目标承载模型、缺口状态与下一步动作。

## 不做

- 不实现最终报表算法。
- 不迁移旧低代码引擎。
- 不修改 `smart_core` 平台内核。
- 不修改启动链 `login -> system.init -> ui.contract`。
- 不改自定义前端消费逻辑。

## 旧库证据来源

- `ts_function_RecordUserClick`：真实用户功能点击日志。
- `BASE_LOWCODE_FORM_CONFIG`：低代码报表/List 配置。
- `BASE_LOWCODE_CUSTOM_SQL`：SQLID 对应自定义 SQL。
- `sys.parameters` / `sys.sql_expression_dependencies`：存储过程参数与依赖对象。
- 旧库核心表行数：项目、合同、付款、收款、发票、资金日报、账户、供应商等事实表。

## P0 报表基线

| 报表 | 点击 | 用户 | 最近使用 | 旧实现 | 承载状态 |
| --- | ---: | ---: | --- | --- | --- |
| 应收应付报表（项目） | 8243 | 18 | 2026-04-10 | LowCode + `UP_USP_SELECT_YSYFHZB_XM` | 部分具备 |
| 账户收支统计表 | 1549 | 10 | 2026-04-10 | LowCode + `Report_SP_USP_Select_ZHSZTJB_GS_Tree` | 部分具备 |
| 资金日报表 | 926 | 8 | 2026-04-10 | LowCode List | 已有事实基础 |
| 项目经营统计表 | 866 | 8 | 2026-04-10 | LowCode + `SELECT_XMJYTJB` | 部分具备 |
| 应收应付报表 | 752 | 10 | 2026-04-08 | LowCode SQL/过程口径 | 部分具备 |
| 公司经营情况表 | 726 | 7 | 2026-04-08 | LowCode + `Report_GSJYQKB_BSJZ` | 存在缺口 |

## 实施结果

- 新增模型：`sc.legacy.report.inventory`
- 新增菜单：报表中心 / 旧库报表承载清单
- 新增 P0/P1 种子数据：8 条
- 权限：数据、财务、成本相关能力组只读；平台配置管理员可维护基线。

## 下一批建议

Batch-B 应优先选择“资金日报表”作为第一个可运行报表闭环，因为新系统已有 `sc.legacy.fund.daily.snapshot.fact` 和 `sc.legacy.fund.daily.line`，数据条件最完整。目标是补齐资金日报汇总视图/聚合服务，而不是继续扩展清单。

Batch-C 再处理“应收应付报表（项目）”，先拆旧过程字段和新系统事实覆盖率，再落聚合模型。

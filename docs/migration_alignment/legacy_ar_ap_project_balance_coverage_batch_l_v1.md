# 应收应付报表（项目）实际可用余额覆盖修复 Batch-L

## 1. 批次定位

- Layer Target：业务事实分析层 / Domain Projection
- Module：`addons/smart_construction_core`
- Reason：Batch-K 审计发现 `SJKYYE` 实际可用余额虽然已进入项目级历史事实，但 `sc.ar.ap.project.summary` 只在已有往来单位业务行上展示余额，导致只有资金余额、没有合同/收付款/发票/自筹事实的项目无法出现在报表中。

## 2. 问题事实

修复前运行库 `sc_prod_sim`：

- `sc.legacy.project.fund.balance.fact` 有效项目余额事实：`755` 个项目
- `sc.ar.ap.project.summary` 中有实际可用余额事实的项目：`512` 个
- 缺口：仅有项目余额、没有其他往来单位事实的项目不会显示

该问题不是字段缺失，而是报表 key 集合只来自项目+往来单位事实，没有把项目级资金余额事实作为补漏 key。

## 3. 修复策略

`sc.ar.ap.project.summary` 的 SQL view 调整为两层 key：

1. `business_keys`：保留原有合同、收款、付款、发票、抵扣、自筹、计价方式等项目+往来单位事实 key。
2. `keys`：先使用 `business_keys`，再补充 `project_fund_balance` 中没有任何业务 key 的项目。

补充行使用：

- `partner_id = NULL`
- `partner_key = project_balance:<project_id>`
- `partner_name = 项目级余额`

这样已有往来单位事实的项目不新增额外行，避免重复膨胀；只有余额事实的项目才新增项目级余额行。

## 4. 验证结果

修复后运行库 `sc_prod_sim`：

- 报表行数：`11696`
- 报表覆盖项目：`814`
- 新增项目级余额行：`56`
- 项目资金余额事实项目数：`755`
- 未进入报表的资金余额项目：`0`
- 有非零实际可用余额的报表行：`10498`
- 有非零实际可用余额的项目：`513`

说明：

- `project_balance:%` 行只用于补足项目级余额可见性。
- `actual_available_balance` 仍是项目级指标，在普通往来单位行上会重复展示，列表页不能直接对该列求和。

## 5. 风险与回滚

- P2：新增的 `项目级余额` 是系统生成显示名，不是旧库往来单位。该显示名用于避免用户误以为余额属于某个客户或供应商。
- P2：项目余额按新系统项目 ID 聚合，若多个旧项目映射到同一新项目，仍按当前项目映射结果展示。
- 回滚：回退本批提交并升级 `smart_construction_core`，即可恢复原 key 逻辑。

## 6. 下一批次

继续复核 `SF` 抵扣比例的旧过程最终 SELECT 口径，判断它是项目+往来单位维度，还是项目级税负比例。

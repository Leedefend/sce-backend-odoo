# 应收应付报表全局口径 Batch-AI

## 批次定位

- Layer Target：Domain Projection / Report View
- Module：`addons/smart_construction_core`
- 数据库：`sc_prod_sim`
- 目标：承载旧库 P0 “应收应付报表”的公司/全局口径入口，复用已验证的项目应收应付事实，不新增历史事实写入。

## 实现内容

新增只读 SQL view 模型：

- 模型：`sc.ar.ap.company.summary`
- 菜单：报表中心 / 应收应付报表
- 来源：`sc.ar.ap.project.summary`
- 粒度：按项目汇总，每个项目一行

该模型复用“应收应付报表（项目）”已验证的 27 字段事实来源，将项目+往来单位粒度聚合到项目粒度。

## 关键口径

- 普通金额字段按项目求和。
- `actual_available_balance` 是项目级指标，从项目口径行取 `MAX`，避免往来单位重复展示导致余额被重复求和。
- `tax_deduction_rate` 是项目级比例，从项目口径行取 `MAX`，不做跨项目简单平均。
- `payable_pricing_method_text` 按项目拆分去重后合并。
- `partner_count` 统计项目下往来单位键数量，辅助判断项目业务复杂度。

## 运行库结果

模拟生产库验证：

- 全局报表行数：`815`
- 项目口径底表行数：`11696`
- 有未收款项目：`658`
- 实际可用余额为负项目：`37`
- 真实用户 `wutao` 可读取：`PASS`
- 菜单归属：`报表中心 / 应收应付报表`

## 验收判断

本批解决的是旧库 P0 “应收应付报表”的入口和项目级汇总承载，不改变项目口径底层事实。

当前状态可用于业务查看公司/全局项目维度应收应付、开票、收付款、税额、自筹、余额等指标。后续如要严格对齐旧过程 `UP_USP_SELECT_YSYFHZB_XM_ZJ`，应按旧库常用查询条件做新旧项目级汇总对账，并确认旧过程是否存在独立公司筛选或特殊汇总行。

## 回滚

回退本批新增模型、视图、ACL、manifest 注册和报表清单状态后，升级 `smart_construction_core` 并重启模拟生产服务。

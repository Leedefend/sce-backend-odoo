# 资金日报汇总报表 Batch-B

## 批次边界

- Layer Target：Domain Projection
- Module：`addons/smart_construction_core`
- Reason：旧库 P0 高频报表“资金日报表”已有主表和明细事实，本批将其承载为报表中心可直接使用的汇总报表。

## 本批目标

新增 `sc.fund.daily.summary` SQL 只读聚合视图，基于 `sc.legacy.fund.daily.line` 按日期、项目、账户汇总，提供 tree / pivot / graph 原生视图入口。

## 不做

- 不修改旧库明细数据。
- 不实现账户收支统计表。
- 不处理应收应付、项目经营、公司经营报表。
- 不修改自定义前端结构。
- 不触碰 `smart_core` 启动链或平台 intent。

## 聚合口径

维度：

- 日期
- 项目
- 账户名称
- 银行账号

指标：

- 明细数
- 当日收入
- 当日支出
- 收支净额
- 账面余额
- 当前账面余额
- 当前银行余额
- 账实差异

## 承载结果

- 模型：`sc.fund.daily.summary`
- 菜单：报表中心 / 资金日报汇总
- 视图：tree、pivot、graph
- 权限：财务只读、财务办理、财务管理员均只读访问

## 后续

下一批可继续推进“应收应付报表（项目）”，但需要先拆 `UP_USP_SELECT_YSYFHZB_XM` 的字段输出和新系统事实覆盖率，不能直接把它当普通列表。

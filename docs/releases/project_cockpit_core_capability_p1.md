# 项目驾驶舱核心能力 P1（冻结稿）

## 1. 目标

在 `project.management` 现有 7-block 合同外壳不变前提下，将页面从“展示壳”升级为“可运营的项目驾驶舱”。

P1 聚焦三件事：

1. 项目是否健康；
2. 哪些指标正在偏离；
3. 今天优先处理哪些动作。

## 2. 执行边界

- 不改 scene registry / scene governance / delivery policy 主机制；
- 不改 ACL / 权限基线；
- 不推翻 `project.dashboard` contract envelope；
- 仅增强 block `data` 的业务语义聚合字段；
- 保持 `verify.project.dashboard.contract` 链路可通过。

## 3. P1 能力范围（7-block）

- Header：项目身份与阶段上下文；
- Metrics：合同/产值/成本/回款/风险 KPI；
- Progress：任务完成率 + 里程碑进展 + 延期信号；
- Contract：合同总额/执行额/变更额/履约率；
- Cost：目标成本/实际成本/偏差/偏差率；
- Finance：应收/已收/应付/已付/资金缺口；
- Risk：风险总量/高风险/风险评分/等级。

## 4. 数据策略

- 业务模型优先（`project.task`、`construction.contract`、`project.cost.ledger`、`payment.request`、`project.risk`）；
- 若模型/字段缺失，返回 0 或空结构，保持合同稳定；
- 允许同一 block 同时输出：
  - 兼容字段（旧渲染继续可用）；
  - 语义字段（新表达可直接消费）。

## 5. 完成标准

- 7 个 block 均有可解释的业务语义数据；
- 页面能回答“健康度/偏差/优先动作”；
- 不破坏现有 verify 主链路。

## 6. 页面结构优先级（前端收口）

在不改变 7-block 合同的前提下，驾驶舱采用固定展示顺序：

1. 核心指标（Metrics）；
2. 风险提醒（Risk）+ 项目进度（Progress）；
3. 合同执行（Contract）+ 成本控制（Cost）+ 资金情况（Finance）；
4. 项目头部信息（Header，作为上下文收口区）。

该顺序用于确保用户首屏先看到“指标 + 风险 + 进度”，再进入经营分项与上下文信息。

## 7. 本轮精修（P1-R2）

- 指标卡补充管理语义提示（如“项目收入基线”“回款/合同额”）；
- 进度区区分“百分比进度”与“延期数量”，避免将延期数误显示为百分比；
- 风险卡在风险区强化视觉权重（强调高风险告警优先处理）。

## 8. 本轮精修（P1-R3）

- Header 摘要区压缩为“项目识别 + 管理上下文”核心字段，减少冗余信息；
- Cost 区按“目标成本/实际成本/偏差/偏差率”统一四列摘要；
- Contract 与 Finance 区表格样式统一（标题层级、行高、斑马纹、区块底色），形成同一经营分项语言。

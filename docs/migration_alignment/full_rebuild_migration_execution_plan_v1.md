# 完整新库重建执行计划 v1

任务：`ITER-2026-04-13-1850`

## Phase 0：重建环境与门禁

- 固定新库初始化方式；
- 固定模块安装/升级顺序；
- 固定字典与基础配置；
- 建立全局 migration run id；
- 所有导入器支持 dry-run 与 write 模式隔离。

## Phase 1：Partner 主数据

当前输入：

- 369 个强证据 partner 候选；
- `res.partner` 已具备 7 个 legacy 字段；
- dry-run 结果：369 个全部 `create_candidate`。

下一步：

- 晋级 partner rebuild importer；
- 先 no-DB；
- 再小样本 create-only；
- 写后复核；
- rollback dry-run。

## Phase 2：Project 主数据

必须重新按完整新库目标生成项目输入，而不是复用演示库样本状态。

要求：

- legacy identity 固定；
- lifecycle 主状态规则固定；
- stage 只做投影；
- project create-only / upsert 策略重新评估。

## Phase 3：Contract 骨架

必须等 partner/project 均 ready 后执行。

首轮只导安全字段：

- legacy contract identity；
- project link；
- partner link；
- subject / type / date 等低风险字段；
- 不回放复杂状态；
- 不处理税务、付款、结算、附件。

## Phase 4：业务链路

建议顺序：

1. 合同扩展字段；
2. 回款/收款切片；
3. 付款申请切片；
4. 结算/成本切片；
5. 附件；
6. 历史流程与审批记录只读归档。

## 每阶段必过门禁

- 输入版本固定；
- dry-run 输出；
- create/update/skip/reject 统计；
- 错误清单；
- rollback dry-run；
- 小样本试写；
- 写后只读复核；
- 可重复运行验证。

## 当前 GO/NO-GO

- 完整生产重建：`NO-GO`
- partner 小样本试写：`NOT_READY`
- partner rebuild importer no-DB 晋级：`READY`


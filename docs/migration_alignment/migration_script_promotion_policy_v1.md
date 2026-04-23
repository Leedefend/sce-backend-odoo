# 迁移脚本晋级策略 v1

任务：`ITER-2026-04-13-1847`

## 脚本分级

### Probe

用于读取旧库或 CSV，获取事实。

要求：

- 只读；
- 可重复运行；
- 输出 JSON/CSV artifact；
- 不写 Odoo；
- 不写旧库。

### Dry-Run

用于模拟创建/更新/跳过/拒绝。

要求：

- 不写数据库；
- 输出逐行结果；
- 输出汇总报告；
- 使用正式候选输入；
- 给出阻塞项。

### Trial Write

用于小样本真实写入。

要求：

- 用户明确授权；
- 使用 legacy identity；
- create-only 或 upsert 策略明确；
- 具备 rollback dry-run；
- 写后只读复核。

### Production Rebuild Step

用于完整新库重建。

要求：

- 幂等；
- 可配置；
- 可分批；
- 可断点恢复；
- 有输入版本；
- 有输出审计；
- 有精确回滚策略；
- 有模块升级/字段物化前置检查。

## 当前脚本状态

当前脚本均处于 `Probe` 或 `Dry-Run Prep` 阶段，不得直接作为生产重建步骤使用。

## 晋级门槛

任何脚本从 `Probe` 晋级到 `Production Rebuild Step` 前，必须补齐：

1. CLI 参数；
2. 输入文件版本校验；
3. legacy identity 校验；
4. 幂等策略；
5. dry-run 与 write 模式隔离；
6. 逐行错误输出；
7. 汇总报告；
8. 回滚锁定设计；
9. Makefile 调用入口；
10. 新库重建顺序文档。


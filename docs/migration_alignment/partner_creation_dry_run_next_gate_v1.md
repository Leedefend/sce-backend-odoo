# Partner 创建 Dry-Run 下一轮门禁 v1

任务：`ITER-2026-04-13-1846`

## 当前状态

状态：`PASS_WITH_IMPORT_BLOCKED`

已具备进入 partner 创建 dry-run 设计的输入表，但不具备真实 partner 创建条件。

## 下一轮允许

下一轮允许：

- 实现 no-DB-write partner dry-run importer；
- 读取 `partner_strong_evidence_dry_run_input_v1.csv`；
- 模拟 create/reuse 判定；
- 输出每个候选的 dry-run action；
- 输出回滚锁定策略；
- 输出是否可进入小样本真实 partner 创建的门禁。

## 下一轮禁止

- 不创建 `res.partner`；
- 不回填合同；
- 不处理 supplier-only；
- 不处理跨源冲突；
- 不处理删除态；
- 不写 Odoo 数据库。

## 推荐锁定键

本批次推荐锁定键：

1. `legacy_partner_id`
2. `source = T_Base_CooperatCompany`
3. `partner_name`

统一社会信用代码和税号只能做辅助校验，因为当前 369 个候选中仅 28 个有统一社会信用代码，1 个有税号。


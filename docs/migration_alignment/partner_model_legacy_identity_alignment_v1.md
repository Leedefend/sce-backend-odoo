# Partner 模型 Legacy Identity 对齐 v1

任务：`ITER-2026-04-13-1849`

## 背景

1848 dry-run 显示 369 个强证据 partner 候选全部是 `create_candidate`。为了满足“完整新库可重复重建”目标，`res.partner` 必须具备稳定旧系统身份字段，否则无法幂等、upsert 或精确回滚。

## 本轮变更

在 `res.partner` 上新增最小追溯字段：

- `legacy_partner_id`
- `legacy_partner_source`
- `legacy_partner_name`
- `legacy_credit_code`
- `legacy_tax_no`
- `legacy_deleted_flag`
- `legacy_source_evidence`

## 设计原则

- `legacy_partner_id + legacy_partner_source` 是首轮重建锁定键；
- `legacy_credit_code` 和 `legacy_tax_no` 只做辅助校验；
- 不新增唯一约束，避免历史脏数据阻断模块升级；
- 不创建 partner；
- 不回填合同；
- 不处理 supplier 补充资料合并。

## 模块影响

- 模型：`res.partner`
- 模块：`smart_construction_core`
- 入口：`addons/smart_construction_core/models/support/partner_legacy.py`
- 注册：`addons/smart_construction_core/models/support/__init__.py`

## 当前结论

模型具备 partner 重建首轮 dry-run / trial write 的 legacy identity 前置字段。真实写入仍需后续授权与写入脚本门禁。


# Odoo 原生承载差距迭代进展（v3.2-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 已完成项

1. `api.data(list)` grouped_rows 契约增强：
   - 新增 `page_requested_size`
   - 新增 `page_applied_size`
   - 新增 `page_clamped`
2. 前端契约同步：
   - schema 增加字段类型定义
   - ActionView 的 `pageSyncedFromServer` 增加 `page_clamped` 判定
3. 文档同步：
   - grouped pagination contract 增补新增字段说明

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

本轮继续完成契约本体增强，grouped 分页对“请求值 vs 实际应用值”的表达进一步完善，客户端可更稳定地处理分页裁剪语义，达到可合并状态。

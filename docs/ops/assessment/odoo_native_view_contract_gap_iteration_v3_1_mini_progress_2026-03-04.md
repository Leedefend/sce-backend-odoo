# Odoo 原生承载差距迭代进展（v3.1-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 已完成项

1. `api.data(list)` grouped_rows 契约增强：
   - 新增 `page_requested_offset`
   - 新增 `page_applied_offset`
   - 新增 `page_max_offset`
2. 前端契约同步：
   - schema 增加上述字段类型
   - ActionView 分页偏移优先使用 `page_applied_offset`，兼容 `page_offset`
3. 文档同步：
   - grouped pagination contract 增补新字段说明

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

本轮继续完成“契约本体”增强，grouped 分页返回语义更完整，可直接支持客户端对分页偏移裁剪行为的可见化与可调试，达到可合并状态。

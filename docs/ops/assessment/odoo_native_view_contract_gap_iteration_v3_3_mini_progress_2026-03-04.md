# Odoo 原生承载差距迭代进展（v3.3-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 已完成项

1. 后端 `api.data(list)` 契约增强：
   - 新增请求参数 `group_limit`
   - 新增响应 `group_paging` 汇总块
   - grouped_rows 新增 size/offset 裁剪语义字段（requested/applied/max/clamped）
2. 前端契约同步：
   - schema 增加 `group_limit`、`group_paging` 与 grouped row 新字段类型
   - ActionView 请求携带 `group_limit`
   - ActionView 消费 `group_paging.page_size` 与 `page_applied_offset`
3. 契约文档同步：
   - grouped_pagination_contract 增补 request/summary/row 字段约定

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

本轮完成以契约本体为中心的连续增强，grouped 分页接口从“可用”提升到“可解释、可调试、可摘要消费”，达到可合并状态。

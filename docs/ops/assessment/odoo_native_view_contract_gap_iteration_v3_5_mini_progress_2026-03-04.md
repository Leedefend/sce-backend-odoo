# Odoo 原生承载差距迭代进展（v3.5-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端 `api.data(list)` 契约增强：
   - 请求接入 `group_offset`
   - `group_paging.group_offset` 回传
   - `meta.group_offset` 回传
2. 前端契约同步：
   - schema 增加 `ApiDataListRequest.group_offset`
   - schema 增加 `ApiDataListResult.group_paging.group_offset`
   - ActionView 列表请求透传 `group_offset=0`（为后续路由化分页预留）
3. 契约文档同步：
   - grouped pagination contract 增加 `group_offset` 请求/摘要说明

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

grouped 分组结果契约从“仅 limit 窗口”升级到“offset + limit 窗口”，为后续大规模分组场景提供稳定分页基础。

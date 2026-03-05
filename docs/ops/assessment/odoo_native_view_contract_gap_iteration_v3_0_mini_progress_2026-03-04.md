# Odoo 原生承载差距迭代进展（v3.0-mini）

日期：2026-03-04  
分支：`feat/interaction-core-p2-mini-v2_8`

## 已完成项

1. 后端 `api.data(list)` grouped 分页契约增强：
   - `group_page_size` 请求参数已接入
   - `grouped_rows` 增加 `page_size` 响应字段（与 `page_limit` 等值）
2. 前端契约消费同步：
   - schema 增加 `group_page_size` / `page_size` 类型
   - ActionView grouped 分页消费优先取 `page_size`，兼容 `page_limit`
   - listRecords/listRecordsRaw 增加 `group_page_size` 透传
3. 文档同步：
   - `docs/contract/grouped_pagination_contract.md` 增加 `group_page_size` 与 `page_size` 约定

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `BASELINE_FREEZE_ENFORCE=0 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 make verify.contract.preflight`：PASS

## 结论

本轮已按目标回归“契约本体完善”，完成 grouped 分页契约的 page-size 明确化升级，达到可合并状态。

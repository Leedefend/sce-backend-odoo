# Odoo 原生承载差距迭代进展（v3.8-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端 `api.data(list)` grouped 契约增强：
   - `group_paging.next_group_offset`：在 `has_more=true` 时给出下一窗口偏移
   - `group_paging.prev_group_offset`：在当前偏移大于 0 时给出上一窗口偏移
   - meta 同步回传 `next_group_offset/prev_group_offset`
2. 前端契约同步：
   - schema 增加 `ApiDataListResult.group_paging.next_group_offset`
   - schema 增加 `ApiDataListResult.group_paging.prev_group_offset`
3. 契约文档同步：
   - grouped pagination contract 增加导航偏移字段说明

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `make verify.contract.preflight`：PASS

## 结论

grouped 分组分页契约已进一步具备可直接消费的窗口导航偏移信息，前端可在不重复推导的前提下稳定实现上一页/下一页分组窗口跳转。

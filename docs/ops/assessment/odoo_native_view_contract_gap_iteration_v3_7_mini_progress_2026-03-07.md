# Odoo 原生承载差距迭代进展（v3.7-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端 `api.data(list)` grouped 契约增强：
   - 新增请求开关 `need_group_total`
   - 新增响应字段 `group_paging.group_total`
   - meta 回传 `need_group_total/group_total`
2. 前端契约同步：
   - schema 增加 `ApiDataListRequest.need_group_total`
   - schema 增加 `ApiDataListResult.group_paging.group_total`
   - ActionView grouped 请求透传 `need_group_total`
3. 契约文档同步：
   - grouped pagination contract 增加 `need_group_total` 与 `group_total` 说明

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `make verify.contract.preflight`：PASS

## 结论

grouped 分页契约已具备“窗口态 + 继续性 + 总量可见性”三要素，前端可在按需模式下构建更完整的分组分页控制与提示。

# Odoo 原生承载差距迭代进展（v3.6-mini）

日期：2026-03-07  
分支：`feat/interaction-core-p2-mini-v3_4`

## 已完成

1. 后端 `api.data(list)` grouped 契约增强：
   - 通过 `group_limit + 1` 的探测窗口计算是否存在后续分组
   - `group_paging.has_more` 回传窗口后续可拉取状态
   - `meta.group_has_more` 回传同语义元信息
2. 前端契约同步：
   - schema 增加 `ApiDataListResult.group_paging.has_more`
3. 契约文档同步：
   - grouped pagination contract 增加 `has_more` 字段说明

## 验证结果

1. `python3 -m py_compile addons/smart_core/handlers/api_data.py`：PASS
2. `make verify.grouped.governance.bundle`：PASS
3. `make verify.frontend.quick.gate`：PASS
4. `make verify.contract.preflight`：PASS

## 结论

grouped 分组分页契约从“可偏移拉取”进一步升级为“可判断是否继续拉取”，前端可据此安全驱动分组窗口的下一页加载。

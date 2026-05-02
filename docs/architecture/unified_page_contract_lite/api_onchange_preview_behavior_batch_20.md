# api.onchange Lite Preview Behavior Guard - Batch 20

## 目标

验证 `api.onchange` 的 Lite preview 接入满足三条运行前置条件：

- 默认请求不返回 `lite_preview`
- opt-in 不完整时仍保持 legacy 默认响应
- opt-in 完整时只追加 `lite_preview` envelope，不改写原 `data`

## 边界

本批次只验证 `api_onchange` 入口的 Lite patch 预览行为。

不做：

- 不启用 `load_contract`
- 不启用 `ui.contract`
- 不改变 legacy `data` 结构
- 不引入 `runtimeContract`
- 不接入前端消费

## 实现策略

将 Lite preview 的判断和 envelope 组装抽到纯 `core` helper：

```text
addons/smart_core/core/unified_page_contract_lite_preview.py
```

`api_onchange` handler 只负责在 legacy response 完成后调用：

```text
with_lite_preview_if_requested(response, params, "api_onchange")
```

这样离线 guard 可以直接验证 helper 行为，不需要启动 Odoo、连接 DB、加载 worker。

## 验收

行为守卫：

```text
scripts/verify/unified_page_contract_lite_api_onchange_preview_behavior_guard.py
```

验证内容：

- default params 返回同一个 response object
- default params 不包含 `lite_preview`
- missing version opt-in 不包含 `lite_preview`
- valid opt-in 返回浅拷贝 response
- valid opt-in 保持 legacy `data` 不变
- valid opt-in 不修改原始 response
- preview payload 为 `updateType=partial`
- preview payload 包含 `statusPatch` / `dataPatch` / `layoutPatch`

产物：

```text
artifacts/backend/unified_page_contract_lite_api_onchange_preview_behavior.json
```

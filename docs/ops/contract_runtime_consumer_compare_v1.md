# Contract Runtime Verification v1 · Batch C

## Scope
- payload source: `docs/ops/contract_runtime_payload_samples_v1.json`
- consumer baseline: `docs/ops/contract_consumer_dependency_v1.md`
- 目标：验证前端真实依赖字段是否被运行时 payload 稳定供给，并识别 fallback 掩盖。

## Dependency supply (runtime payload)
- `head.model` supplied in `0/48` samples
- `head.view_type` supplied in `0/48` samples
- `permissions.effective.rights.create` supplied in `48/48` samples
- `permissions.effective.rights.write` supplied in `48/48` samples
- `render_profile` supplied in `48/48` samples
- `permissions.can_create` supplied in `0/48` samples
- `permissions.can_edit` supplied in `0/48` samples
- `runtime_page_status/page_status` supplied in `0/48` samples
- `actions[]` on `payment.request` supplied in `0/8` samples

## Stability verdict
- 稳定供给：`head.model`, `head.view_type`, `permissions.effective.rights.create/write`。
- 不稳定/缺失：`permissions.can_create`, `permissions.can_edit`, `runtime_page_status/page_status`（在本批 `op=model` payload 中几乎不供给）。
- payment action surface（`actions[].allowed/reason_code/execute_*`）未在本批 `op=model` payload 中出现，需在后续通过 action surface 专项接口补抓。

## Fallback masking findings
- 前端存在 `rights` 默认放行兜底；当 rights 字段缺失时可能掩盖 contract 漏字段。
- 前端存在 `view_type` fallback；当 shape 异常时可能被吸收，降低告警显著性。
- 本批样本虽未出现 rights 缺失，但 runtime 依赖字段缺失会触发“可写态判定依赖其他链路”的隐性风险。

## Batch C conclusion
- `payload vs consumer` 结论：`PARTIAL`。
- 原因：通用 contract 基础字段稳定；但 consumer baseline 中 runtime / action 依赖字段未在本批 `op=model` 样本完整覆盖。
- 输入 Batch D：需在最终验收中明确“冻结字段分层（model surface vs action/runtime surface）”并输出 gap 清单。

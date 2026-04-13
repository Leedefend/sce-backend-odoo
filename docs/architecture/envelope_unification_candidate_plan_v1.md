# Envelope Unification Candidate Plan v1

来源：`artifacts/architecture/envelope_consistency_audit_v1.json`

## Candidate List

1. `addons/smart_core/controllers/platform_contract_capability_api.py`
2. `addons/smart_core/controllers/platform_contract_portal_dashboard_api.py`
3. `addons/smart_core/controllers/platform_execute_api.py`
4. `addons/smart_core/controllers/platform_meta_api.py`

## Risk Tier

- **Tier-1 (low risk, first)**
  - `platform_meta_api.py`
  - `platform_contract_capability_api.py`
  - 理由：以读取/描述类接口为主，副作用低，便于先统一 envelope。

- **Tier-2 (medium risk, second)**
  - `platform_contract_portal_dashboard_api.py`
  - 理由：面向 portal 组合输出，字段兼容面更广，需先做 snapshot 对比。

- **Tier-3 (higher risk, last)**
  - `platform_execute_api.py`
  - 理由：涉及执行动作与 effect 语义，必须在前两层稳定后再推进。

## Batch Order

1. `1533`：Tier-1 第一批（`platform_meta_api.py`）
2. `1534`：Tier-1 第二批（`platform_contract_capability_api.py`）
3. `1535`：Tier-2（`platform_contract_portal_dashboard_api.py`）
4. `1536`：Tier-3（`platform_execute_api.py`）

## Execution Status (2026-04-09)

- `1533` ✅ completed
- `1534` ✅ completed
- `1535` ✅ completed
- `1536` ✅ completed
- `1542` ✅ strict fail-gate enabled in `verify.contract.envelope_consistency_guard`

每批都必须包含：

- envelope before/after snapshot
- error path consistency check
- rollback command

## Rollback

单批回滚规则：

- 仅回滚当前批次改动文件，不跨批回滚
- 保留审计产物和日志，不删除证据

建议命令（示例）：

- `git restore addons/smart_core/controllers/<target>.py`

## Stop Condition

任一批次若出现以下情况即停：

- 返回壳变更导致现有前端解析失败
- 错误路径 reason_code 丢失或口径改变
- effect/data/meta 分层被破坏
- 出现跨域（security/record_rules/payment/settlement/account）修改需求

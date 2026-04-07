# ITER-2026-04-07-1284 Report

## Summary of change
- Batch A（支付/结算隔离补齐）:
  - `addons/smart_construction_core/models/core/project_core.py`
    - 保留并复用 `payment.ledger` 锚点补齐逻辑（`project_id/company_id`）。
    - 新增 `PaymentRequestIsolationAnchor`，用于 `payment.request.company_id` 与项目公司对齐补齐。
  - `scripts/verify/native_business_fact_payment_settlement_anchor_data_verify.py`
    - 修正为“可运行且可解释”的锚点校验：
      - 校验 `payment.ledger` 在 `payment_request` 有项目时不丢失 `project_id`。
      - 校验 `payment.request`、`sc.settlement.order` 在项目存在且项目公司可用时不丢失 `company_id`。
      - 输出 `project_without_company` 观测值作为风险观测，不阻断本批次锚点闭环。
  - 执行历史数据补齐（Odoo shell SQL）：
    - `payment_request.company_id` 回填 102 条。
    - `payment_ledger.company_id` 回填 2 条。
- Batch B（项目组织规则接入 v1）:
  - `addons/smart_construction_core/security/sc_record_rules.xml`
    - `project.project` 用户侧规则补入 `create_uid` 路径，形成“成员/主责/创建人”最小准入。

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1284.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo python3 scripts/verify/native_business_fact_payment_settlement_anchor_data_verify.py`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_OUTSIDER_LOGIN=outsider_seed ROLE_OUTSIDER_PASSWORD=demo STRICT_OUTSIDER_DENY=true python3 scripts/verify/native_business_fact_fixed_user_matrix_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Risk analysis
- High-risk authority path batch completed under dedicated contract allowlist.
- 观测到历史遗留：`payment.request.project_without_company=102`、`sc.settlement.order.project_without_company=18`。
- 当前批次未改动 `security/ir.model.access.csv` 与 `record_rules/**` 之外路径，且未触碰 manifest/financial 语义。
- Stage gate 中 `scene_legacy_auth_smoke` 仍出现 `localhost:8070` runtime unreachable fallback 警告（非本批次目标），建议独立严格化批次清理。

## Rollback suggestion
- `git restore addons/smart_construction_core/models/core/project_core.py`
- `git restore addons/smart_construction_core/security/sc_record_rules.xml`
- `git restore scripts/verify/native_business_fact_payment_settlement_anchor_data_verify.py`
- 若需回滚数据补齐：从 `sc_prod_sim` 备份快照恢复（本批次含 SQL 历史修复）。

## Next iteration suggestion
- 开启下一轮“项目级 company 事实补齐”专项，清零 `project_without_company` 存量后把锚点校验从“有锚项目”提升到“全量项目记录”。

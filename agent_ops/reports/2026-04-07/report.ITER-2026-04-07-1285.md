# ITER-2026-04-07-1285 Report

## Summary of change
- Batch A（project.company_id 存量清理）
  - 盘点结果：`project_project.company_id IS NULL` 共 65 条。
  - 回填策略（最小可解释链）：
    1) `project_manager_user_id.company_id`
    2) `user_id.company_id`
    3) `create_uid.company_id`
    4) `project_task` 单一公司反推
    5) `sc_settlement_order` 单一公司反推
  - 实施结果：
    - by_manager=49
    - by_owner_user=0
    - by_creator=10
    - by_task_single_company=0
    - by_settlement_single_company=0
    - 剩余 6 条待人工处理（均为场景合同历史记录，缺负责人/创建人锚点）。

- Batch B（锚点验证严格化）
  - `scripts/verify/native_business_fact_payment_settlement_anchor_data_verify.py` 升级为阻塞语义：
    - `payment.ledger`：项目型记录必须具备 project 锚点且项目公司存在。
    - `payment.request`：项目型记录必须具备 `company_id`，且项目公司存在。
    - `sc.settlement.order`：项目型记录必须具备 `company_id`，且项目公司存在。
  - `project_without_company` 从观测项升级为 FAIL 条件。

- Batch C（项目侧规则下沉）
  - `addons/smart_construction_core/security/sc_record_rules.xml`
  - 为 `project.task` 两条最小规则补入 `create_uid = user.id` 路径，形成：
    - 项目成员 / 任务负责人 / 创建人 可见。

## Manual pending list
- 未自动回填项目（需人工指定公司，共 6 条）：
  - id=28 name=SCENE-CONTRACT-9c7c4042
  - id=29 name=SCENE-CONTRACT-5720ce48
  - id=30 name=SCENE-CONTRACT-c0a4f1bc
  - id=31 name=SCENE-CONTRACT-d02a6c6b
  - id=32 name=SCENE-CONTRACT-50065a8a
  - id=33 name=SCENE-CONTRACT-f3ac1651

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1285.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo python3 scripts/verify/native_business_fact_payment_settlement_anchor_data_verify.py`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_OUTSIDER_LOGIN=outsider_seed ROLE_OUTSIDER_PASSWORD=demo STRICT_OUTSIDER_DENY=true python3 scripts/verify/native_business_fact_fixed_user_matrix_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Risk analysis
- 交付阻塞项已收敛：payment/settlement 项目型记录锚点严格校验为 0 缺口。
- 残留风险仅在 `project.project` 自身历史场景记录 6 条无公司（当前未影响 payment/request/settlement 项目型锚点）。
- stage_gate 仍存在 `scene_legacy_auth_smoke` 运行态 unreachable fallback WARN（已按“附加小批次”留作独立治理）。

## Rollback suggestion
- `git restore addons/smart_construction_core/security/sc_record_rules.xml`
- `git restore scripts/verify/native_business_fact_payment_settlement_anchor_data_verify.py`
- 若需回滚本轮数据修复，请恢复 `sc_prod_sim` 回填前备份快照。

## Next iteration suggestion
- 启动独立小批次：`scene_legacy_auth_smoke` 严格化（runtime unreachable 必须 FAIL，移除默认 fallback PASS）。

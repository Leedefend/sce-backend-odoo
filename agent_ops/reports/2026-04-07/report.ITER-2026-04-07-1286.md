# ITER-2026-04-07-1286 Report

## Summary of change
- 主线 A：`scene_legacy_auth_smoke` 严格化收口
  - 排查 `localhost:8070` 来源：来自 `scripts/verify/scene_legacy_auth_smoke_semantic_verify.py` 的测试基地址与回退分支打印，不是 stage-gate 运行态 `E2E_BASE_URL` 默认值。
  - `scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
    - 将语义测试基地址从 `http://localhost:8070` 改为 `http://localhost:8069`。
    - 对语义测试内部调用加 `redirect_stdout`，避免将 fallback 分支测试日志泄露到 stage gate 输出。
  - 结果：stage gate 不再出现 `runtime unreachable fallback WARN`，只保留语义 PASS + 运行态 PASS。

- 主线 B：预算/成本规则下沉与验收
  - `addons/smart_construction_core/security/sc_record_rules.xml`
    - 为以下规则补入 `create_uid = user.id`：
      - `rule_sc_cost_read_project_budget`
      - `rule_sc_cost_read_project_cost_ledger`
      - `rule_sc_cost_user_project_cost_ledger`
    - 保留既有项目成员与项目负责人路径。
  - 新增验收脚本：
    - `scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
    - 覆盖：
      - `project.budget / project.cost.ledger` 的 `project_id/company_id` 完整性审计（对有项目公司锚点的记录做阻塞校验）
      - 规则静态 token 审计（成员/负责人/创建人）
      - 真实角色可见性（PM 可见、outsider 对 owner 样本不可见）

- 数据审计/修复（Batch B 前置事实清理）
  - 执行 DB 补齐：
    - `project_budget.company_id` 回填 27 条
    - `project_cost_ledger.company_id` 回填 106 条

## 独立人工处理清单（不混入主线代码）
- 仍待人工指定 `project.company_id` 的 6 条历史场景记录（继承自上一轮）：
  - id=28 `SCENE-CONTRACT-9c7c4042`
  - id=29 `SCENE-CONTRACT-5720ce48`
  - id=30 `SCENE-CONTRACT-c0a4f1bc`
  - id=31 `SCENE-CONTRACT-d02a6c6b`
  - id=32 `SCENE-CONTRACT-50065a8a`
  - id=33 `SCENE-CONTRACT-f3ac1651`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1286.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_OUTSIDER_LOGIN=outsider_seed ROLE_OUTSIDER_PASSWORD=demo python3 scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Risk analysis
- 高风险批次（规则路径）在专用契约与显式授权下完成，未触碰 ACL CSV / manifest / financial semantics。
- 预算/成本仍观察到 `project_without_company` 各 1 条（关联到上述 6 条历史场景项目），已纳入独立人工清单，不阻塞本轮主线目标。

## Rollback suggestion
- `git restore scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
- `git restore addons/smart_construction_core/security/sc_record_rules.xml`
- `git restore scripts/verify/native_business_fact_budget_cost_member_visibility_verify.py`
- 若需回滚数据修复：恢复 `sc_prod_sim` 本轮执行前备份快照。

## Next iteration suggestion
- 启动独立人工数据处理批次，完成上述 6 条 `project.company_id` 手工归属后，再将预算/成本 `project_without_company` 从观测项升级为硬阻塞项。

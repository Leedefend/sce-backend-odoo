# ITER-2026-04-09-1455 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Architecture declaration
- Layer Target: `Platform business-fact permission layer`
- Module: `smart_core release models acl`
- Module Ownership: `smart_core backend contract stack`
- Kernel or Scenario: `scenario`
- Reason: 用户特别授权执行高风险 ACL 分类落地，并要求迭代记录。

## Change summary
- `addons/smart_core/security/smart_core_security.xml`
  - 新增 `smart_core.group_smart_core_release_operator`
  - 新增 `smart_core.group_smart_core_release_auditor`
- `addons/smart_core/security/ir.model.access.csv`
  - `sc.release.action` 新增 operator ACL：`read/write/create=1, unlink=0`
  - `sc.release.action` 新增 auditor ACL：`read=1`
  - `sc.edition.release.snapshot` 新增 operator ACL：`read=1`
  - `sc.edition.release.snapshot` 新增 auditor ACL：`read=1`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1455.yaml` ✅
- `CODEX_NEED_UPGRADE=1 MODULE=smart_core DB_NAME=sc_demo make mod.upgrade` ✅
- `make restart` ✅
- Runtime ACL query (`make odoo.shell.exec DB_NAME=sc_demo`) ✅
  - `sc.edition.release.snapshot`
    - `smart_core.group_smart_core_admin`: `1,1,1,1`
    - `smart_core.group_smart_core_release_auditor`: `1,0,0,0`
    - `smart_core.group_smart_core_release_operator`: `1,0,0,0`
  - `sc.release.action`
    - `smart_core.group_smart_core_admin`: `1,1,1,1`
    - `smart_core.group_smart_core_release_auditor`: `1,0,0,0`
    - `smart_core.group_smart_core_release_operator`: `1,1,1,0`

## Risk analysis
- 结论：`PASS`
- 风险级别：high
- 风险说明：
  - 本批直接修改 ACL 事实层，已按专批策略收口。
  - `release_orchestrator` 当前仍使用 `sudo` 落库，ACL 分类主要约束直接模型访问面；若需执行面完全受 ACL 驱动，需后续专题收敛 `sudo` 边界。

## Rollback suggestion
- `git restore addons/smart_core/security/smart_core_security.xml`
- `git restore addons/smart_core/security/ir.model.access.csv`
- `CODEX_NEED_UPGRADE=1 MODULE=smart_core DB_NAME=sc_demo make mod.upgrade`
- `make restart`

## Next suggestion
- 开下一轮“发布执行 sudo 边界治理”screen 批，分类哪些 `sudo` 必须保留、哪些可下沉到 ACL+policy 事实层。

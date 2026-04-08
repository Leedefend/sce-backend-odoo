# ITER-2026-04-08-1371 Report

## Batch
- Batch: `1/1`

## Summary of change
- 目标问题：`permissions.effective.rights` 与真实用户可执行权限不一致，导致 UI 契约出现“全 false”假象。
- 根因定位：
  - 页面装配路径在 `sudo` 环境下生成权限契约；
  - `get_permission_contract(filter_runtime=True)` 用 `self.env.uid` 计算 effective rights；
  - 在 `sudo` 记录上该 uid 漂移为超级用户上下文，导致 effective 结果偏离请求用户事实。
- 修复内容：
  - `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`：
    - 获取权限契约时显式透传请求用户 `env.uid` 到 `runtime_uid` 上下文。
  - `addons/smart_core/app_config_engine/models/app_permission_config.py`：
    - `get_permission_contract(filter_runtime=True)` 优先使用 `context.runtime_uid` 计算 effective；
    - XMLID 映射 group id 时显式 `int()` 归一，避免类型漂移造成命中异常。
  - `addons/smart_core/tests/test_permission_runtime_uid_alignment.py`：
    - 新增回归测试，覆盖“sudo uid 漂移 vs runtime_uid 覆盖”行为。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1371.yaml` ✅
- `CODEX_MODE=fast CODEX_NEED_UPGRADE=1 ENV=dev DB_NAME=sc_demo MODULE=smart_core make mod.upgrade` ✅
- `ENV=dev DB_NAME=sc_demo make restart` ✅
- `docker exec sc-backend-odoo-dev-odoo-1 sh -lc "python3 /mnt/scripts/verify/permission_runtime_uid_probe.py ..."` ❌（探针脚本在仓库/容器中不存在）
- 等价运行态验证（live intent API）✅：
  - `ui.contract(action_id=543, render_profile=create)` 返回
  - `permissions.effective.rights = {read:true, write:true, create:true, unlink:true}`

## Risk analysis
- 结论：`PASS_WITH_RISK`
- 风险级别：medium
- 风险说明：
  - 合同中声明的探针脚本缺失，已使用等价在线探针替代验证；
  - 建议后续补齐标准探针脚本，避免 acceptance 命令与仓库资产漂移。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/models/app_permission_config.py`
- `git restore addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
- `git restore addons/smart_core/tests/test_permission_runtime_uid_alignment.py`

## Next iteration suggestion
- 新建低风险治理批次：补齐 `permission_runtime_uid_probe.py` 到标准 verify 资产，并将任务合同 acceptance 命令与实际探针资产对齐。

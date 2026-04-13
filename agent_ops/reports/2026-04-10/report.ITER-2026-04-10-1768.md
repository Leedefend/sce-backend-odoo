# ITER-2026-04-10-1768 Report

## Batch
- Batch: `FORM-Batch3`
- Mode: `implement`
- Stage: `form action single-source closure`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `form action single-source governance`
- Module Ownership: `smart_core v2 service + verify script`
- Kernel or Scenario: `kernel`
- Reason: 收敛 form 动作多 surface 的真值关系，避免 name-only 去重误合并与跨区冲突。

## Change summary
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - 升级 `_action_identity`：由 name-only 改为复合 identity（`name/method/action_id/ref`）。
  - 新增 `_canonicalize_action_row`：按 canonical source 补齐跨 surface 一致字段。
  - 增强 `_dedupe_form_action_surfaces`：
    - 以 `buttons + header + box + stat` 构建 canonical map
    - 统一 `header_buttons/button_box/stat_buttons` 的派生与去重
    - 规范 `action_groups` actions（canonical 化 + 组内去重）
- 新增 `scripts/verify/form_action_single_source_audit.py`
  - 审计各 surface 重复 identity
  - 审计跨 surface label 冲突
  - 输出 `artifacts/contract/form_action_single_source_v1.json`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1768.yaml` ✅
- `python3 -m py_compile addons/smart_core/v2/services/ui_contract_service.py scripts/verify/form_action_single_source_audit.py` ✅
- `make restart` ✅
- 重新抓取运行态快照：`tmp/json/form.json` ✅
- `python3 scripts/verify/form_action_single_source_audit.py --json --input tmp/json/form.json` ✅
  - `summary.status=PASS`
  - `surface_duplicates` 全部为 0
  - `label_conflicts=[]`

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：identity 去重由单键升级为复合键，降低误合并风险；仍保持兼容不改变业务动作语义。

## Rollback suggestion
- `git restore addons/smart_core/v2/services/ui_contract_service.py`
- `git restore scripts/verify/form_action_single_source_audit.py`

## Next suggestion
- 进入 `FORM-Batch4 / 104-1`：create/edit/readonly 三态真实 surface 差异化收敛。

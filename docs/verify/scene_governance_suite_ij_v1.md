# Scene Governance Suite IJ v1

状态：PASS  
批次：`ITER-2026-04-22-BE-SCENE-GOVERNANCE-SUITE-IMPLEMENT-IJ`

## 1. 目标

把当前分散的场景治理导出与核心守卫收口成一条统一 suite。

## 2. 当前 suite 顺序

1. `python3 scripts/verify/scene_governance_asset_export.py`
2. `python3 scripts/verify/backend_scene_authority_guard.py`
3. `python3 scripts/verify/backend_scene_canonical_entry_guard.py`
4. `python3 scripts/verify/backend_scene_menu_mapping_guard.py`
5. `python3 scripts/verify/backend_task_family_compat_gap_guard.py`
6. `python3 scripts/verify/backend_scene_provider_completeness_guard.py`
7. `python3 scripts/verify/scene_governance_family_priority_score.py`

## 3. 当前意义

这条 suite 让以下工作不再散落执行：

- current-state governance asset export
- authority / canonical / menu / compat / provider completeness guard
- family priority scoring

## 4. 后续接入方向

后续任何涉及以下内容的批次都应该优先通过这条 suite：

- registry
- provider registration
- menu interpreter
- capability scene target
- family governance closure

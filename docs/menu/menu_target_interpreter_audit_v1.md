# Menu Target Interpreter Audit v1

## Audit Scope

- Facts-only source: `/api/menu/tree` (`nav_fact`)
- Interpreter source: `MenuTargetInterpreterService`
- Unified outlet: `/api/menu/navigation`

## Assertions

1. 每个菜单节点都有唯一解释结果。
2. facts-only 输出不包含解释层字段回写。
3. `target_type` 和 `delivery_mode` 使用固定枚举。
4. 可点击节点有确定 `route`，不可点击节点 `route = null`。
5. `active_match` 由后端生成，不依赖前端推理。
6. 目录节点输出 `DIRECTORY_ONLY` 且不可点击。
7. 不可用节点输出可审计 `reason_code`。

## Current Batch Coverage

- Batch 1: 解释器骨架
- Batch 2: scene 映射
- Batch 3: custom_action 判定
- Batch 4: native_bridge 判定
- Batch 5: url/unavailable 判定
- Batch 6: route 统一生成
- Batch 7: active_match 统一生成
- Batch 8: directory 规则固化
- Batch 9: `/api/menu/navigation` 统一出口
- Batch 10: 快照验证与契约冻结

## Artifacts

- `artifacts/menu/menu_navigation_snapshot_v1.json`

## Verify Entry

- `python3 scripts/verify/menu_target_navigation_snapshot.py --db ${DB_NAME:-sc_demo} --output artifacts/menu/menu_navigation_snapshot_v1.json`


# Projection Refresh Policy v1

## 目的

把刷新语义从页面行为提升为投影层策略：

`action -> mutation -> projection refresh`

## Projection 类型

- `scene_projection`：当前场景列表/表单/工作区投影
- `workbench_projection`：首页指标、今日行动、风险摘要
- `role_surface_projection`：角色入口与可见能力投影

## 策略协议

```json
{
  "refresh_policy": {
    "on_success": ["scene_projection", "workbench_projection"],
    "on_failure": [],
    "mode": "immediate",
    "scope": "local",
    "debounce_ms": 0
  }
}
```

## 执行规则

- `scene_projection` 必须在 mutation 成功后立即刷新。
- `workbench_projection` 在核心业务动作成功后必须刷新。
- 刷新执行结果必须写入 runtime trace（成功/失败/耗时）。

## Core 场景强制项

- `core` 场景必须声明 `refresh_policy.on_success`。
- 未声明视为不满足 `product_ready`。


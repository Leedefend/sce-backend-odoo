# Scene Ready Strict Contract Guard v1

## 目标

将“严格契约模式是否真正由后端契约驱动”纳入可失败的审计断言，
避免迭代再次回到“前端展示补洞”路径。

## 断言范围

- 后端 `scene_ready` 构建器必须输出 `contract_guard`
- `contract_guard` 必须包含：
  - `missing`
  - `defaults_applied`
  - `contract_ready`
- 后端运行链测试必须覆盖：
  - pilot 场景 strict 字段物化
  - 声明策略优先于默认 fallback
  - strict 场景缺口显式化
  - non-pilot 未声明策略时不自动 strict

## 执行命令

```bash
make verify.scene.ready.strict_contract.guard
make verify.scene.ready.strict_gap.full_audit
```

## 报告产物

- `artifacts/backend/scene_ready_strict_contract_guard_report.json`
- `docs/ops/audits/scene_ready_strict_contract_guard_report.md`
- `artifacts/backend/scene_ready_strict_gap_full_audit.json`
- `docs/ops/audits/scene_ready_strict_gap_full_audit.md`

其中 `strict_gap_full_audit` 为**全场景严格检查**：
- 对 `scene_ready_contract_v1.scenes[*]` 逐一检查 surface/view_modes/sections/action_surface/projection 最小契约完整性；
- 同时保留 core strict 场景（4 个）的 `contract_guard` 断言。

## 失败解释

失败意味着 strict 模式的后端契约自证链不完整，
必须先补齐 builder/test 断言，再推进页面层改动。

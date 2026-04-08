# Contract Runtime Verification v1 · Batch B

## Scope
- 输入样本：`docs/ops/contract_runtime_payload_samples_v1.json`
- 冻结基线：`docs/ops/contract_freeze_surface_v1.md`
- 对比维度：缺失字段、shape 漂移、对象差异、角色差异

## Coverage
- sample_count: `48`
- objects: `6`
- roles: `4`

## Missing fields vs freeze
- samples with missing frozen fields: `48/48`
- `head.permissions.create` missing in `48` samples
- `head.permissions.read` missing in `48` samples
- `head.permissions.unlink` missing in `48` samples
- `head.permissions.write` missing in `48` samples
- `permissions.can_create@runtime` missing in `48` samples
- `permissions.can_edit@runtime` missing in `48` samples
- `runtime_page_status/page_status` missing in `48` samples

## Shape drift
- model/surface entries with shape drift: `1`
- `project.project` `form` shape variants: `2`

## Role/object diff summary
- entries with role-rights differences: `0`

## Batch B conclusion
- 发现冻结字段缺口，主要集中在 runtime 冻结字段（`can_create/can_edit/runtime_page_status`）未随 `op=model` payload 提供。
- 存在按角色的 payload shape 差异，需在 Batch D 结论中分类（预期差异 vs 非预期漂移）。
- 建议 Batch C 重点核对：前端真实依赖字段是否被上述 runtime 缺口影响，是否存在 fallback 掩盖。

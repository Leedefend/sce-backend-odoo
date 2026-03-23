# ActionView Batch-C Decision

## Decision

- 结论：`SKIP_BATCH_C`

## Decision Gates

### G1：page shell 是否仍承载业务推导逻辑？

- 结论：`NO`
- 依据：
  - 当前残留主要是 `status/trace/records/projectScope*` 与 `route/lifecycle/group bridge`
  - 这些残留属于数据面 host 与 bridge，不是业务语义推导
  - Phase 2 已完成：
    - `advanced rows -> assembler`
    - `hud entries -> assembler`
    - `selection/batch/group state -> capsule`

### G2：是否阻断首发切片（项目创建 -> 驾驶舱）？

- 结论：`NO`
- 依据：
  - 首发切片链路依赖的是：
    - `project.initiation.enter`
    - `project.dashboard.enter`
    - dashboard entry/block contract
  - `ActionView` 不是首发切片主页面
  - 继续拆 `ActionView` 不会直接提高首发切片冻结度

### G3：继续拆是否还能带来“职责边界级收益”？

- 结论：`NO`
- 依据：
  - 继续拆的剩余项已经从“主链总控权”变为“page shell 厚度优化”
  - 该收益低于切换主线到首发切片的收益
  - 本轮约束明确禁止继续优化 `ActionView` 内部实现

## 残留为何接受

- `records/listTotalCount/projectScope*`：
  - 当前属于主数据面 host，可接受。
- `route/lifecycle/group bridge`：
  - 当前属于 page shell bridge，可接受。
- `group runtime bridge`：
  - 仍有优化空间，但不阻断首发切片。

## 管理结论

- `ActionView` 到此停止继续深化。
- 若未来重新打开 Batch-C，只允许聚焦一个点：
  - `group route/drilldown bridge`
- 当前不建议打开。

# Common Project Code Alignment Wave-1 Plan v1

状态：Next Implementation Batch Plan  
适用对象：平台内核代码层收敛批次 1 的首轮低风险实现任务

---

## 1. 文档目的

本计划把以下三份基线转成真正可执行的 wave-1：

- `platform_kernel_current_mapping_v1.md`
- `common_project_kernel_candidate_map_v1.md`
- `project_workspace_shell_boundary_v1.md`

目标不是大重构，而是用一批低风险 helper / utility 收敛，把 common project 层的候选能力显式化。

---

## 2. Wave-1 范围

wave-1 仅允许以下类型任务：

- request normalization helper extraction
- response envelope helper extraction
- generic workspace collection helper convergence
- project/workspace read-model utility convergence
- contract-to-runtime adapter helper cleanup

这些任务必须满足：

- low-risk
- additive or narrowing cleanup
- no schema change
- no ACL or record-rule change
- no industry semantic relocation

---

## 3. 优先级

### 3.1 Priority A

- generic project/workspace read-model utility inventory and convergence
- common shell runtime adapter helper consolidation

### 3.2 Priority B

- contract normalization helpers shared by project/workspace runtime flows
- common collection response assembly helpers

### 3.3 Priority C

- mixed file ownership clarification notes
- future wave-2 extraction candidates

---

## 4. Do Not Touch

wave-1 明确 `do not touch`：

- payment semantics
- settlement semantics
- account / treasury semantics
- ACL / record rule / security files
- scenario-specific block payload logic
- manifest / migration / schema changes

---

## 5. 推荐任务编组

推荐把下一轮代码层收敛分成三个小批次：

1. `read_model_utility_wave`
   - target: generic project/workspace read-model helpers
   - outcome: shared helper inventory plus first narrow convergence

2. `runtime_adapter_wave`
   - target: contract-to-runtime adapter glue
   - outcome: repeated request/response shaping moves into shared helper modules

3. `workspace_shell_wave`
   - target: common shell helpers only
   - outcome: workspace shell logic narrows while scenario block semantics remain untouched

---

## 6. 验证要求

每张 wave-1 任务卡至少要有：

- task contract validation
- direct unit or verify command for touched helper
- repo-level risk scan
- report with ownership statement

若任务无法明确回答 `Kernel or Scenario`，则不得进入实现。

---

## 7. 结论

- wave-1 只做 low-risk helper convergence
- 先 commonize utilities，不重命名模块
- 先缩小 mixed files，再考虑 deeper extraction
- 完成 wave-1 后，才讨论 wave-2 的 common project layer explicitization

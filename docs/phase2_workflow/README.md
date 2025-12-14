# Phase 2 工作流/审批引擎设计基线

## 范围与目标

- 本阶段唯一主线：把 Phase1 的硬编码状态流转，升级为“可配置的审批链 + 统一运行时”。
- 先落地对象：`project.material.plan`（物资计划）。
- 不做的：通用 BPMN、可视化流程编辑器、多条件分支。保留扩展点，先完成最小闭环。

## 设计产物

- `erd_workflow.md`：工作流核心模型 ERD（Mermaid）。
- `spec_workflow_runtime.md`：运行时动作规范（submit / approve / reject / cancel）。

## 交付思路

- 先锁定文档，再按 Commit A/B/C/D 逐步实现（见作战手册说明）。

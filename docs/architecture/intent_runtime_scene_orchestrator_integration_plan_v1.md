# Intent Runtime 接入 Scene Orchestrator 改造方案 v1

日期：2026-03-14

---

## 1. 改造目标

当前系统存在以下问题：

- UI Base Contract 已存在
- Scene 编排能力存在
- 但 Scene 编排没有进入 Intent Runtime 主链

导致：

- 前端直接消费 Base Contract
- Scene Contract 未成为运行时输出

改造目标：

```text
Intent Runtime
      ↓
UI Base Contract
      ↓
Scene Orchestrator
      ↓
Scene-ready Contract
      ↓
Frontend
```

---

## 2. 新运行链路

### 2.1 改造前

```text
frontend
   ↓
intent request
   ↓
platform core
   ↓
UI contract
   ↓
frontend render
```

### 2.2 改造后

```text
frontend
   ↓
intent request
   ↓
platform core
   ↓
UI Base Contract
   ↓
Scene Orchestrator
   ↓
Scene-ready Contract
   ↓
frontend render
```

---

## 3. Scene Orchestrator 输入

Scene Orchestrator 输入包括：

| 输入 | 来源 |
| --- | --- |
| scene_key | intent |
| ui_base_contract | platform core |
| scene profile | scene registry |
| role surface | app.init |
| delivery policy | product policy |
| provider outputs | scene provider |

---

## 4. Scene Orchestrator 输出

输出统一结构：

```text
scene-ready contract
```

包含：

| 类型 | 内容 |
| --- | --- |
| layout | zones |
| blocks | 页面组件 |
| actions | 可执行动作 |
| search surface | 搜索 |
| workflow surface | 状态 |
| permissions | 权限 |

---

## 5. 系统模块职责

### 平台核心（`smart_core`）

负责：

- UI Base Contract
- Intent Router
- Permission Engine

### 场景编排层（`smart_scene`）

负责：

- Scene Orchestrator
- Scene Profile
- Nav Policy
- Role Policy

### 行业模块（`smart_construction_scene`）

负责：

- 行业 scene 定义
- 页面布局
- block 组合

---

## 6. 前端渲染规则

前端只做：

```text
Scene Renderer
```

前端组件只渲染：

```text
zones
blocks
actions
search surface
```

不参与：

- 页面逻辑判断
- 权限推理
- 页面结构生成

---

## 7. 运行时验证升级

`verify` 需要新增运行时验证：

### `verify.scene.runtime`

验证：

- intent response 是否经过 orchestrator
- response 是否 scene-ready
- base contract 未被直接暴露

---

## 8. 迁移步骤

建议迁移顺序：

### Step 1

定义 UI Base Contract。

### Step 2

实现 Scene Orchestrator runtime。

### Step 3

打通一个样板 scene。推荐：

```text
projects.intake
```

### Step 4

前端只消费 scene-ready contract。

---

## 9. 最终系统结构

最终系统 UI 架构：

```text
Frontend
   ↓
Intent API
   ↓
Platform Core
   ↓
UI Base Contract
   ↓
Scene Orchestrator
   ↓
Scene-ready Contract
   ↓
Scene Renderer
```

---

## 10. 关键结论

**UI Base Contract 是能力事实。**

**Scene-ready Contract 才是页面现实。**


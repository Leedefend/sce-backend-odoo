# UI Base Contract 与 Scene-ready Contract 分层定义 v1

日期：2026-03-14  
范围：平台 UI 契约体系

---

## 1. 架构目标

在当前系统架构中：

- 平台核心可以返回完整 UI 契约能力
- 场景编排层负责产品化页面组织
- 前端负责通用渲染

为了避免系统出现 **契约输入与页面输出混用** 的问题，平台 UI 契约体系必须明确分层。

系统 UI 契约分为三类：

| 层级 | 名称 | 职责 |
| --- | --- | --- |
| L1 | UI Base Contract | 平台原始 UI 能力事实 |
| L2 | Scene-ready Contract | 场景编排后的页面契约 |
| L3 | App Shell Contract | 应用壳层契约 |

前端只能消费 **Scene-ready Contract + App Shell Contract**。

---

## 2. UI Base Contract 定义

### 2.1 定义

UI Base Contract 是平台核心返回的 **原始 UI 能力事实集合**。

来源：

```text
intent request
      ↓
platform core
      ↓
UI Base Contract
```

该契约描述系统**可以表达的 UI 能力**。

### 2.2 Base Contract 典型结构

```json
{
  "model": "...",
  "fields": {},
  "views": {},
  "actions": [],
  "search": {},
  "workflow": {},
  "permissions": {},
  "validators": {},
  "meta": {}
}
```

### 2.3 Base Contract 的职责

Base Contract 用于描述：

| 类型 | 内容 |
| --- | --- |
| 模型能力 | 字段定义 |
| 视图能力 | tree/form/kanban |
| 行为能力 | actions |
| 查询能力 | search/filter/group |
| 权限能力 | ACL |
| 工作流能力 | 状态推进 |
| 校验能力 | validator |

它回答的问题是：

> **系统原生能力是什么**

### 2.4 Base Contract 的重要约束

Base Contract **不是前端页面契约**。

前端不得：

- 直接读取 base contract 生成页面
- 直接使用 base contract 中的字段/动作

Base Contract 的唯一职责是：

```text
Scene Orchestrator 输入
```

---

## 3. Scene-ready Contract 定义

### 3.1 定义

Scene-ready Contract 是经过场景编排层处理后生成的 **最终页面契约**。

来源：

```text
UI Base Contract
      +
Scene Profile
      +
Role Surface
      +
Delivery Policy
      ↓
Scene Orchestrator
      ↓
Scene-ready Contract
```

### 3.2 Scene-ready Contract 典型结构

```json
{
  "scene": {
    "key": "projects.intake",
    "title": "项目立项",
    "layout": "list"
  },
  "page": {
    "zones": [
      {
        "name": "header",
        "blocks": []
      },
      {
        "name": "main",
        "blocks": []
      }
    ]
  },
  "actions": [],
  "search_surface": {},
  "workflow_surface": {},
  "permission_surface": {},
  "meta": {}
}
```

### 3.3 Scene-ready Contract 的职责

Scene-ready Contract 描述：

| 类型 | 内容 |
| --- | --- |
| 页面布局 | zones / blocks |
| 页面行为 | actions |
| 查询界面 | search_surface |
| 权限界面 | permission_surface |
| 工作流界面 | workflow_surface |

它回答的问题是：

> **当前用户在当前场景看到的页面是什么**

---

## 4. App Shell Contract

App Shell Contract 由 `app.init` 返回。用于定义应用壳层结构。

典型结构：

```json
{
  "nav": [],
  "nav_meta": {},
  "role_surface": {},
  "default_route": "/workspace"
}
```

职责：

| 类型 | 内容 |
| --- | --- |
| 导航结构 | nav |
| 用户角色 | role_surface |
| 默认入口 | default_route |

---

## 5. 三层契约关系

系统 UI 契约层级如下：

```text
App Shell Contract
      ↓
Scene-ready Contract
      ↓
UI Base Contract
```

逻辑关系：

```text
UI Base Contract
        ↓
Scene Orchestrator
        ↓
Scene-ready Contract
        ↓
Frontend Renderer
```

---

## 6. 前端消费规则

前端只允许使用：

```text
Scene-ready Contract
App Shell Contract
```

前端禁止：

- 直接消费 Base Contract
- 直接读取模型字段结构
- 自行组织页面结构

---

## 7. 系统收益

分层后系统获得以下能力：

### UI 可产品化

页面由 Scene Orchestrator 定义。

### 前端完全通用

前端只负责渲染 blocks。

### 行业模块独立

行业模块只需要定义 scene profile。


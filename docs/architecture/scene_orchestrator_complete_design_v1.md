# Scene Orchestrator 完整设计 v1

日期：2026-03-14  
范围：平台 UI 场景编排引擎

---

## 1. 设计目标

Scene Orchestrator 是系统 UI 架构中的核心运行时组件。

其职责是：

> 将 **UI Base Contract（平台能力事实）** 转换为  
> **Scene-ready Contract（页面最终结构）**

实现平台 UI 的：

- 场景化
- 产品化
- 角色化
- 行业化

核心原则：

**前端永远不理解业务，只理解 Scene。**

---

## 2. 架构位置

系统整体 UI 架构：

```text
Frontend Renderer
        ↑
Scene-ready Contract
        ↑
Scene Orchestrator
        ↑
UI Base Contract
        ↑
Platform Core (Intent Engine)
        ↑
Odoo Models / Views
```

含义：

- Odoo 提供能力
- 平台核心暴露能力
- Scene Orchestrator 编排能力
- 前端只渲染结果

---

## 3. Scene Orchestrator 的职责

Scene Orchestrator 完成六件事：

| 编排能力 | 说明 |
| --- | --- |
| Layout 编排 | 页面结构 |
| Block 编排 | 页面组件 |
| Action 编排 | 页面行为 |
| Search 编排 | 查询界面 |
| Workflow 编排 | 状态流程 |
| Permission 编排 | 权限控制 |

换句话说：

Scene Orchestrator 决定：

**这个页面应该长什么样**

---

## 4. Scene Profile（场景配置）

每个 Scene 必须定义 Scene Profile。

Scene Profile 描述：

```text
页面要展示什么
```

示例：

```python
SceneProfile(
    key="projects.intake",
    model="project.project",
    view_type="list",
    layout="list_with_toolbar",

    zones=[
        "header",
        "toolbar",
        "search",
        "main",
        "sidebar"
    ]
)
```

Scene Profile 不包含：

- 页面数据
- 页面组件实例

只定义：

**结构框架**

---

## 5. 页面结构体系

Scene 页面由四层组成：

```text
Scene
  └── Page
        └── Zones
              └── Blocks
```

结构：

```text
Scene
 └ Page
    ├ Header
    ├ Toolbar
    ├ Search
    ├ Main
    └ Sidebar
```

---

## 6. Zone 定义

Zone 是页面结构区域。

常见 Zone：

| Zone | 作用 |
| --- | --- |
| header | 页面标题 |
| toolbar | 页面按钮 |
| search | 搜索区 |
| main | 主内容 |
| sidebar | 辅助信息 |
| footer | 页脚 |

Zone 只描述：

```text
区域存在
```

不描述：

```text
区域内容
```

---

## 7. Block 定义

Block 是 UI 的最小可组合单位。

例如：

| Block | 示例 |
| --- | --- |
| ListBlock | 列表 |
| FormBlock | 表单 |
| KanbanBlock | 看板 |
| StatsBlock | 统计卡片 |
| ChartBlock | 图表 |

Block 由 Scene Orchestrator 生成。

示例：

```json
{
  "block_type": "list",
  "model": "project.project",
  "fields": ["name", "stage", "manager"],
  "actions": ["open", "edit"]
}
```

---

## 8. Action Surface

Scene Orchestrator 生成：

```text
actions surface
```

定义页面行为。

示例：

```json
{
  "actions": [
    {
      "key": "create_project",
      "label": "新建项目",
      "intent": "project.create"
    }
  ]
}
```

来源：

```text
Base Contract actions
+ Scene policy
```

---

## 9. Search Surface

Search Surface 定义：

```text
搜索 UI
```

来源：

```text
Odoo search view
+ Scene policy
```

示例：

```json
{
  "filters": [
    "stage",
    "manager"
  ],
  "search_fields": [
    "name",
    "code"
  ]
}
```

---

## 10. Workflow Surface

Workflow Surface 定义：

```text
状态推进 UI
```

例如：

```text
Draft → Approved → Executing → Done
```

示例：

```json
{
  "workflow": {
    "states": ["draft", "approved", "running", "done"],
    "transitions": [
      {"from": "draft", "to": "approved"},
      {"from": "approved", "to": "running"}
    ]
  }
}
```

---

## 11. Permission Surface

Scene Orchestrator 根据：

```text
ACL
Record Rules
Role Surface
```

生成页面权限。

示例：

```json
{
  "permissions": {
    "create": true,
    "edit": false,
    "delete": false
  }
}
```

---

## 12. Scene-ready Contract 完整结构

最终输出：

```json
{
  "scene": {
    "key": "projects.intake",
    "title": "项目立项"
  },

  "page": {
    "zones": [
      {
        "name": "header",
        "blocks": []
      },
      {
        "name": "toolbar",
        "blocks": []
      },
      {
        "name": "search",
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
  "permission_surface": {}
}
```

---

## 13. Scene Orchestrator 运行流程

运行链路：

```text
intent request
      ↓
platform core
      ↓
UI Base Contract
      ↓
Scene Registry
      ↓
Scene Profile
      ↓
Scene Orchestrator
      ↓
Scene-ready Contract
      ↓
frontend render
```

---

## 14. Scene Registry

Scene Registry 用于注册所有 Scene。

示例：

```python
SCENE_REGISTRY = {
    "workspace.home": WorkspaceHomeScene,
    "projects.intake": ProjectIntakeScene,
    "projects.dashboard": ProjectDashboardScene
}
```

Registry 提供：

```text
scene_key → scene_profile
```

---

## 15. Scene Provider

Scene Provider 用于动态补充数据。

例如：

- Dashboard metrics
- KPI
- 统计

示例：

```python
class ProjectDashboardProvider(SceneProvider):

    def provide(self, env):
        return {
            "stats": {
                "project_count": 52
            }
        }
```

---

## 16. 行业模块职责

行业模块定义：

| 类型 | 内容 |
| --- | --- |
| scene profile | 页面结构 |
| scene provider | 业务数据 |
| nav policy | 导航分组 |

例如：

```text
smart_construction_scene
```

---

## 17. 平台模块职责

平台层负责：

- Scene Orchestrator
- Scene Registry
- Scene Runtime
- Contract Validation

---

## 18. 系统收益

完成该架构后系统获得：

### UI 产品化

页面完全由 scene 定义。

### 前端极简

前端只渲染 blocks。

### 行业可扩展

行业模块只写 scene。

### 架构稳定

Odoo 升级不会影响 UI。

---

## 19. 最重要的一句话

**Odoo 提供能力**

**Scene Orchestrator 决定产品**

**Frontend 只是渲染器**


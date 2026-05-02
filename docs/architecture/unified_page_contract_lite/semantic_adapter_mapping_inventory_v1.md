# Unified Semantic Page Contract Lite - Semantic Adapter Mapping Inventory v1

Date: 2026-05-01
Status: Phase 1 mapping freeze

## 1. Batch Boundary

Layer Target: Contract Governance / Semantic Adapter Mapping

Module:

- `docs/architecture/unified_page_contract_lite`
- `docs/ops/audits`
- `scripts/verify`
- `Makefile`

Reason:

当前阶段必须先把现有 Odoo 契约来源到 Lite 目标结构的映射关系冻结，再写 adapter。否则实现会把兼容逻辑、状态推导、patch 规则散进 handler 或前端。

本批只做映射清单，不实现 adapter。

## 2. Active Target

当前 active canonical target 是：

```text
Unified Semantic Page Contract Lite
```

顶层只允许：

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "meta": {}
}
```

Phase 1 不做：

- `runtimeContract`
- `componentRegistry`
- `capabilities`
- `selectorStatus`
- `dependencyGraph`
- realtime / streaming / subscription
- collaboration / AI orchestration
- Action DSL / Workflow VM

## 3. Source Inventory

| Source | Path | Role | Phase 1 Use |
|---|---|---|---|
| `ui.contract` | `addons/smart_core/handlers/ui_contract.py` | 当前原生契约交付入口 | input only |
| native view projection | `addons/smart_core/core/native_view_contract_projection.py` | primary view 投影 | input only |
| `semantic_page` snapshots | `docs/contract/snapshots/native_view/*.json` | 当前最稳定语义页面面 | preferred input |
| view parser | `addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py` | XML/modifiers/x2many 解析 | input only |
| page assembler | `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py` | fields/permissions/relation_entry/access_policy | input only |
| contract governance | `addons/smart_core/utils/contract_governance.py` | field/action/validation policies | input only |
| `api.onchange` | `addons/smart_core/handlers/api_onchange.py` | onchange patch source | patch input |
| x2many commands | `frontend/apps/web/src/app/x2manyCommands.ts` | 当前前端命令语义参考 | reference only |
| `scene_contract_v1` | `addons/smart_core/core/scene_contract_builder.py` | 场景兼容来源 | compat input only |
| `page_orchestration_v1` | `addons/smart_core/core/page_contracts_builder.py` | 编排兼容来源 | compat input only |

## 4. Mapping Rules

### 4.1 PageInfo

| Source | Target | Rule |
|---|---|---|
| `ui.contract.head.model` | `pageInfo.model` | 直接继承 Odoo model |
| `ui.contract.head.view_type` / primary view | `pageInfo.viewType` | 取 primary view，`tree,form` 首位为当前视图 |
| `scene_key` / action/menu context | `pageInfo.sceneKey` | 有场景则保留；无场景用 model/view 生成稳定 key |
| request client type | `pageInfo.clientType` | 只影响适配，不改变业务语义 |
| Lite schema | `pageInfo.contractVersion` | 固定 `2.0.0` |

### 4.2 LayoutContract

| Source | Target | Rule |
|---|---|---|
| `semantic_page.zones[]` | `layoutContract.containerList[]` | zone 映射为顶层 container |
| `semantic_page.zones[].blocks[]` | `container.children/widgetList` | block 映射为容器或组件 |
| `views.form.layout` | container tree | semantic_page 不足时作为补充输入 |
| `views.form.subviews` / x2many blocks | `containerType=x2many` | x2many 关系区块保留结构，不携带权限判断 |
| `statusbar/header_buttons/button_box` | widget/container | 只生成结构占位，状态交给 StatusContract |

禁止：

- 在 LayoutContract 放 `readonly/required/permission`
- 在 LayoutContract 放业务规则
- Phase 1 引入 `componentRegistry/capabilities`

### 4.3 StatusContract

| Source | Target | Rule |
|---|---|---|
| `semantic_page.permission_verdicts` | global status defaults | 作为 read/write/create/delete/execute 的全局依据 |
| `field_policies` | `widgetStatus[]` | 首选字段最终状态来源 |
| `views.form.field_modifiers` | `widgetStatus[]` | 静态 verdict 可直接映射；动态表达式由后端 patch 收敛 |
| `access_policy` | `widgetStatus[]` | relation read deny/block/degrade 映射为字段状态 |
| `action_policies` | `buttonStatus[]` | 首选按钮状态来源 |
| `semantic_page.actions.*.enabled` | `buttonStatus[]` | 补充按钮启用状态与 reasonCode |

关键原则：

```text
Status must be backend generated.
Frontend must not infer visible / readonly / required / disabled.
```

### 4.4 ActionContract

| Source | Target | Rule |
|---|---|---|
| `semantic_page.actions` | `actionRuleList[]` | 只生成事件声明 |
| `views.form.header_buttons` | click action | header/smart/body button 统一为 click dispatch |
| onchange field list | change action | 字段变化只上报 actionId |
| save/delete/validate | submit/delete/confirm action | 前端只 dispatch，后端执行 |
| x2many row actions | click/add/delete action | row action 仍是事件声明 |

禁止字段：

- `actionType`
- `chainAction`
- `conditionBranch`
- `loop`
- `workflow`
- `jsonLogic`
- `script/function/eval/expression`

ActionContract 不是规则引擎。

### 4.5 DataContract

| Source | Target | Rule |
|---|---|---|
| record / values | `mainData` | 主表单可渲染值 |
| rows / relation rows / line patches | `relationData` | x2many/relation 可渲染行 |
| dict/options | `dictData` | 下拉、枚举、selection |
| relation_entry metadata | `dictData` hints only | 只保留可渲染提示；权限进入 StatusContract |

禁止：

- permission
- readonly
- workflow
- linkage rules
- realtime datasource
- subscription / consistency / streaming

### 4.6 Patch Protocol

| Source | Target | Rule |
|---|---|---|
| `api.onchange.patch` | `dataPatch` | 字段值变化 |
| `api.onchange.modifiers_patch` | `statusPatch` | 显隐/只读/必填/domain 状态变化 |
| `api.onchange.line_patches` | `dataPatch.relationData` | x2many 行级变化 |
| warnings | `meta` or patch diagnostics | 只作提示，不改变业务语义 |

Patch 只允许：

- `replace`
- `merge`

## 5. Governance Decisions

1. `semantic_page` 是 Phase 1 最优先 source surface。
2. `ui.contract` 当前仍是交付入口，但不是 Lite canonical output。
3. `scene_contract_v1` 和 `page_orchestration_v1` 只能作为 compat input，不进入 Lite 顶层。
4. x2many 现有前端命令逻辑只能作为参考，最终语义必须收敛到后端 adapter 和 patch。
5. Lite adapter 后续必须是纯后端、无 ORM write、无 public intent 改名、无启动链改动。

## 6. Next Batch

Batch: `Lite Phase 1 / Batch-2 - Pure Backend Lite Adapter Skeleton`

Allowed scope:

- `addons/smart_core/core`
- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Must not touch:

- `login`
- `system.init`
- `ui.contract` default output
- frontend runtime
- `runtimeContract`

Exit criteria:

- adapter can convert existing static sample payloads into Lite snapshots
- Lite guard validates snapshots
- no runtime-heavy field is introduced


# 契约 2.0 规范与开发手册（Contract-First）

> 本文在“契约 1.0”基础上，**固化并升级**为“契约 2.0”。核心变化：  
> - **单一接口**：`POST /api/contract/get`，统一 `nav / menu / action / model` 四类入口  
> - **契约即页面、即数据**：支持 `with_data`、分页/筛选、动态规则、搜索面板、工作流态、协作区等  
> - **可缓存**：ETag/304、版本拼装；前端零推理渲染与最少 API

---

## 目录

- [一、设计目标（对比 1.0 ➜ 2.0）](#一设计目标对比-10--20)
- [二、统一接口协议](#二统一接口协议)
  - [2.1 路由](#21-路由)
  - [2.2 Request Body](#22-request-body)
  - [2.3 Response Body](#23-response-body统一)
  - [2.4 错误模型](#24-错误模型)
- [三、契约数据结构规范（2.0）](#三契约数据结构规范20)
  - [关键域说明](#关键域说明)
- [四、导航契约（Nav Contract）](#四导航契约nav-contract)
- [五、后端实现要点](#五后端实现要点)
  - [5.1 控制器（V2，单一入口）](#51-控制器v2单一入口)
  - [5.2 服务：`app.contract.service.generate_contract(...)`](#52-服务appcontractservicegenerate_contract)
- [六、前端对接指南（要点）](#六前端对接指南要点)
- [七、迁移指南（1.0 ➜ 2.0）](#七迁移指南10--20)
- [八、测试与发布清单](#八测试与发布清单)
- [九、性能优化建议](#九性能优化建议)
- [十、附录：表达式与语法](#十附录表达式与语法)
- [License](#license)

---

## 一、设计目标（对比 1.0 ➜ 2.0）

| 维度 | 1.0 | 2.0（本稿） |
|---|---|---|
| 入口 | `GET /api/v1/contract`（仅 `model_code`） | **`POST /api/contract/get`**（`subject:'nav'|'menu'|'action'|'model'`） |
| 一次响应 | 字段+权限+布局 | **页面全量**：`head / permissions / rules / search / views / fields / buttons / workflow / collab / reports / ui / data / meta` |
| 数据 | 另行调用列表/记录接口 | **`with_data`** 同返首屏数据；统一 `domain/order/limit/offset` |
| 搜索/聚合 | 无标准 | **`search.filters/group_by`**、`pivot/graph/calendar/gantt` |
| 动态规则 | 局部 | **统一 `modifiers/attrs` 表达式**（`invisible/readonly/required`） |
| 菜单/动作 | 依赖额外接口 | **`subject:` `nav/menu/action` 原生支持** |
| 缓存 | 弱 | **ETag/304 + version** |
| 前端耦合 | 较多推理 | **零推理渲染**（契约即页面/行为/数据） |

---

## 二、统一接口协议

### 2.1 路由

- **POST** `/api/contract/get`（仅 JSON）  
- `auth='user'`（建议）  
- 返回：`{ ok, data, meta } | { ok:false, error }`

### 2.2 Request Body

```json
{
  "subject": "nav | menu | action | model",

  "id": 390,                         // subject:'menu'
  "action_id": 472,                  // subject:'action'
  "action_xmlid": "module.action_x", // subject:'action'
  "model": "project.project",        // subject:'model'

  "view_type": "tree,form",   // 可单值或逗号串
  "view_id": 123,             // 可空
  "record_id": 456,           // 打开表单时的记录

  "with_data": true,          // 是否返回首屏数据
  "domain": [["active","=",true]],
  "order": "id desc",
  "limit": 50,
  "offset": 0,

  "measures": ["amount_total:sum"],     // pivot/graph 可选
  "groupby": ["company_id","create_date:month"],
  "calendar": {"date_start":"date_start","date_stop":"date_end","color":"user_id"},
  "gantt": {"date_start":"date_start","date_stop":"date_end","progress":"progress"},

  "context": {"lang":"zh_CN","uid":7,"company_id":1}
}
```

### 2.3 Response Body（统一）

```json
{
  "ok": true,
  "data": { ... 契约主体 ... },
  "meta": {
    "subject": "menu",
    "version": "model:12|view:34|perm:7|search:5|actions:9",
    "etag": "8e7a5b...f1",
    "ts": "2025-08-21T06:12:00Z",
    "elapsed_ms": 23
  }
}
```

### 2.4 错误模型

```json
{ "ok": false, "error": "Missing parameter: id (menu_id)" }
```

> **说明**：前端可根据 HTTP 200 + `ok:false` 统一处理；严重异常可直接 5xx。

---

## 三、契约数据结构规范（2.0）

> 顶层对象即**页面全部“渲染 + 交互 + 数据”所需**。

```json
{
  "head": {
    "model": "project.project",
    "title": "项目列表",
    "view_modes": ["tree","form","kanban","pivot","calendar","gantt","graph"],
    "default_view": "tree",
    "breadcrumbs": [{"label":"施工企业管理","menu_id":382},{"label":"项目","menu_id":383}],
    "identity": {"pk":"id","display":"name"},
    "context": {"lang":"zh_CN","uid":7,"company_id":1}
  },

  "permissions": { "read": true, "create": true, "write": true, "unlink": false },

  "rules": {
    "record_rules": [{"name":"项目可见性","domain":[["company_id","=",1]]}],
    "domain_default": [],
    "order_default": "id desc"
  },

  "search": {
    "filters": [
      {"name":"my_projects","label":"我的项目","domain":[["user_id","=","uid"]],"default":true},
      {"name":"active","label":"启用","domain":[["active","=",true]]}
    ],
    "group_by": [
      {"field":"stage_id","type":"many2one"},
      {"field":"company_id","type":"many2one"},
      {"field":"create_date","type":"date","granularity":["day","week","month"]}
    ],
    "facets": { "enabled": true, "fast_count": false }
  },

  "views": {
    "tree": {
      "columns": ["id","name","partner_id","stage_id","amount_total","create_date"],
      "row_actions": [{"name":"open_form","label":"打开","intent":"form.open"}],
      "modifiers": { "amount_total": {"align":"right","format":"currency"} },
      "row_classes": [{"expr":["state","=","blocked"],"class":"row-error"}],
      "page_size": 50
    },
    "form": {
      "layout": [
        {"type":"sheet","children":[
          {"type":"group","label":"基本信息","children":[
            {"type":"field","name":"name"},
            {"type":"field","name":"partner_id"},
            {"type":"notebook","tabs":[
              {"label":"明细","children":[{"type":"field","name":"line_ids"}]},
              {"label":"备注","children":[{"type":"field","name":"notes"}]}
            ]}
          ]}
        ]},
        {"type":"chatter","enabled": true}
      ],
      "statusbar": {"field":"state","states":["draft","confirm","done","cancel"]},
      "modifiers": {
        "partner_id": {"required":["state","=","draft"]},
        "notes": {"readonly":["state","in",["done","cancel"]]}
      }
    },
    "kanban": { "templates": "..." },
    "pivot":  { "measures": ["amount_total"], "dimensions": ["company_id","stage_id","create_date:month"]},
    "graph":  { "type":"bar", "measure":"amount_total", "dimension":"create_date:month" },
    "calendar": { "date_start":"date_start","date_stop":"date_end","color":"user_id" },
    "gantt":    { "date_start":"date_start","date_stop":"date_end","progress":"progress" }
  },

  "fields": {
    "id": {"string":"ID","type":"integer","readonly":true},
    "name": {"string":"名称","type":"char","required":true},
    "partner_id": {"string":"客户","type":"many2one","relation":"res.partner","domain":[],"onchange":["name"]},
    "stage_id": {"string":"阶段","type":"many2one","relation":"project.stage"},
    "amount_total": {"string":"金额","type":"monetary","currency_field":"currency_id"},
    "state": {"string":"状态","type":"selection","selection":[["draft","草稿"],["confirm","确认"],["done","完成"]]}
  },

  "buttons": [
    {"name":"action_confirm","label":"确认","place":"header","intent":"button.execute","visible":["state","=","draft"]},
    {"name":"action_cancel","label":"取消","place":"header","level":"danger","intent":"button.execute","visible":["state","in",["draft","confirm"]]}
  ],

  "workflow": {
    "states": ["draft","confirm","done","cancel"],
    "transitions": [
      {"from":"draft","to":"confirm","by":"action_confirm"},
      {"from":"confirm","to":"cancel","by":"action_cancel"}
    ]
  },

  "collab": {
    "chatter": {"enabled": true},
    "activity": {"enabled": true},
    "attachments": {"enabled": true}
  },

  "reports": [
    {"name":"project_report","label":"项目报表","type":"qweb-pdf","action_id":1234}
  ],

  "ui": {
    "i18n": {"empty_state":"暂无数据","help":"填写完整后提交"},
    "shortcuts": [{"key":"Ctrl+S","action":"form.save"}],
    "responsive": {"mobile":["kanban","form"],"desktop":["tree","form"]}
  },

  "data": {
    "type": "records|record|groups|pivot|calendar|gantt|kpis",
    "records": [],
    "total": 123,
    "next_offset": 50,
    "kpis": [{"key":"sum_amount","label":"总金额","value":123456.78}]
  }
}
```

### 关键域说明

- **views.\*.modifiers**：字段/列的动态规则，语法沿用 Odoo `attrs`/domain 表达式，例如：`{"readonly":["state","in",["done","cancel"]]}`。  
- **search.filters / group_by**：直接渲染搜索面板，不再推理。  
- **data**：根据请求参数与视图类型返回对应数据形态；分页通过 `limit/offset` 与 `next_offset` 协同。  
- **permissions/rules**：服务端汇总访问控制与 ir.rule 的默认域、默认排序，前端可渲染禁用态。

---

## 四、导航契约（Nav Contract）

`subject:'nav'` 返回标准化菜单树（**叶子即可点击**；不强依赖 `action/head`）：

```json
{
  "nav": [
    {
      "id": 382, "name": "施工企业管理", "children": [
        { "id": 394, "name": "工作台", "children": [] },
        { "id": 383, "name": "项目", "children": [
          { "id": 392, "name": "项目列表", "children": [] }
        ]}
      ]
    }
  ]
}
```

> 前端将**所有叶子**注入为路由 `/m/:menuId`，点击后用 `subject:'menu'` 打契约；若服务端提供 `head/model/action_id` 等，作为补充信息放到 `meta`，但不作为点击前置条件。

---

## 五、后端实现要点

### 5.1 控制器（V2，单一入口）

- **路由**：`POST /api/contract/get`（JSON）  
- **分派**：`subject: nav | menu | action | model`  
- **透传**：`with_data / domain / order / limit / offset / context / measures / groupby / calendar / gantt` 至 service  
- **缓存**：生成 `ETag`（基于版本与关键参数），支持 `If-None-Match` 返回 `304`  
- **错误**：统一 `{ ok:false, error }`

### 5.2 服务：`app.contract.service.generate_contract(...)`

**建议签名：**

```python
def generate_contract(
  model_name,
  view_type='tree,form',
  view_id=None,
  record_id=None,
  with_data=False,
  domain=None, order=None, limit=None, offset=None,
  measures=None, groupby=None,       # pivot/graph
  calendar=None, gantt=None,         # 日历/甘特字段
  context=None
) -> {"status","data","meta"}
```

**职责：**

- 聚合 `app.model.config / app.view.config / app.action.config / app.permission.config / app.security.rule.config / app.workflow.config`  
- 产出 2.0 结构：`head / permissions / rules / search / views / fields / buttons / workflow / collab / reports / ui`  
- 若 `with_data=True`，根据 `view_type` 返回 `data`（`search_read`、`read`、`read_group` 等）  
- 计算 `version/etag`（元数据 + 视图版本 + 权限版本 + 搜索版本 + 动作版本）  

---

## 六、前端对接指南（要点）

1. **登录后**：`POST /api/contract/get { subject:'nav' }` → 取树 → **叶子即注入**。  
2. **点击叶子**：跳 `/m/:menuId` → `POST /api/contract/get { subject:'menu', id, with_data:true }`。  
3. **AutoPage 渲染**：  
   - 用 `views[active] + fields + modifiers` 渲染；  
   - `search` 渲染筛选与分组；  
   - 用 `data` 显示列表/表单/聚合；分页修改 `limit/offset` 再调同接口。  
4. **按钮执行**：`intent` 执行成功后，再次 `contract.get` 刷新。  
5. **缓存**：带上 `If-None-Match: <etag>`，命中则 304；前端应维护契约缓存。  
6. **路由注入**：父路由名保持一致（如 `'RootLayout'`）；注入时仅依赖叶子 `menu_id`。

---

## 七、迁移指南（1.0 ➜ 2.0）

- **移除**：`GET /api/v1/contract`（仅 `model_code`）与 `/api/menu/tree`。  
- **新增**：`POST /api/contract/get`；前端改为 `contractGet(body)`。  
- **menuStore ➜ navStore**：只走 `subject:'nav'`；注入规则“叶子即注入”。  
- **AutoPage**：将“取契约 + 数据”合并为一次 `contract.get` 调用。  
- **按钮**：保留 `intent` 调用；执行后刷新契约。  
- **测试**：所有页面“零推理渲染、首屏无额外 API”通过。

---

## 八、测试与发布清单

- ✅ **契约完整性**：`head / permissions / rules / search / views / fields / buttons / workflow / collab / reports / ui / data` 均返回。  
- ✅ **首屏无额外请求**：开启 `with_data` 后渲染完整。  
- ✅ **动态规则**：`modifiers` 的 `invisible/readonly/required` 在表单/列表生效。  
- ✅ **分页/筛选**：`domain/order/limit/offset` 正常。  
- ✅ **多视图**：`tree/form/pivot/calendar/gantt/graph` 可切换。  
- ✅ **缓存**：ETag 命中率可观（返回 304）。  
- ✅ **权限**：契约权限与数据权限一致。  
- ✅ **安全**：接口 `auth='user'`；敏感字段按权限过滤。

---

## 九、性能优化建议

- many2one 值域：**懒加载 + 缓存**；selection：全局缓存。  
- 大表分页：限制 `limit`，提供 `next_offset`。  
- `search_read` 字段列：优先 `views.tree.columns` + must-have（`id`/`display`）。  
- `read_group` 仅在 pivot/graph 请求时执行。  
- ETag 维度仅包含“契约相关”与“关键查询参数”。  
- 可在 `meta` 增加 `elapsed_ms / cache_hit / warn` 便于观测。

---

## 十、附录：表达式与语法

- **Domain**：沿用 Odoo 语法（数组表达式）。  
- **Modifiers**：`{"readonly": <domain>, "invisible": <domain>, "required": <domain>}`。  
- **Group By 语法**：`"field[:granularity]"`（如 `"create_date:month"`）。  
- **Measure 语法**：`"field[:agg]"`（如 `"amount_total:sum"`）。  
- **按钮**：`{ name, label, place:'header'|'row', level:'info'|'danger', intent:'button.execute', visible?:<domain> }`。

---

## License

如无特殊说明，本规范文档遵循内部共享许可；对外发布前请先进行安全与合规审查。

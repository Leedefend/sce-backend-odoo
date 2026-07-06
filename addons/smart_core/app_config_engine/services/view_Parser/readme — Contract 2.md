# Contract 2.0 视图解析器

> 目标：**零推理渲染**、**保真解析**、**标准输出**、**稳健降级**

本目录是 `app.view.parser` 的 Odoo 原生视图解析入口。它只解析 Odoo 原生结构并输出契约 2.0 所需的结构化数据，不做运行态治理、不定义产品化表单布局、不拥有业务事实。

## Legacy Filesystem Boundary

当前目录名和部分文件名保留历史形态：`view_Parser`、`contract_Parser.py`、`parsers Tree Form.py`、`parsers Kanban Pivot Graph.py`、`parsers_Calendar_Gantt Activity.py`。

这些名称是兼容边界，不是新代码命名规范。入口 `contract_Parser.py` 必须通过 `LEGACY_MIXIN_MODULES` 和 `_load_legacy_mixin()` 集中加载旧 mixin 文件，避免在其他位置散落动态导入字符串。

## 目录结构

```
services/view_Parser/
├── contract_Parser.py                  # 对外入口，Odoo 模型 `app.view.parser`
├── base.py                             # 通用工具 & XML 保真解析 & toolbar/modifiers
├── parsers Tree Form.py                # tree / form 解析 + 表单布局 + 按钮归一
├── parsers Kanban Pivot Graph.py       # kanban / pivot / graph 解析
├── parsers_Calendar_Gantt Activity.py  # calendar / gantt / activity / search 合并
└── __init__.py                         # 注册 `app.view.parser`
```

## 安装与接入

现有调用处保持不变：

* `self.env['app.view.parser'].parse_odoo_view(model_name, view_type)`

解析过程必须使用当前请求用户环境，不能在解析入口默认 `sudo()`，否则 Odoo group-based 视图裁剪会和原生客户端不一致。

## 关键增强点（对齐近期讨论）

* **`_merge_search`**：合并主视图 & 独立 search 视图的 `filters/group_by`，去重保序，兼容 `context` 中的 group\_by 列表/字符串。
* **能力位（capabilities）**：按视图类型输出可直接驱动 UI 的开关，如 `tree.inline_edit/can_create/can_delete`、`kanban.quick_create`、`calendar.event_open_popup` 等。
* **列元信息（columns\_schema）**：在 `tree.columns`（兼容数组）基础上，提供每列的 widget/optional/sum/modifiers 细节。
* **表单布局（layout）**：将保真 XML 结构转换成 UI 可渲染布局树（sheet/group/page/field/button 等），并附带字段元信息。
* **按钮统一（button→action）**：`object/action/url/workflow` 统一为 `open/server/url` 语义；选择模式兜底；保留 `confirm/context/domain/options` 原文。
* **保真 + 降级**：`parsed_structure`（保真 XML）与 `original_odoo_view`（可序列化快照）齐备；任一子解析失败不抛出，全链路可降级。
* **日志锚点**：`VIEW_PARSER_DEBUG` / `TREE_PARSER_DEBUG` 等便于排障；与上层 `app_view_config` 的日志对齐。

## 输出契约（单视图）

```jsonc
{
  "id": "project.task_tree",
  "model": "project.task",
  "view_type": "tree",
  "original_odoo_view": {"arch": "...", "fields": {...}, "toolbar": {...}},
  "parsed_structure": { /* 保真 XML 字典 */ },

  "toolbar": {"header": [...], "sidebar": [...], "footer": []},
  "search": {"filters": [...], "group_by": ["stage_id"], "facets": {"enabled": true}},
  "order": "priority desc, sequence, date_deadline asc, id desc",  // tree 优先用 default_order
  "modifiers": {"field": {"readonly": [...], "required": [...], "invisible": [...]}},

  // 各视图特有块（示例：tree）
  "columns": ["id", "name", "stage_id", ...],
  "columns_schema": [{"name":"name","widget":"char","optional":"show"}, ...],
  "row_actions": [...],
  "row_classes": [{"class":"danger","expr_raw":"state=='blocked'"}],
  "page_size": 50,
  "capabilities": {"inline_edit": true, "can_create": true, "can_delete": false}
}
```

## 兼容性

* 兼容 `model.get_view` 与 `fields_view_get(toolbar=True)` 两种来源。
* 支持视图类型：`tree/form/kanban/pivot/graph/calendar/gantt/activity/search`。
* `view_type` 可传 `"tree,form"` 或列表 `['tree','form']`，返回聚合对象。

# 阶段 2 导入与层级重构设计（文档先行）

目标：在不改变业务行为的前提下，重构导入解析架构，增强章节识别与层级稳定性，奠定后续 display_order / parent_path 稳定排序基础。阶段 2 仅搭框架，不变更现有视图/逻辑输出。

## 任务分解

### 任务 2.1：导入引擎拆解（Parser Engine）
- 新类 `BoqParser`（置于 wizard 内部）：
  - `__init__(wizard)`
  - `parse_file(data, filename)`
  - `parse_sheet(sheet, sheet_index)`
  - `parse_rows(data_rows)`
- `RowParser` 抽取：`parse_row(raw_row, col_map)`，便于按清单类别定制。
- Wizard 主流程调用 Parser：`parser.parse_file(...)` 返回 rows/created_uoms/skipped。
- 不负责 parent_id/层级，仅产出结构化行数据。

**中间数据结构规范（Parser → Wizard）**  
统一的行字典结构，便于后续扩展/日志定位/排序：
```json
{
  "name": str,
  "code": str | null,
  "qty": float | null,
  "uom": str | null,
  "price": float | null,
  "amount": float | null,
  "division_name": str | null,
  "category": str,
  "line_type": str,
  "origin_row_index": int  // 重要：用于日志、错误提示、display_order 生成
}
```

### 任务 2.2：章节预解析（Chapter Layer v0）
- 合并单元格标题区解析：`parse_merged_title_area(sheet)`，输出 major/division/subtitle 信息（仅收集，不推断）。
- 分部标题捕获增强：优先使用标题区，其次样式/关键字（工程/绿化/市政/道路），改善 division_name 识别。
- 章节池（Chapter Pool v0）：收集所有章节/标题文本（无数量/编码）供后续阶段使用，不参与当前层级决策。

### 任务 2.3：层级推导框架（Hierarchy Framework）
- `HierarchyBuilder` 栈管理：
  - `stack: level -> record`
  - `place(rec, level)`: parent = stack[level-1]; rec.parent_id = parent 或 False；stack[level] = rec。
- 层级来源优先级框架（暂不启用新算法）：
  - code-based（已有）
  - title-based（章节池，标记 TODO 阶段 3）
  - fee-based（金金额型 total/fee/tax 规则）
  - fallback item
- display_order 协议：约定格式 `001.003.005`（L1-L2-L3），本阶段仅文档协议，不写值。
- parent_path 统一刷新接口：`refresh_parent_path(project_id)`，在 `_create_with_hierarchy` 尾部调用，确保层级一致性。
- 预留层级修复接口：`heal_hierarchy(records)`，用于后续（阶段 4）自动修复层级连续性/断层，当前仅定义接口。

## 清单类别管线（六类）
- `boq`：分部分项，编码驱动层级。
- `unit_measure`：单价措施，平铺/或复用编码层级（保持现状，框架化）。
- `total_measure` / `fee` / `tax`：金额型费用，保持现有分组/过滤规则，框架化放入 Parser/Builder。
- `other`：其他项目清单，保留现有层级规则，纳入统一管线。

## 边界与不变原则（阶段 2）
- 不修改现有业务行为（层级判定、视图表现、导入规则输出保持不变）。
- 新增的章节池、标题解析、display_order 协议仅存文档/框架，不改数据。
- 代码重构聚焦可维护性与稳定性：职责拆分、统一入口、可单测。

## 后续阶段提示（阶段 3 展望）
- 启用 title-based 层级推断、章节池匹配。
- 生成 display_order 并用于排序。
- 增强层级校验/重建工具，支持 parent_path 与序号重算。

## 实施状态（2025-12-XX）
- BoqParser / RowParser 骨架已实现，仍委托原有解析函数，未改导入行为。
- chapter_pool / parse_merged_title_area 已实现，占位收集标题文本，不参与层级决策。
- HierarchyBuilder 已实现 place/reset/refresh_parent_path/heal_hierarchy 占位，未改现有层级算法。
- is_group / hierarchy_code / display_order 字段已在模型与视图中露出（只读、可隐藏），未参与逻辑。
- 行为验证：导入结果（行数、层级结构、金额汇总）与 Phase-0/1 一致。
- 结论：Phase-2 作为“导入与层级重构骨架”已完成，业务行为保持稳定。

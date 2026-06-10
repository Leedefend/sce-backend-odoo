# 施工日志验收字段正式承接审计

日期：2026-06-10

## 范围

本轮只处理用户已确认菜单体系下的 `施工日志` 正式业务模型字段承接，不调整菜单体系、不改变用户已验收列表口径。

验收面字段：

- `legacy_visible_07`：出勤机械
- `legacy_visible_08`：备注

正式业务字段：

- `attendance_equipment`：出勤机械
- `note`：备注

## 本地执行结果

数据库：`sc_demo`

专项回填：

- 施工日志记录数：3233
- 出勤机械来源非空：110
- 出勤机械来源为空：3123
- 出勤机械正式字段缺失：0
- 备注来源非空：502
- 备注来源为空：2731
- 备注正式字段缺失：0

专项审计：

```text
CONSTRUCTION_DIARY_VISIBLE_FIELDS_AUDIT: PASS
source_count=3233
source_equipment_count=110
source_equipment_projected_count=110
source_equipment_missing_count=0
source_note_count=502
source_note_projected_count=502
source_note_missing_count=0
```

全量发布闸门：

```text
FORMAL_BUSINESS_RELEASE_GATE_RESULT: PASS
started_at=2026-06-10T09:37:48+08:00
finished_at=2026-06-10T09:40:18+08:00
```

用户确认菜单数据对齐：

- 菜单数：62
- 覆盖记录数：256844
- 覆盖字段数：862
- 错位字段数：0
- 状态：PASS

## 告警分类

`visible_data_usability_warning_classification.py` 已把施工日志 `legacy_visible_07,legacy_visible_08` 归类为：

```text
covered_by_construction_diary_visible_fields_gate
```

剩余未关闭项为来源录入人、来源录入时间等元数据门禁项，不属于本轮正式办理字段承接范围。

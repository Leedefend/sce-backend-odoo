# Project Specialty Type Mapping v1

## Source Summary

- Rows scanned: 755
- Non-empty rows: 755
- Unique legacy specialty IDs: 37
- Unique legacy specialty names: 36
- Runtime dictionary candidates:
  - `project_type`: `施工项目`, `设计项目`, `运维项目`, `市政工程`, `房建工程`
  - `project_category`: `房建`, `市政`, `机电`, `产业园区`, `公共配套`

## Exact Dictionary Coverage

| Legacy Name | Rows | Candidate | Match Mode | Confidence | Manual Confirm |
| --- | ---: | --- | --- | --- | --- |
| `房建工程` | 117 | `project_type: 房建工程` | exact | high | no |
| `市政工程` | 134 | `project_type: 市政工程` | exact | high | no |
| `房建` | 30 | `project_category: 房建` | exact | high | no |
| `市政` | 28 | `project_category: 市政` | exact | high | no |

## Candidate But Not Auto-Mapped

| Legacy Name | Rows | Candidate | Match Mode | Confidence | Manual Confirm |
| --- | ---: | --- | --- | --- | --- |
| `机电工程` | 6 | `project_category: 机电` | text_match | medium | yes |
| `机电安装` | 2 | `project_category: 机电` | text_match | medium | yes |
| `土石方工程` | 8 | `sc.dictionary cost_item: 土石方工程` | dictionary | low | yes, target type is not project type/category |
| `土石方` | 1 | `sc.dictionary cost_item: 土石方工程` | text_match | low | yes, target type is not project type/category |

## Uncovered Values

| Legacy Name | Rows |
| --- | ---: |
| `专业分包` | 110 |
| `装修装饰` | 69 |
| `劳务工程` | 65 |
| `装饰装修` | 33 |
| `水利工程` | 45 |
| `电力工程` | 17 |
| `公路工程` | 28 |
| `公路交通` | 14 |
| `水利水电工程` | 11 |
| `消防工程` | 7 |
| `劳务分包` | 5 |
| `园林绿化工程` | 4 |
| `内部` | 3 |
| `桥梁隧道` | 2 |
| `消防设施` | 2 |
| `建筑防水` | 2 |
| `农田水利` | 1 |
| `钢结构工程` | 1 |
| `安广公司工程` | 1 |
| `景观土建` | 1 |
| `幕墙设计` | 1 |
| `桥梁工程` | 1 |
| `亮化工程` | 1 |
| `德阳市执法局入库` | 1 |
| `园林绿化` | 1 |
| `保温工程` | 1 |
| `防腐保温` | 1 |
| `钢结构` | 1 |

## Coverage

| Metric | Value |
| --- | ---: |
| exact mapped rows | 309 / 755 = 40.93% |
| exact mapped unique names | 4 / 36 = 11.11% |
| medium-confidence candidate rows | 8 / 755 = 1.06% |
| unresolved rows after exact mapping | 446 |

## Import Readiness

First import may safely preserve `legacy_specialty_type_id` and
`specialty_type_name`. Writing `project_type_id` or `project_category_id` is not
ready for all rows; it needs either new dictionary values or an approved
normalization table.

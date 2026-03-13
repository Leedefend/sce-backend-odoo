# Native View Contract Coverage Matrix v1

| Capability | Form | Tree | Kanban | Search | Status | Contract Uniformity | Priority |
|---|---:|---:|---:|---:|---|---|---|
| Header buttons | ✅ | N/A | N/A | N/A | Supported | High | P0 |
| Stat buttons / button_box | ✅ | N/A | N/A | N/A | Supported | High | P0 |
| Group hierarchy | ✅ | N/A | N/A | N/A | Partial | Medium | P0 |
| Notebook/pages | ✅ | N/A | N/A | N/A | Supported | High | P0 |
| Field modifiers final verdict | ✅ | ✅ | ✅ | N/A | Partial | Medium | P0 |
| x2many structure/subviews | ✅ | N/A | N/A | N/A | Supported | High | P0 |
| Chatter | ✅ | N/A | N/A | N/A | Supported | High | P0 |
| Ribbon/statusbar | ✅ | N/A | N/A | N/A | Partial | Medium | P1 |
| Tree column order | N/A | ✅ | N/A | N/A | Supported | High | P1 |
| Tree row action semantics | N/A | ✅ | N/A | N/A | Supported | High | P1 |
| Kanban card semantic extraction | N/A | N/A | ✅ | N/A | Supported | High | P1 |
| Search filters/group_by/search_fields | N/A | N/A | N/A | ✅ | Supported | High | P1 |
| Searchpanel/Favorites boundary | N/A | N/A | N/A | ✅ | Partial | Medium | P2 |
| Permission explanation reason codes | ✅ | ✅ | ✅ | ✅ | Supported | High | P0 |
| Record-state action gating | ✅ | ✅ | ✅ | N/A | Partial | Medium | P0 |
| Unified semantic page (page/zone/block) | ✅ | ✅ | ✅ | ✅ | Supported | High | P0 |
| `load_view` alias compatibility | ✅ | ✅ | ✅ | ✅ | Supported | High | P0 |

## Notes
- 评分基于后端契约输出与快照守卫，不包含前端视觉验收。
- 当前主链路统一到 `load_contract` 语义出口，`load_view` 仅作为兼容别名。
- 后续 P2 重点：searchpanel 深化、favorites 语义边界、record-state gate 精细化。

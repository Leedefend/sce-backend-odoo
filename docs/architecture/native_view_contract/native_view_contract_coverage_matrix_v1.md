# Native View Contract Coverage Matrix v1

| Capability | Form | Tree | Kanban | Search | Status | Contract Uniformity | Priority |
|---|---:|---:|---:|---:|---|---|---|
| Header buttons | ✅ | N/A | N/A | N/A | Partial | Medium | P0 |
| Stat buttons / button_box | ✅ | N/A | N/A | N/A | Partial | Medium | P0 |
| Group hierarchy | ✅ | N/A | N/A | N/A | Partial | Low | P0 |
| Notebook/pages | ✅ | N/A | N/A | N/A | Partial | Low | P0 |
| Field modifiers final verdict | ✅ | ✅ | ✅ | N/A | Partial | Low | P0 |
| x2many structure/subviews | ✅ | N/A | N/A | N/A | Partial | Low | P0 |
| Chatter | ✅ | N/A | N/A | N/A | Partial | Medium | P0 |
| Ribbon/statusbar | ✅ | N/A | N/A | N/A | Partial | Medium | P1 |
| Tree column order | N/A | ✅ | N/A | N/A | Supported | Medium | P1 |
| Tree batch action semantics | N/A | ✅ | N/A | N/A | Partial | Low | P1 |
| Kanban card semantic extraction | N/A | N/A | ✅ | N/A | Partial | Low | P1 |
| Search filters/group_by | N/A | N/A | N/A | ✅ | Supported | Medium | P1 |
| Searchpanel/favorites boundary | N/A | N/A | N/A | ✅ | Gap | N/A | P2 |
| Permission explanation reason codes | ✅ | ✅ | ✅ | ✅ | Partial | Low | P0 |
| Record-state action gating | ✅ | ✅ | ✅ | N/A | Partial | Low | P0 |
| Unified semantic page (page/zone/block) | ✅ | ✅ | ✅ | ✅ | Gap | N/A | P0 |
| `load_view` multi-view support | ❌ | ❌ | ❌ | ❌ | Gap | N/A | P0 |

## Notes
- 评分基于代码审计而非视觉验收。
- 主要矛盾：能力“有”，但“不在同一个统一契约出口”。

# Native-View-Reuse Driven Frontend Page Design Spec v1

## 1. Objective

This spec standardizes how frontend pages are built in this repo:

`Odoo native views define base structure -> backend normalizes and lifts semantics -> frontend renders from unified contracts -> scene/product layer adds enhancements.`

Scope:
- Odoo backend view parsing
- frontend generic renderers
- scene orchestration
- product enhancement layer

## 2. Core Principles

1. **Native structure first**: if native view already defines field/group/notebook/header/chatter/x2many/modifiers, frontend must not redefine it.
2. **Backend interpretation first**: frontend must not parse XML or infer business semantics.
3. **Generic renderer first**: prioritize shared renderers over page-level hardcoding.
4. **Enhancement as extension**: risk/AI/next-action panels must be injected as extension blocks, not by mutating base renderers.
5. **Consistency first**: Odoo backend and custom frontend must keep consistent semantics, permission outcomes, and status meaning.

## 3. Four-Layer Page Model

1) **Native View Layer**: raw Odoo view facts.
2) **Normalized Structure Layer**: standardized machine-consumable structure.
3) **Semantic Page Layer**: `zone + block` semantics for rendering.
4) **Product Orchestration Layer**: scene/role-specific composition without breaking base semantics.

Recommended zones:
- `header_zone`, `summary_zone`, `detail_zone`, `relation_zone`
- `action_zone`, `collaboration_zone`, `insight_zone`, `attachment_zone`

Recommended blocks:
- `title_block`, `status_block`, `action_bar_block`, `field_group_block`
- `notebook_block`, `relation_table_block`, `stat_button_block`
- `chatter_block`, `attachment_block`, `risk_alert_block`
- `ai_recommendation_block`, `next_action_block`

## 4. Mandatory Delivery Flow

1. Check native view carrying capability first.
2. If UI is insufficient, improve backend semantic output first.
3. Frontend consumes only semantic contracts (`page/zones/blocks/fields/actions/permissions`).
4. Page-level special cases are allowed only for high-value scenarios with explicit rationale.

## 5. Backend Responsibilities

Backend must output:
- base view definition
- structured page contract
- field modifiers
- executable actions
- permission/status interpretation with reason codes

Backend must not:
- dump raw XML and delegate semantic interpretation to frontend
- return only fields + records while omitting structure
- maintain multiple conflicting structure sources for one page

## 6. Frontend Responsibilities

Frontend is responsible for:
- structural rendering
- component mapping
- interaction and feedback
- form input management
- submit/refresh lifecycle
- extension slot rendering

Frontend must not:
- parse Odoo XML
- infer permissions/action availability
- rebuild business partitioning by guesswork
- override native semantic order with ad-hoc field order

## 7. Governance

### New page checklist
1. Is native view sufficient for base layout?
2. Is backend semantic output complete?
3. Is this requirement generic rendering or product enhancement?
4. Is a page special-case truly necessary?
5. Will this break renderer consistency?

### Implementation priority
1. Backend parsing/normalization
2. Frontend generic renderers
3. Semantic orchestration
4. Product enhancement
5. Page special-cases

## 8. Enforced Rule for Future Iterations

From this spec onward:
- New page work must start with native-carrying assessment.
- Structure gaps must be fixed in backend semantic output first.
- Frontend page structure must be contract-driven.
- Any page special-case must include entry criteria and exit criteria in iteration notes.

## 9. One-Line Policy

Native Odoo views define the base page structure, backend provides unified semantics, frontend renders generically, and high-value scenes receive product enhancements.


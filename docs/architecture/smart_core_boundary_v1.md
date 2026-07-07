# Smart Core Boundary V1

`addons/smart_core` 是平台内核模块。它提供契约、意图、配置、权限、交付、场景和运行时治理能力，但不拥有任何行业业务事实。

本文件用于固化 `smart_core` 的目录级职责边界。后续表单、列表、搜索、菜单、场景、发布能力迭代，必须先判断变更落在哪个目录和权威层，不能把行业业务逻辑散落到平台管线里。

## Platform Contract

`smart_core` 的平台契约是：

- 提供稳定的 HTTP/intent/contract 运行入口。
- 保真读取 Odoo 原生模型、菜单、动作、视图、权限和上下文。
- 承载低代码配置和业务视图编排的基础模型。
- 把配置、原生结构、权限、场景和用户上下文投影为前端契约。
- 管理平台发布、订阅、公司访问、场景快照和能力治理。
- 提供扩展点，让行业模块供给行业事实、行业菜单和行业场景。

`smart_core` 不做：

- 不定义施工、合同、付款、发票、材料、劳务等行业业务事实。
- 不把某个行业入口的产品化表单 layout 硬编码到平台层。
- 不直接维护行业模块数据记录的业务生命周期。
- 不绕过 `ui.business.config.contract`、扩展点或正式模型边界写入产品化配置。
- 不把 `smart_construction_core` 作为 manifest 依赖。

## Directory Ownership

| Directory | Responsibility | Authority | Must Not Own |
| --- | --- | --- | --- |
| `controllers` | HTTP adapter for platform APIs such as intent, menu, ops, dashboard | Request routing and response transport | Business facts or product layout |
| `handlers` | Intent/API handlers and V2 facade handlers | Runtime operation adapter, request validation, policy calls | Persistent industry business rules |
| `core` | Pure platform builders, routers, source authority, semantic bridges, orchestration utilities | Platform algorithms and contract composition | Industry record semantics |
| `app_config_engine` | `/api/contract/get` runtime contract plumbing | Native parse, page assembly, projection, governance envelope | Product form/list/search authority |
| `model` | Low-code and business configuration infrastructure models | `ui.business.config.contract`, form/menu configuration carriers | Industry module records |
| `models` | Platform operational models | Subscription, product policy, release snapshot, base contract assets | Industry transaction facts |
| `delivery` | Product delivery and release services | Menu/product policy projection, release snapshot, operator surface | Industry process truth |
| `governance` | Scene and capability governance engines | Drift checks, normalization, capability surface | Business transaction mutation |
| `orchestration` | Scene/slice orchestrator adapters | Scene contract orchestration scaffolding | Hard-coded tenant facts |
| `runtime` | Runtime degrade and execution support | Runtime safety and degradation decisions | Product definition |
| `security` | Platform auth, intent permission, platform admin, company access | Permission evaluation and platform groups | Industry role taxonomy ownership |
| `identity` | Request/user identity resolution | Identity projection | Industry profile records |
| `adapters` | Odoo adapter helpers | Conversion and cleanup around Odoo primitives | Business policy |
| `utils` | Shared policy and utility helpers | Cross-cutting constants, idempotency, governance helpers | Feature-specific ownership |
| `view` | Native/universal view parsing utilities | Parse/projection support | Runtime governance or layout decisions |
| `data`, `views` | Platform seed data and platform admin views | Platform menus, subscriptions, release/config views | Industry menus outside explicit compatibility |
| `tests` | Platform regression tests | Test doubles and boundary regression | Runtime source of truth |

## Authority Layers

### Native Odoo Authority

Odoo models, fields, views, actions, menus, ACL and record rules remain the native structural authority. `smart_core` can parse and project them, but should not silently invent conflicting structure.

### Business Configuration Authority

`ui.business.config.contract` is the canonical carrier for runtime business configuration contracts, including `view_orchestration`.

Product-release form/list/search contracts should express intent through field sets, sections, columns, filters, actions and semantic composition modes. They should not replace the native parser and backend orchestrator with full hand-written UI trees.

### Runtime Contract Authority

`app_config_engine`, `UiContractV2Handler`, unified page contract builders, and scene builders are runtime projection layers. They produce consumable contracts from native Odoo, configuration, security and context.

### Delivery Authority

`delivery` and release-related `models` own product policy, release snapshots, subscription/company access, and release operator read models. They do not own the underlying industry business facts that a product policy exposes.

### Extension Authority

Industry modules may extend platform behavior through declared extension hooks, service adapters, `ui.business.config.contract` data, Odoo model/view/action/menu records, and release policy data. Platform code should prefer extension lookup over direct industry XMLID references.

### Extension Hook Authority

When platform runtime needs an industry-owned default, the authority must be explicit and replaceable:

- extension hook result;
- `ir.config_parameter`;
- `ui.business.config.contract`;
- release/product policy records;
- native Odoo model/view/action/menu records owned by the extension module.

`smart_core` may call these interfaces, but it may not persist the industry-specific value as its own default.

## No Industry Defaults

`smart_core` production code has zero industry defaults.

Forbidden in `smart_core` production code:

- direct `smart_construction_core` module references;
- centralized industry compatibility files;
- hard-coded industry XMLIDs, role prefixes, menu lists, action XMLIDs, root menu IDs, or source database parameter names;
- industry default product keys or brand/root labels such as `construction.standard` and `智慧施工管理平台`;
- construction-specific delivery/product policy branches;
- platform source authority names that imply a construction-only resolver.

Required replacement pattern:

1. The industry module owns the concrete XMLID, role, menu, product key, label, service, and navigation contract.
2. `smart_core` reads it through an extension hook, config parameter, release policy record, or native Odoo record.
3. If no extension/config exists, `smart_core` degrades to platform-neutral behavior instead of silently selecting an industry default.
4. Productized form/list/search behavior lives in industry configuration or `ui.business.config.contract`, not in platform runtime plumbing.

## Form/List/Search Productization Boundary

For productized views:

- Native parse remains in Odoo parser and `app_config_engine` parse services.
- Product intent is declared in `ui.business.config.contract.view_orchestration`.
- `ViewOrchestrator` composes the runtime view from native structure and configuration.
- `app_config_engine` and V2 handlers carry, normalize and expose the composed result.
- Frontend consumes contract output; it should not guess backend actions, model policy or product field authority.

This boundary is the reason `app_config_engine` is a runtime contract pipe, while `ViewOrchestrator` and `ui.business.config.contract` define the productized view contract path.

## Record Context Boundary

平台运行时的中性上下文是 record context，不是某个行业的 project concept。

Required pattern:

- Runtime code should call `selected_record_context_id_from_context` when it needs the selected record context id.
- Menu and navigation contracts should expose `record_scope_policy` with neutral values such as `current_record`, `global`, and `exempt`.
- Legacy `current_project_id`, `project_id`, `project_scope_policy`, and `current_project` keys may remain as compatibility aliases for existing frontend routes, Odoo fields, release policies, and persisted configuration.
- Compatibility aliases must map back to the neutral record context contract instead of becoming a second source of truth.
- Industry modules may still own project-specific models, labels, handlers, and fields. `smart_core` only owns the neutral adapter and compatibility bridge.

## Verification

Primary guard:

- `make verify.smart_core.boundary_guard`

Related guards:

- `make verify.app_config_engine.boundary_guard`
- `make verify.lowcode_config.boundary.guard`
- `make verify.view.orchestration_product_boundary_guard`
- `make verify.business_form.productization.audit`
- `make verify.view.orchestration_boundary_guard`
- `make verify.contract_parse_boundary_guard`

The primary guard verifies:

- this document preserves the platform contract, directory ownership, authority layers, no-industry-default rule and productization boundary;
- `smart_core` manifest does not depend on `smart_construction_core`;
- required platform directories remain present;
- production code does not introduce direct `smart_construction_core`, `industry_compatibility`, `legacy_construction`, `construction_source`, `construction.standard`, `智慧施工管理平台`, or `CONSTRUCTION_` defaults;
- the boundary document preserves the neutral record context contract and its legacy project compatibility rule;
- `app_config_engine` has its own local boundary document and guard.
- the low-code platform boundary has a static aggregate gate before runtime/browser acceptance.

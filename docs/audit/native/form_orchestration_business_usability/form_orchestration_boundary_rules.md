# Form Orchestration Boundary Rules

## Layer Ownership

- Business fact model and native business view: owns business fields, labels, required fields, relation metadata, and concrete business section wording.
- Business orchestration contract (`ui.business.config.contract`): owns which business fields participate in a form structure for a given model/action/view scope.
- Platform v2 contract (`smart_core`): owns generic slots, field roles, source trace, permission/runtime projection, and consistency checks. It must not hard-code domain terms such as contract, invoice, machinery, tax deduction, or construction diary sections.
- Frontend renderer: owns generic rendering of the contract. It must not infer missing business facts by model name.

## Gap Routing

- Missing business field, label, required projection, relation metadata, or business identity signal: fix the business fact model, native business view, or `ui.business.config.contract`.
- Structure references a field outside governance, projects an internal field, or layout/structure disagree: fix the orchestration layer or the business orchestration contract, depending on whether the field is absent from governance.
- Contract cannot be produced by intent, handler, parser, or runtime: fix platform infrastructure.
- A field exists in the contract but is not usable in the browser: fix the frontend renderer or relation interaction runtime.

## Prohibited Platform Behavior

- Do not add model-specific section aliases in `smart_core`.
- Do not whitelist business model names in platform contract code.
- Do not add business fields to the contract because an audit expects them. The audit should identify the owner layer; the owner layer supplies the fact or contract.

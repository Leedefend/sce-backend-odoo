# Edition Runtime Routing Model v1

## Goal

Standardize edition runtime routing so `requested edition` and `effective edition` are explicit runtime facts instead of implicit frontend behavior.

## Runtime Priority

1. Route/query edition injection
2. Session requested edition
3. Default `standard`

## system.init Surface

`system.init` now returns `edition_runtime_v1`:

- `requested`
- `effective`
- `diagnostics`

`requested` describes what the client asked for.  
`effective` describes what runtime actually resolved after lifecycle/access fallback.  
`diagnostics` describes why fallback happened, if any.

## Frontend Rules

- Session persists both `requestedEditionKey` and `effectiveEditionKey`.
- Route query only changes `requestedEditionKey`.
- Subsequent runtime intents use:
  - `requestedEditionKey` for `system.init`
  - `effectiveEditionKey` for non-`system.init` intents

## Guardrails

- Preview route must not mutate standard release surface.
- Invalid edition query must be normalized out of the route.
- Unauthorized preview access must fallback to `construction.standard` with diagnostics.

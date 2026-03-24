# Edition Runtime Surface v1

## Status

`runtime-governed`

## Scope

Edition runtime routing on top of existing:

- released navigation
- Delivery Engine v1
- Product Edition Stratification v1
- Edition Lifecycle Governance v1

## Release Surface

- `system.init.edition_runtime_v1`
- frontend session requested/effective edition context
- route/query edition injection
- subsequent runtime intent edition pass-through

## Required Guards

- `make verify.edition.runtime_routing_guard`
- `make verify.edition.session_context_guard`
- `make verify.edition.route_fallback_guard`
- `make verify.release.edition_runtime.v1`

## Runtime Rule

- `requested edition` may be `preview`
- `effective edition` may fallback to `standard`
- fallback must be observable through diagnostics
- fallback must not pollute standard surface

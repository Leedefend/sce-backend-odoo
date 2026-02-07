# ADR-000: Auth Unification (Draft)

Status: Draft (decision deferred)

## Context
The system currently runs dual auth:
- JWT for SPA API calls.
- Odoo session cookies for server-rendered portal pages.

This increases complexity and cross-domain coupling.

## Options
1. JWT-only
   - SPA and portal APIs use JWT exclusively.
   - Portal pages become SPA-native or accept JWT directly.

2. Session-only
   - SPA uses Odoo session cookies.
   - Requires CORS and cookie domain alignment.

## Decision
Deferred until portal pages migrate into SPA or are fully deprecated.

## Preferred Direction
JWT-only, once portal pages are SPA-native.

## Consequences
- Short-term: bridge and token propagation remain.
- Mid-term: portal pages should be migrated to SPA routes.

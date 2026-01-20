# P3 Runtime R1 v0.1

Tag: `p3-runtime-r1-v0.1`

Scope: contract reconciliation summary + audit query runtime + smoke gates.

Verification:
- `make ci.gate.tp08 DB=sc_demo`
- `make p3.smoke DB=sc_p3`
- `make p3.audit DB=sc_p3`

Expected outputs:
- p3.smoke: RECON_ASSERT: PASS, RECON_EXPLAIN present
- p3.audit: AUDIT_QUERY_COUNT >= 1

Commit:
- feat(p3-runtime): finalize R1 v0.1 (recon + audit query + smoke gates)

Known limitations:
- audit actor_login may be __system__ when actions run under sudo.

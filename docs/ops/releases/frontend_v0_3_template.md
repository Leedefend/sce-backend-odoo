# Frontend v0.3 Release Checklist (Template)

## Scope
- [ ] Session/401 handling verified
- [ ] Resolver layer used in views
- [ ] Contract-driven Tree/Form fields
- [ ] Error/loading/empty states
- [ ] Frontend gate passes

## Verification
```bash
pnpm -C frontend install
pnpm -C frontend gate
```

Manual flow:
- [ ] Login → app.init
- [ ] Menu → list → record
- [ ] Refresh preserves session
- [ ] 401 redirects to /login?redirect=...

## Evidence
- [ ] Screenshot / log snippet
- [ ] Trace IDs (if error reproduced)

# Boundary Guardrails (P-1.6)

This guardrail prevents demo assets from leaking back into core/custom/seed.

## Lint Rules

The boundary lint fails if any of these appear in manifests:

- core: dictionary_demo.xml, cost_demo.xml, project_demo_banner_views.xml, demo/sc_demo_users.xml
- custom: role_matrix_demo_users.xml
- seed: sc_demo_showcase_actions.xml

## Run

```bash
make audit.boundary
```

## Expected

- Passes on current P-1 branch.
- Fails immediately if demo assets are reintroduced into core/custom/seed.

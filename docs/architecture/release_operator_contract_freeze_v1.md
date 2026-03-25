# Release Operator Contract Freeze v1

## Goal

Freeze the release operator protocols so that:

- `release_operator_surface_v1`
- `release_operator_read_model_v1`
- `release_operator_write_model_v1`

become versioned product contracts rather than only stable code structures.

## Registry

Registry contract:

- `release_operator_contract_registry_v1`

Registry entries:

- `release_operator_surface`
- `release_operator_read_model`
- `release_operator_write_model`

Each entry declares:

- `contract_key`
- `contract_version`
- `state=frozen`
- `change_rule=version_bump_required`

## Freeze Rule

Any operator protocol change must satisfy:

1. Contract version changes explicitly.
2. Registry entry changes accordingly.
3. Contract guard stays green.

No silent payload drift is allowed.


# Business Admin Config Center Intent Parity v1

- result: `PASS`
- base_url: `http://localhost:8071`
- db: `sc_test`
- session-bootstrap: required and applied for all role probes

## Rows
- role=admin intent_form=16 intent_tree=16 eq_fields=16 required_fields_present=True rights={'read': True, 'write': True, 'create': True, 'unlink': True}
- role=pm intent_form=16 intent_tree=16 eq_fields=16 required_fields_present=True rights={'read': True, 'write': True, 'create': True, 'unlink': False}
- role=finance intent_form=16 intent_tree=16 eq_fields=16 required_fields_present=True rights={'read': True, 'write': False, 'create': False, 'unlink': False}
- role=outsider intent_form=16 intent_tree=16 eq_fields=16 required_fields_present=True rights={'read': False, 'write': False, 'create': False, 'unlink': False}

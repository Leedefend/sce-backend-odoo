# Legacy Payment Approval Downstream Fact Screen v1

## Scope
- Source: legacy approval audit rows plus migration manifests for downstream payment facts.
- Strong downstream evidence: actual outflow rows that reference an outflow payment request.
- Structural detail rows are reported but not counted as approval evidence by themselves.
- Mode: read-only screen; no Odoo business records are mutated.

## Counts
- Raw workflow rows: 163245
- Payment distinct targets: 23316
- Final approval facts: `{"historical_approved": 7, "historical_approved_by_downstream_business_fact": 12194, "historical_pending_or_trace_only": 11115}`
- Downstream-approved targets: 12194
- Downstream-approved trace-only targets: 12194

## Safe Interpretation
- Explicit old audit approval remains historical approval.
- An outflow request referenced by actual outflow is historical approval by downstream business fact.
- Outflow detail lines and receipt invoice lines are structural facts, not approval proof by themselves.

## Key Finding
Old audit status may be incomplete, but actual outflow rows provide direct business evidence that the referenced payment request passed approval and reached execution.

## Top Downstream Evidence Rows
- legacy_outflow_sc_0000fe26abfd4c99aa33351b268c0fc0 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=66000.00
- legacy_outflow_sc_001ebb3a99354849a275c34044e7e20a / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=168403.00
- legacy_outflow_sc_002997205db94d43ba84a560df054679 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=60000.00
- legacy_outflow_sc_002eff22d0e84d9a90c535a42581794d / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=61950.00
- legacy_outflow_sc_0033cf2511ad406b817b550533b0a22e / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=101700.00
- legacy_outflow_sc_00340ff86e71447fbfb4fdc5c81628d7 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=48000.00
- legacy_outflow_sc_0036e9d95a2e4751acb79f9c99b8f878 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=11700.00
- legacy_outflow_sc_003aec86a9544ae785faf3391dfb9b08 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=10000.00
- legacy_outflow_sc_003b091f16bf494f81ac7df5113d48e9 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=52451.41
- legacy_outflow_sc_003ecaa1aa404cb7849bdb3a46fc3844 / lane=outflow_request / final=historical_approved_by_downstream_business_fact / audit=historical_pending_or_trace_only / actual_outflows=1 / amount=682007.00

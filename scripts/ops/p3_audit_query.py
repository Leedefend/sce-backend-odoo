# -*- coding: utf-8 -*-
import json
import os

Audit = env["sc.audit.log"].sudo()

codes_raw = os.environ.get("EVENT_CODES", "")
model = os.environ.get("MODEL")
res_id = os.environ.get("RES_ID")
project_id = os.environ.get("PROJECT_ID")
contract_id = os.environ.get("CONTRACT_ID")
start_ts = os.environ.get("START_TS")
end_ts = os.environ.get("END_TS")

codes = [c.strip() for c in codes_raw.split(",") if c.strip()]

domain = []
if codes:
    domain.append(("event_code", "in", codes))
if model and res_id:
    try:
        domain.append(("model", "=", model))
        domain.append(("res_id", "=", int(res_id)))
    except ValueError:
        pass
if project_id:
    try:
        domain.append(("project_id", "=", int(project_id)))
    except ValueError:
        pass
if contract_id:
    try:
        contract = env["construction.contract"].browse(int(contract_id))
        if contract and contract.project_id:
            domain.append(("project_id", "=", contract.project_id.id))
    except ValueError:
        pass
if start_ts:
    domain.append(("ts", ">=", start_ts))
if end_ts:
    domain.append(("ts", "<", end_ts))

count = Audit.search_count(domain)
record = Audit.search(domain, order="ts desc, id desc", limit=1)

print("AUDIT_QUERY_COUNT: %s" % count)
if record:
    sample = {
        "ts": str(record.ts),
        "event_code": record.event_code,
        "model": record.model,
        "res_id": record.res_id,
        "actor_login": record.actor_login,
        "trace_id": record.trace_id,
        "reason": record.reason,
    }
    print(
        "AUDIT_QUERY_SAMPLE: %s"
        % ("%s %s %s" % (record.event_code, record.model, record.res_id))
    )
    print("AUDIT_QUERY_JSON: %s" % json.dumps(sample, ensure_ascii=True))

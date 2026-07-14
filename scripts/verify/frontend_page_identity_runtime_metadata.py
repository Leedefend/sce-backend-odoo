"""Export audit-only action XML-ID metadata without changing navigation contracts."""

import json

rows = env["ir.model.data"].sudo().search([
    ("model", "in", ["ir.actions.act_window", "ir.actions.client", "ir.actions.report", "ir.actions.server"]),
])
action_xmlids = {}
for row in rows:
    key = str(row.res_id)
    xmlid = "%s.%s" % (row.module, row.name)
    current = action_xmlids.get(key)
    if not current or xmlid.startswith("smart_construction_core."):
        action_xmlids[key] = xmlid

print("FRONTEND_PAGE_IDENTITY_ACTION_XMLIDS_JSON=%s" % json.dumps(action_xmlids, ensure_ascii=True, separators=(",", ":")))

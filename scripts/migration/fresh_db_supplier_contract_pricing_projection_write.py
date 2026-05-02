#!/usr/bin/env python3
"""Project legacy supplier contract pricing facts into formal supplier contracts."""

from __future__ import annotations

import json
import os
from pathlib import Path


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_migration_fresh").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: object) -> str:
    return str(value or "").strip()


ensure_allowed_db()
output_json = artifact_root() / "fresh_db_supplier_contract_pricing_projection_write_result_v1.json"

Fact = env["sc.legacy.supplier.contract.pricing.fact"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821

tax = Contract._get_default_tax("in")
created_projects = []
created_partners = []
created_contracts = 0
updated_facts = 0
skipped_existing = 0
failures = []

facts = Fact.search([], order="legacy_contract_id,id")
for fact in facts:
    existing = Contract.search([("type", "=", "in"), ("legacy_contract_id", "=", fact.legacy_contract_id)], limit=1)
    if existing:
        skipped_existing += 1
        continue
    try:
        project = fact.project_id
        project_ref = clean(fact.project_legacy_id)
        if not project and project_ref:
            project = Project.search(
                ["|", ("legacy_project_id", "=", project_ref), ("legacy_parent_id", "=", project_ref)],
                limit=1,
            )
        if not project and project_ref:
            vals = {"name": clean(fact.project_name) or "历史未归档项目 %s" % project_ref}
            if "legacy_project_id" in Project._fields:
                vals["legacy_project_id"] = project_ref
            if "legacy_parent_id" in Project._fields:
                vals["legacy_parent_id"] = project_ref
            project = Project.create(vals)
            created_projects.append(project_ref)

        partner = fact.partner_id
        partner_ref = clean(fact.partner_legacy_id)
        partner_name = clean(fact.partner_name)
        if not partner and partner_ref and "legacy_partner_id" in Partner._fields:
            partner = Partner.search([("legacy_partner_id", "=", partner_ref)], limit=1)
        if not partner and partner_name:
            partner = Partner.search([("name", "=", partner_name)], limit=1)
        if not partner:
            partner = Partner.create(
                {
                    "name": partner_name or "历史供应商 %s" % (partner_ref or fact.legacy_contract_id),
                    "supplier_rank": 1,
                    **({"legacy_partner_id": partner_ref} if partner_ref and "legacy_partner_id" in Partner._fields else {}),
                }
            )
            created_partners.append(partner_ref or partner_name or fact.legacy_contract_id)

        if not project or not partner:
            failures.append({"legacy_contract_id": fact.legacy_contract_id, "reason": "project_or_partner_anchor_unavailable"})
            continue

        contract = Contract.create(
            {
                "legacy_contract_id": fact.legacy_contract_id,
                "legacy_project_id": project_ref,
                "legacy_counterparty_text": partner_name,
                "legacy_status": clean(fact.document_state),
                "legacy_deleted_flag": clean(fact.deleted_flag),
                "subject": "历史供应合同 %s" % (partner_name or fact.legacy_contract_id),
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
                "tax_id": tax.id,
                "note": (
                    "[migration:supplier_contract_pricing] legacy_contract_id=%s; "
                    "pricing_method=%s; amount_total=%s; historical_runtime_projection=true"
                )
                % (fact.legacy_contract_id, clean(fact.pricing_method_text), fact.amount_total or 0.0),
            }
        )
        if fact.project_id != project or fact.partner_id != partner:
            fact.write({"project_id": project.id, "partner_id": partner.id})
            updated_facts += 1
        created_contracts += 1
        if created_contracts % 200 == 0:
            env.cr.commit()  # noqa: F821
    except Exception as exc:
        failures.append(
            {
                "legacy_contract_id": fact.legacy_contract_id,
                "error": "%s: %s" % (type(exc).__name__, str(exc)[:240]),
            }
        )

env.cr.commit()  # noqa: F821

total_facts = Fact.search_count([])
target_contracts = Contract.search_count([("type", "=", "in"), ("legacy_contract_id", "!=", False)])
payload = {
    "status": "PASS" if not failures else "WARN",
    "mode": "fresh_db_supplier_contract_pricing_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "legacy_total": total_facts,
    "target_supplier_contracts_with_legacy_id": target_contracts,
    "created_contracts": created_contracts,
    "skipped_existing": skipped_existing,
    "created_placeholder_project_count": len(created_projects),
    "created_placeholder_partner_count": len(created_partners),
    "updated_fact_anchor_count": updated_facts,
    "failed_count": len(failures),
    "created_placeholder_project_refs_sample": created_projects[:20],
    "created_placeholder_partner_refs_sample": created_partners[:20],
    "failures": failures[:20],
    "db_writes": created_contracts + len(created_projects) + len(created_partners) + updated_facts,
    "decision": "legacy_supplier_contract_pricing_projected_to_supplier_contracts",
}
write_json(output_json, payload)
print("SUPPLIER_CONTRACT_PRICING_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

#!/usr/bin/env python3
"""Create a sensitive-free migration-safety fingerprint through isolated Compose."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


COUNT_TABLES = {
    "companies": "res_company",
    "users": "res_users",
    "partners": "res_partner",
    "projects": "project_project",
    "contracts": "construction_contract",
    "settlements": "sc_settlement_order",
    "payment_requests": "payment_request",
    "payment_executions": "sc_payment_execution",
    "ledgers": "sc_treasury_ledger",
    "attachments": "ir_attachment",
}
AMOUNT_FIELDS = {
    "contracts": ("construction_contract", "contract_amount"),
    "settlements": ("sc_settlement_order", "settlement_amount"),
    "payment_requests": ("payment_request", "request_amount"),
    "payment_executions": ("sc_payment_execution", "payment_amount"),
    "ledgers": ("sc_treasury_ledger", "amount"),
}


def run(command, *, stdin=None):
    return subprocess.run(
        command, check=True, text=True, input=stdin, capture_output=True
    ).stdout.strip()


def canonical_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class Database:
    def __init__(self, project, compose_file, database):
        self.base = ["docker", "compose", "-p", project, "-f", compose_file]
        self.database = database

    def scalar(self, sql):
        return run(
            self.base
            + ["exec", "-T", "db", "psql", "-U", "odoo", "-d", self.database, "-At"],
            stdin=sql,
        )

    def table_exists(self, table):
        return self.scalar(f"SELECT to_regclass('public.{table}') IS NOT NULL") == "t"

    def column_exists(self, table, column):
        sql = (
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            f"WHERE table_schema='public' AND table_name='{table}' AND column_name='{column}')"
        )
        return self.scalar(sql) == "t"

    def filestore(self):
        script = (
            f"root='/var/lib/odoo/filestore/{self.database}'; "
            "if [ ! -d \"$root\" ]; then echo '0|0|e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'; exit; fi; "
            "count=$(find \"$root\" -type f | wc -l); "
            "bytes=$(find \"$root\" -type f -printf '%s\\n' | awk '{s+=$1} END {print s+0}'); "
            "digest=$(find \"$root\" -type f -printf '%P\\0' | sort -z | "
            "while IFS= read -r -d '' f; do sha256sum \"$root/$f\" | awk -v p=\"$f\" '{print p \" \" $1}'; done | sha256sum | awk '{print $1}'); "
            "echo \"$count|$bytes|$digest\""
        )
        raw = run(self.base + ["run", "--rm", "--no-deps", "--entrypoint", "bash", "odoo", "-lc", script])
        count, size, digest = raw.splitlines()[-1].split("|")
        return {"file_count": int(count), "bytes": int(size), "sha256": digest}


def collect(db):
    counts = {}
    id_digests = {}
    for key, table in COUNT_TABLES.items():
        if not db.table_exists(table):
            counts[key] = None
            id_digests[key] = None
            continue
        counts[key] = int(db.scalar(f'SELECT count(*) FROM "{table}"'))
        id_digests[key] = db.scalar(
            f'SELECT md5(COALESCE(string_agg(id::text,\',\' ORDER BY id),\'\')) FROM "{table}"'
        )

    amounts = {}
    for key, (table, column) in AMOUNT_FIELDS.items():
        if db.table_exists(table) and db.column_exists(table, column):
            amounts[key] = db.scalar(f'SELECT COALESCE(sum("{column}"),0)::text FROM "{table}"')
        else:
            amounts[key] = None

    demo_user_sql = (
        "SELECT COALESCE(string_agg(res_id::text,',' ORDER BY res_id),'') FROM ir_model_data "
        "WHERE module='smart_construction_demo' AND model='res.users'"
    )
    demo_user_ids = [int(value) for value in db.scalar(demo_user_sql).split(",") if value]
    id_list = ",".join(map(str, demo_user_ids)) or "0"

    audit_columns = db.scalar(
        "SELECT table_name||'.'||column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND column_name IN ('create_uid','write_uid') ORDER BY 1"
    ).splitlines()
    audit_queries = []
    for item in audit_columns:
        table, column = item.split(".", 1)
        audit_queries.append(
            f'SELECT count(*)::bigint AS n FROM "{table}" WHERE "{column}" IN ({id_list})'
        )
    audit_reference_count = int(
        db.scalar(
            "SELECT COALESCE(sum(n),0) FROM (" + " UNION ALL ".join(audit_queries) + ") refs"
        )
    ) if audit_queries else 0

    approval_columns = db.scalar(
        "SELECT table_name||'.'||column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND column_name IN "
        "('approved_by','approver_id','approved_by_user_id') ORDER BY 1"
    ).splitlines()
    approval_queries = []
    for item in approval_columns:
        table, column = item.split(".", 1)
        approval_queries.append(
            f'SELECT count(*)::bigint AS n FROM "{table}" WHERE "{column}" IN ({id_list})'
        )
    approval_reference_count = int(
        db.scalar(
            "SELECT COALESCE(sum(n),0) FROM (" + " UNION ALL ".join(approval_queries) + ") refs"
        )
    ) if approval_queries else 0

    relationships = {
        "demo_user_count": len(demo_user_ids),
        "create_write_audit_references": audit_reference_count,
        "approval_references": approval_reference_count,
        "project_owner_manager_references": 0,
        "followers": 0,
        "company_relations": 0,
    }
    if db.table_exists("project_project"):
        project_columns = [column for column in ("user_id", "manager_id") if db.column_exists("project_project", column)]
        if project_columns:
            predicate = " OR ".join(f'"{column}" IN ({id_list})' for column in project_columns)
            relationships["project_owner_manager_references"] = int(
                db.scalar(f'SELECT count(*) FROM project_project WHERE {predicate}')
            )
    if db.table_exists("mail_followers") and db.table_exists("res_users"):
        relationships["followers"] = int(
            db.scalar(
                "SELECT count(*) FROM mail_followers WHERE partner_id IN "
                f"(SELECT partner_id FROM res_users WHERE id IN ({id_list}))"
            )
        )
    if db.table_exists("res_company_users_rel"):
        relationships["company_relations"] = int(
            db.scalar(f"SELECT count(*) FROM res_company_users_rel WHERE user_id IN ({id_list})")
        )

    xmlids = {
        "count": int(
            db.scalar("SELECT count(*) FROM ir_model_data WHERE module='smart_construction_demo'")
        ),
        "digest": db.scalar(
            "SELECT md5(COALESCE(string_agg(name||':'||model||':'||res_id::text,',' ORDER BY name,model,res_id),'')) "
            "FROM ir_model_data WHERE module='smart_construction_demo'"
        ),
    }
    module_states = db.scalar(
        "SELECT name||'='||state||'='||COALESCE(latest_version,'') FROM ir_module_module "
        "WHERE name IN ('smart_construction_demo','smart_construction_seed','smart_core',"
        "'smart_construction_core','smart_construction_portal','smart_construction_custom') ORDER BY name"
    ).splitlines()
    protected = {
        "counts": counts,
        "id_digests": id_digests,
        "amounts": amounts,
        "relationships": relationships,
        "demo_xmlids": xmlids,
        "filestore": db.filestore(),
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": db.database,
        **protected,
        "module_states": module_states,
        "protected_fingerprint_sha256": canonical_hash(protected),
        "sensitive_values_included": False,
        "database_writes": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="sc-production-blocker-matrix")
    parser.add_argument("--compose-file", default="docker-compose.migration-safety.yml")
    parser.add_argument("--database", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = collect(Database(args.project, args.compose_file, args.database))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        f"[migration_safety_fingerprint] database={args.database} "
        f"fingerprint={payload['protected_fingerprint_sha256']}"
    )


if __name__ == "__main__":
    main()

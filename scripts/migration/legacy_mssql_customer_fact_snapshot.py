#!/usr/bin/env python3
"""Export customer business fact candidates from the restored legacy MSSQL DB."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


QUERY = r"""
SET NOCOUNT ON;
WITH facts AS (
    SELECT
        'T_ProjectContract_Out' AS source_table,
        'FBF' AS source_field,
        '' AS legacy_partner_id,
        LTRIM(RTRIM(FBF)) AS name,
        COUNT_BIG(*) AS fact_row_count,
        COALESCE(SUM(CAST(f_YZXMJE AS decimal(18, 2))), 0) AS fact_amount
    FROM T_ProjectContract_Out
    WHERE COALESCE(DEL, 0) = 0 AND NULLIF(LTRIM(RTRIM(FBF)), '') IS NOT NULL
    GROUP BY LTRIM(RTRIM(FBF))
    UNION ALL
    SELECT
        'C_JFHKLR',
        'WLDWMC',
        COALESCE(NULLIF(LTRIM(RTRIM(WLDWID)), ''), ''),
        LTRIM(RTRIM(WLDWMC)),
        COUNT_BIG(*),
        COALESCE(SUM(CAST(f_JE AS decimal(18, 2))), 0)
    FROM C_JFHKLR
    WHERE COALESCE(DEL, 0) = 0 AND NULLIF(LTRIM(RTRIM(WLDWMC)), '') IS NOT NULL
    GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(WLDWID)), ''), ''), LTRIM(RTRIM(WLDWMC))
    UNION ALL
    SELECT
        'C_CWSFK_GSCWSR',
        'FKDW',
        COALESCE(NULLIF(LTRIM(RTRIM(FKDWID)), ''), ''),
        LTRIM(RTRIM(FKDW)),
        COUNT_BIG(*),
        COALESCE(SUM(CAST(JZJE AS decimal(18, 2))), 0)
    FROM C_CWSFK_GSCWSR
    WHERE COALESCE(DEL, 0) = 0 AND NULLIF(LTRIM(RTRIM(FKDW)), '') IS NOT NULL
    GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(FKDWID)), ''), ''), LTRIM(RTRIM(FKDW))
    UNION ALL
    SELECT
        'XMGL_SRHT_QTSRHT',
        'GMDW',
        COALESCE(NULLIF(LTRIM(RTRIM(GMDWID)), ''), ''),
        LTRIM(RTRIM(GMDW)),
        COUNT_BIG(*),
        COALESCE(SUM(CAST(SSJE AS decimal(18, 2))), 0)
    FROM XMGL_SRHT_QTSRHT
    WHERE COALESCE(DEL, 0) = 0 AND NULLIF(LTRIM(RTRIM(GMDW)), '') IS NOT NULL
    GROUP BY COALESCE(NULLIF(LTRIM(RTRIM(GMDWID)), ''), ''), LTRIM(RTRIM(GMDW))
)
SELECT
    facts.source_table,
    facts.source_field,
    facts.legacy_partner_id,
    facts.name,
    facts.fact_row_count,
    facts.fact_amount,
    COALESCE(NULLIF(LTRIM(RTRIM(coop.TYSHXYDM)), ''), NULLIF(LTRIM(RTRIM(coop.SH)), '')) AS tax_no,
    COALESCE(NULLIF(LTRIM(RTRIM(coop.DQMC)), ''), NULLIF(LTRIM(RTRIM(coop.SZS)), '')) AS region,
    LTRIM(RTRIM(COALESCE(coop.ZCZB, ''))) AS registered_capital,
    LTRIM(RTRIM(COALESCE(coop.JYFW, ''))) AS business_scope,
    COALESCE(NULLIF(LTRIM(RTRIM(coop.XXDZ)), ''), NULLIF(LTRIM(RTRIM(coop.LXDZ)), '')) AS address,
    LTRIM(RTRIM(COALESCE(coop.YWLXRXM, ''))) AS contact_name,
    LTRIM(RTRIM(COALESCE(coop.YWLXRHM, ''))) AS contact_phone,
    LTRIM(RTRIM(COALESCE(coop.YWLXRYX, ''))) AS contact_email,
    LTRIM(RTRIM(COALESCE(coop.DGZHYH, ''))) AS bank_name,
    LTRIM(RTRIM(COALESCE(coop.DGZHHM, ''))) AS bank_account,
    LTRIM(RTRIM(COALESCE(coop.DGZHMC, ''))) AS bank_account_name,
    LTRIM(RTRIM(COALESCE(coop.DJBH, ''))) AS partner_code,
    LTRIM(RTRIM(COALESCE(coop.DJZT, ''))) AS document_state,
    LTRIM(RTRIM(COALESCE(coop.LRR, ''))) AS source_operator,
    LTRIM(RTRIM(COALESCE(CONVERT(varchar(19), coop.LRSJ, 120), ''))) AS source_time,
    'T_Base_CooperatCompany' AS profile_source_table
FROM facts
OUTER APPLY (
    SELECT TOP 1 *
    FROM T_Base_CooperatCompany coop
    WHERE COALESCE(coop.DEL, 0) = 0
      AND LTRIM(RTRIM(coop.DWMC)) = facts.name
    ORDER BY
      CASE WHEN NULLIF(LTRIM(RTRIM(COALESCE(coop.TYSHXYDM, coop.SH))), '') IS NOT NULL THEN 0 ELSE 1 END,
      CASE WHEN NULLIF(LTRIM(RTRIM(coop.DQMC)), '') IS NOT NULL THEN 0 ELSE 1 END,
      coop.LRSJ DESC
) coop
ORDER BY source_table, source_field, name, legacy_partner_id;
"""


FIELDS = [
    "source_table",
    "source_field",
    "legacy_partner_id",
    "name",
    "fact_row_count",
    "fact_amount",
    "tax_no",
    "region",
    "registered_capital",
    "business_scope",
    "address",
    "contact_name",
    "contact_phone",
    "contact_email",
    "bank_name",
    "bank_account",
    "bank_account_name",
    "partner_code",
    "document_state",
    "source_operator",
    "source_time",
    "profile_source_table",
]


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.lower() in {"null", "none", "nan"} else text


def run_sqlcmd(container: str, database: str, password: str) -> str:
    command = [
        "docker",
        "exec",
        container,
        "/opt/mssql-tools18/bin/sqlcmd",
        "-C",
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        password,
        "-d",
        database,
        "-W",
        "-h",
        "-1",
        "-s",
        "\t",
        "-Q",
        QUERY,
    ]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError({"command_failed": command[:2] + ["...", "-Q", "QUERY"], "output": proc.stdout})
    return proc.stdout


def resolve_password(container: str, explicit_password: str) -> str:
    if explicit_password:
        return explicit_password
    for env_name in ("LEGACY_MSSQL_SA_PASSWORD", "MSSQL_SA_PASSWORD", "SA_PASSWORD"):
        password = os.environ.get(env_name, "").strip()
        if password:
            return password
    proc = subprocess.run(
        ["docker", "inspect", container, "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            key, _, value = line.partition("=")
            if key in {"MSSQL_SA_PASSWORD", "SA_PASSWORD"} and value.strip():
                return value.strip()
    raise RuntimeError("missing legacy MSSQL SA password; set --password or LEGACY_MSSQL_SA_PASSWORD")


def parse_rows(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip() or line.lstrip().startswith("("):
            continue
        parts = line.split("\t")
        if len(parts) != len(FIELDS):
            continue
        row = {field: clean(value) for field, value in zip(FIELDS, parts, strict=True)}
        if row["name"]:
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", default="legacy-mssql-restore")
    parser.add_argument("--database", default="LegacyDb")
    parser.add_argument("--password", default="")
    parser.add_argument("--out", default="artifacts/migration/legacy_mssql_customer_business_fact_candidates_v1.csv")
    parser.add_argument("--result", default="artifacts/migration/legacy_mssql_customer_business_fact_candidates_result_v1.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        rows = parse_rows(run_sqlcmd(args.container, args.database, resolve_password(args.container, args.password)))
        source_counts = Counter(row["source_table"] + "." + row["source_field"] for row in rows)
        write_csv(Path(args.out), rows)
        result = {
            "status": "PASS",
            "mode": "legacy_mssql_customer_fact_snapshot",
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "database": args.database,
            "row_count": len(rows),
            "source_counts": dict(sorted(source_counts.items())),
            "output": args.out,
            "db_writes": 0,
        }
        write_json(Path(args.result), result)
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0}
        print("LEGACY_MSSQL_CUSTOMER_FACT_SNAPSHOT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("LEGACY_MSSQL_CUSTOMER_FACT_SNAPSHOT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

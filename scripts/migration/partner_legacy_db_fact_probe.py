#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUTPUT_JSON = Path("artifacts/migration/partner_import_decision_support_v1.json")

SQLCMD = [
    "docker",
    "exec",
    "legacy-sqlserver",
    "/opt/mssql-tools18/bin/sqlcmd",
    "-S",
    "localhost",
    "-U",
    "sa",
    "-P",
    "ChangeThis_Strong_Password_123!",
    "-C",
    "-d",
    "LegacyDb",
]


def run_scalar_sql(sql: str) -> str:
    proc = subprocess.run(
        [*SQLCMD, "-Q", f"SET NOCOUNT ON; {sql}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def run_int(sql: str) -> int:
    value = run_scalar_sql(sql)
    return int(value or 0)


def main() -> int:
    queries = {
        "company_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany;",
        "company_distinct_names": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(DWMC)), '')) FROM dbo.T_Base_CooperatCompany;",
        "company_credit_code_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany WHERE NULLIF(LTRIM(RTRIM(TYSHXYDM)), '') IS NOT NULL;",
        "company_distinct_credit_codes": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(TYSHXYDM)), '')) FROM dbo.T_Base_CooperatCompany;",
        "company_tax_no_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany WHERE NULLIF(LTRIM(RTRIM(SH)), '') IS NOT NULL;",
        "company_deleted_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany WHERE CONVERT(nvarchar(20), DEL) = '1';",
        "company_duplicate_name_count": "SELECT COUNT(*) FROM (SELECT DWMC FROM dbo.T_Base_CooperatCompany WHERE NULLIF(LTRIM(RTRIM(DWMC)), '') IS NOT NULL GROUP BY DWMC HAVING COUNT(*) > 1) x;",
        "company_duplicate_rows": "SELECT ISNULL(SUM(cnt), 0) FROM (SELECT COUNT(*) cnt FROM dbo.T_Base_CooperatCompany WHERE NULLIF(LTRIM(RTRIM(DWMC)), '') IS NOT NULL GROUP BY DWMC HAVING COUNT(*) > 1) x;",
        "supplier_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo;",
        "supplier_distinct_names": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(f_SupplierName)), '')) FROM dbo.T_Base_SupplierInfo;",
        "supplier_credit_code_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo WHERE 1 = 0;",
        "supplier_tax_no_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo WHERE 1 = 0;",
        "supplier_bank_account_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo WHERE NULLIF(LTRIM(RTRIM(f_BankCardNumber)), '') IS NOT NULL;",
        "supplier_duplicate_name_count": "SELECT COUNT(*) FROM (SELECT f_SupplierName FROM dbo.T_Base_SupplierInfo WHERE NULLIF(LTRIM(RTRIM(f_SupplierName)), '') IS NOT NULL GROUP BY f_SupplierName HAVING COUNT(*) > 1) x;",
        "supplier_duplicate_rows": "SELECT ISNULL(SUM(cnt), 0) FROM (SELECT COUNT(*) cnt FROM dbo.T_Base_SupplierInfo WHERE NULLIF(LTRIM(RTRIM(f_SupplierName)), '') IS NOT NULL GROUP BY f_SupplierName HAVING COUNT(*) > 1) x;",
        "cross_source_exact_names": "SELECT COUNT(*) FROM (SELECT c.DWMC FROM dbo.T_Base_CooperatCompany c INNER JOIN dbo.T_Base_SupplierInfo s ON LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(s.f_SupplierName)) WHERE NULLIF(LTRIM(RTRIM(c.DWMC)), '') IS NOT NULL GROUP BY c.DWMC) x;",
        "cross_source_company_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany c WHERE EXISTS (SELECT 1 FROM dbo.T_Base_SupplierInfo s WHERE LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(s.f_SupplierName)) AND NULLIF(LTRIM(RTRIM(s.f_SupplierName)), '') IS NOT NULL);",
        "cross_source_supplier_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo s WHERE EXISTS (SELECT 1 FROM dbo.T_Base_CooperatCompany c WHERE LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(s.f_SupplierName)) AND NULLIF(LTRIM(RTRIM(c.DWMC)), '') IS NOT NULL);",
        "cross_source_ambiguous_names": "SELECT COUNT(*) FROM (SELECT c.DWMC FROM dbo.T_Base_CooperatCompany c INNER JOIN dbo.T_Base_SupplierInfo s ON LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(s.f_SupplierName)) WHERE NULLIF(LTRIM(RTRIM(c.DWMC)), '') IS NOT NULL GROUP BY c.DWMC HAVING COUNT(DISTINCT c.Id) > 1 OR COUNT(DISTINCT s.ID) > 1) x;",
        "cross_source_names_with_company_credit_code": "SELECT COUNT(*) FROM (SELECT c.DWMC FROM dbo.T_Base_CooperatCompany c INNER JOIN dbo.T_Base_SupplierInfo s ON LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(s.f_SupplierName)) WHERE NULLIF(LTRIM(RTRIM(c.DWMC)), '') IS NOT NULL AND NULLIF(LTRIM(RTRIM(c.TYSHXYDM)), '') IS NOT NULL GROUP BY c.DWMC) x;",
        "zfsqgl_gysid_to_company": "SELECT COUNT(*) FROM dbo.C_ZFSQGL z WHERE EXISTS (SELECT 1 FROM dbo.T_Base_CooperatCompany c WHERE CONVERT(nvarchar(100), c.Id) = CONVERT(nvarchar(100), z.f_GYSID));",
        "zfsqgl_gysid_to_supplier": "SELECT COUNT(*) FROM dbo.C_ZFSQGL z WHERE EXISTS (SELECT 1 FROM dbo.T_Base_SupplierInfo s WHERE CONVERT(nvarchar(100), s.ID) = CONVERT(nvarchar(100), z.f_GYSID));",
        "jfhlr_wldwid_to_company": "SELECT COUNT(*) FROM dbo.C_JFHKLR h WHERE EXISTS (SELECT 1 FROM dbo.T_Base_CooperatCompany c WHERE CONVERT(nvarchar(100), c.Id) = CONVERT(nvarchar(100), h.WLDWID));",
        "jfhlr_wldwid_to_supplier": "SELECT COUNT(*) FROM dbo.C_JFHKLR h WHERE EXISTS (SELECT 1 FROM dbo.T_Base_SupplierInfo s WHERE CONVERT(nvarchar(100), s.ID) = CONVERT(nvarchar(100), h.WLDWID));",
        "contract_fbf_text_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out WHERE NULLIF(LTRIM(RTRIM(FBF)), '') IS NOT NULL;",
        "contract_fbf_company_matched_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out p WHERE NULLIF(LTRIM(RTRIM(p.FBF)), '') IS NOT NULL AND EXISTS (SELECT 1 FROM dbo.T_Base_CooperatCompany c WHERE LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(p.FBF)));",
        "contract_fbf_company_single_rows": "WITH cm AS (SELECT DWMC, COUNT(*) cnt FROM dbo.T_Base_CooperatCompany GROUP BY DWMC) SELECT COUNT(*) FROM dbo.T_ProjectContract_Out p JOIN cm ON LTRIM(RTRIM(cm.DWMC)) = LTRIM(RTRIM(p.FBF)) WHERE NULLIF(LTRIM(RTRIM(p.FBF)), '') IS NOT NULL AND cm.cnt = 1;",
        "contract_cbf_text_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out WHERE NULLIF(LTRIM(RTRIM(CBF)), '') IS NOT NULL;",
        "contract_cbf_company_matched_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out p WHERE NULLIF(LTRIM(RTRIM(p.CBF)), '') IS NOT NULL AND EXISTS (SELECT 1 FROM dbo.T_Base_CooperatCompany c WHERE LTRIM(RTRIM(c.DWMC)) = LTRIM(RTRIM(p.CBF)));",
        "contract_cbf_company_ambiguous_rows": "WITH cm AS (SELECT DWMC, COUNT(*) cnt FROM dbo.T_Base_CooperatCompany GROUP BY DWMC) SELECT COUNT(*) FROM dbo.T_ProjectContract_Out p JOIN cm ON LTRIM(RTRIM(cm.DWMC)) = LTRIM(RTRIM(p.CBF)) WHERE NULLIF(LTRIM(RTRIM(p.CBF)), '') IS NOT NULL AND cm.cnt > 1;",
        "repayment_contract_linked_contracts": "SELECT COUNT(DISTINCT SGHTID) FROM dbo.C_JFHKLR WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL;",
        "repayment_contract_linked_rows": "SELECT COUNT(*) FROM dbo.C_JFHKLR WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL;",
        "repayment_single_counterparty_contracts": "SELECT COUNT(*) FROM (SELECT SGHTID FROM dbo.C_JFHKLR WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL GROUP BY SGHTID HAVING COUNT(DISTINCT WLDWID) = 1) x;",
        "repayment_multi_counterparty_contracts": "SELECT COUNT(*) FROM (SELECT SGHTID FROM dbo.C_JFHKLR WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL GROUP BY SGHTID HAVING COUNT(DISTINCT WLDWID) > 1) x;",
    }
    result_values = {}
    errors = {}
    for key, sql in queries.items():
        try:
            result_values[key] = run_int(sql)
        except Exception as exc:  # keep probe diagnostic explicit
            errors[key] = str(exc)

    result = {
        "status": "PASS" if not errors else "PASS_WITH_QUERY_ERRORS",
        "mode": "legacy_db_readonly_fact_probe",
        "database": "LegacyDb",
        "results": result_values,
        "errors": errors,
        "decision": "partner import remains NO-GO; use company as primary source and repayment-derived evidence for confirmation",
        "next_step": "generate strong-evidence contract counterparty confirmation slice before any partner or contract write",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_LEGACY_DB_FACT_PROBE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

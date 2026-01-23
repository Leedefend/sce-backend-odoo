import csv
import sys
import traceback


def _safe_str(value):
    return (value or "").strip()


def main():
    if "env" not in globals():
        print("ERROR: Odoo env not found. Run via odoo shell.", file=sys.stderr)
        raise SystemExit(1)

    mail_server_model = env["ir.mail_server"].sudo()
    if hasattr(mail_server_model, "_get_default_mail_server"):
        mail_server = mail_server_model._get_default_mail_server()
    else:
        mail_server = mail_server_model.search([("active", "=", True)], order="sequence,id", limit=1)
        if not mail_server:
            mail_server = mail_server_model.search([], order="sequence,id", limit=1)
    smtp_user = _safe_str(mail_server.smtp_user) if mail_server else ""
    icp_value = _safe_str(env["ir.config_parameter"].sudo().get_param("mail.default.from"))
    companies = env["res.company"].sudo().search([])

    expected = smtp_user
    issues = []

    if not expected:
        issues.append("smtp_user is empty (default mail server missing or no smtp_user)")

    rows = []
    server_id = str(mail_server.id) if mail_server else "none"
    rows.append(("mail_server", f"id={server_id}", smtp_user, smtp_user == expected and bool(expected), expected))
    rows.append(("icp", "mail.default.from", icp_value, icp_value == expected and bool(expected), expected))

    for company in companies:
        company_email = _safe_str(company.email)
        identifier = f"{company.id}:{company.name}"
        rows.append(("company", identifier, company_email, company_email == expected and bool(expected), expected))

    mismatches = [r for r in rows if not r[3]]

    writer = csv.writer(sys.stdout)
    writer.writerow(["kind", "identifier", "value", "match", "expected"])
    for row in rows:
        writer.writerow(row)

    if issues:
        print("GUARD: FAIL", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        raise SystemExit(2)

    if mismatches:
        print("GUARD: FAIL", file=sys.stderr)
        print(f"mismatch_count={len(mismatches)}", file=sys.stderr)
        raise SystemExit(2)

    print("GUARD: PASS", file=sys.stderr)
    raise SystemExit(0)


try:
    main()
except SystemExit:
    raise
except Exception:
    print("ERROR: guard_mail_from crashed", file=sys.stderr)
    traceback.print_exc()
    raise SystemExit(1)

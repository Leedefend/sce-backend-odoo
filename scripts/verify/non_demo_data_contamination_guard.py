# Run with scripts/ops/odoo_shell_exec.sh.
import json
import os
from pathlib import Path

DEMO_DBS = {"sc_demo", "sc_test"}
DEMO_NAME_TOKENS = ("演示", "示例", "某某", "空壳对照", "Demo-")
DEMO_XMLID_MODULES = ("smart_construction_demo",)
REPORT_JSON = Path(os.environ.get("NON_DEMO_DATA_CONTAMINATION_GUARD_JSON", "/tmp/non_demo_data_contamination_guard.json"))
REPORT_MD = Path(os.environ.get("NON_DEMO_DATA_CONTAMINATION_GUARD_MD", "/tmp/non_demo_data_contamination_guard.md"))


def _is_demo_db():
    db_name = str(env.cr.dbname or "").strip()
    return db_name in DEMO_DBS or db_name.startswith("sc_demo_") or db_name.startswith("sc_test_")


def _active_name_count(model_name, field_name="name"):
    Model = env[model_name].sudo()
    if field_name not in Model._fields:
        return 0
    domain = []
    for token in DEMO_NAME_TOKENS:
        leaf = (field_name, "ilike", token)
        if not domain:
            domain = [leaf]
        else:
            domain = ["|", leaf] + domain
    return Model.search_count(domain)


def _is_truthy(value):
    return str(value or "").strip() in {"1", "true", "True", "yes", "YES"}


def _write_report(status, mode, errors=None):
    errors = list(errors or [])
    payload = {
        "ok": status == "PASS" or status == "SKIP",
        "status": status,
        "db_name": str(env.cr.dbname or ""),
        "mode": mode,
        "require_no_demo_data": require_no_demo_data,
        "errors": errors,
        "demo_db_auto_skip": _is_demo_db() and not require_no_demo_data,
        "rules": {
            "forbidden_config": ["sc.login.env=demo", "sc.bootstrap.mode=demo"],
            "forbidden_module": "smart_construction_demo installed",
            "forbidden_xmlid_modules": list(DEMO_XMLID_MODULES),
            "demo_name_tokens": list(DEMO_NAME_TOKENS),
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Non-Demo Data Contamination Guard",
        "",
        f"- status: {status}",
        f"- db_name: `{payload['db_name']}`",
        f"- mode: `{mode}`",
        f"- require_no_demo_data: `{str(require_no_demo_data).lower()}`",
        f"- error_count: {len(errors)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- none")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


require_no_demo_data = _is_truthy(os.environ.get("PRODUCT_REQUIRE_NO_DEMO_DATA"))

if _is_demo_db() and not require_no_demo_data:
    _write_report("SKIP", "demo-db-default-skip")
    print("[non_demo_data_contamination_guard] SKIP demo db", env.cr.dbname)
else:
    errors = []
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.login.env") == "demo":
        errors.append("sc.login.env=demo")
    if ICP.get_param("sc.bootstrap.mode") == "demo":
        errors.append("sc.bootstrap.mode=demo")

    demo_module = env["ir.module.module"].sudo().search(
        [("name", "=", "smart_construction_demo"), ("state", "=", "installed")],
        limit=1,
    )
    if demo_module:
        errors.append("smart_construction_demo installed")

    for model_name in ("project.project", "res.partner"):
        count = _active_name_count(model_name)
        if count:
            errors.append(f"{model_name} active demo-name count={count}")

    imd_count = env["ir.model.data"].sudo().search_count([("module", "in", list(DEMO_XMLID_MODULES))])
    if imd_count:
        errors.append(f"smart_construction_demo xmlid count={imd_count}")

    if errors:
        _write_report("FAIL", "forced" if require_no_demo_data else "default", errors)
        print("[non_demo_data_contamination_guard] FAIL")
        for error in errors:
            print(" -", error)
        raise SystemExit(2)

    mode = "forced" if require_no_demo_data else "default"
    _write_report("PASS", mode)
    print("[non_demo_data_contamination_guard] PASS db=%s mode=%s" % (env.cr.dbname, mode))

# Run with scripts/ops/odoo_shell_exec.sh.
import os

DEMO_DBS = {"sc_demo", "sc_test"}
DEMO_NAME_TOKENS = ("演示", "示例", "某某", "空壳对照", "Demo-")
DEMO_XMLID_MODULES = ("smart_construction_demo",)


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


require_no_demo_data = _is_truthy(os.environ.get("PRODUCT_REQUIRE_NO_DEMO_DATA"))

if _is_demo_db() and not require_no_demo_data:
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
        print("[non_demo_data_contamination_guard] FAIL")
        for error in errors:
            print(" -", error)
        raise SystemExit(2)

    mode = "forced" if require_no_demo_data else "default"
    print("[non_demo_data_contamination_guard] PASS db=%s mode=%s" % (env.cr.dbname, mode))

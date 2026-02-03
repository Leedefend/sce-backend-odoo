#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/../_lib/common.sh"

DB_NAME="${DB_NAME:-sc_demo}"
ROOT_XMLID="${ROOT_XMLID:-smart_construction_core.menu_sc_root}"
LOGIN="${LOGIN:-demo_full}"

log "nav root db check: db=${DB_NAME} root_xmlid=${ROOT_XMLID} login=${LOGIN}"

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T \
  -e DB_NAME="${DB_NAME}" \
  -e ROOT_XMLID="${ROOT_XMLID}" \
  -e LOGIN="${LOGIN}" \
  -e LANG_OVERRIDE="${LANG_OVERRIDE:-}" \
  -e DUMP_MENU_CODE="${DUMP_MENU_CODE:-0}" \
  odoo python3 - <<'PY'
import os
import json
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

db = os.environ.get("DB_NAME", "sc_demo")
root_xmlid = os.environ.get("ROOT_XMLID", "smart_construction_core.menu_sc_root")
login = os.environ.get("LOGIN", "demo_full")

conf_candidates = [
    os.environ.get("ODOO_CONF", ""),
    "/var/lib/odoo/odoo.conf",
    "/etc/odoo/odoo.conf",
]
conf_path = next((p for p in conf_candidates if p and os.path.exists(p)), None)
if conf_path:
    try:
        config.parse_config(["-c", conf_path])
    except Exception:
        pass
config["db_name"] = db

def find_in_tree(nodes, target_id, path=None):
    path = path or []
    for n in nodes or []:
        nid = n.get("id") or n.get("menu_id")
        cur = path + [n]
        if nid == target_id:
            return cur
        found = find_in_tree(n.get("children") or [], target_id, cur)
        if found:
            return found
    return None

def print_chain(menu):
    chain = []
    cur = menu
    while cur:
        chain.append(f"{cur.id}:{cur.name}")
        cur = cur.parent_id if cur.parent_id else None
    return " > ".join(reversed(chain))

registry = odoo.registry(db)
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    print("1) XMLID -> menu")
    if "." not in root_xmlid:
        print(f"   ❌ invalid xmlid: {root_xmlid}")
    else:
        module, name = root_xmlid.split(".", 1)
        imd = env["ir.model.data"].sudo().search([
            ("model", "=", "ir.ui.menu"),
            ("module", "=", module),
            ("name", "=", name),
        ], limit=1)
        if not imd:
            print(f"   ❌ XMLID not found: {root_xmlid}")
        else:
            print(f"   ✅ XMLID found: id={imd.id} res_id={imd.res_id}")
            menu = env["ir.ui.menu"].sudo().browse(imd.res_id)
            if not menu.exists():
                print(f"   ❌ menu record missing for res_id={imd.res_id}")
            else:
                print(f"   ✅ menu: id={menu.id} name={menu.name} active={menu.active}")
                print(f"   parent_id: {menu.parent_id.id if menu.parent_id else None} name={menu.parent_id.name if menu.parent_id else None}")
                print(f"   chain: {print_chain(menu)}")
                if menu.groups_id:
                    groups = []
                    for g in menu.groups_id:
                        gid = env["ir.model.data"].sudo().search(
                            [("model", "=", "res.groups"), ("res_id", "=", g.id)], limit=1
                        )
                        groups.append(f"{g.name}({gid.module}.{gid.name})" if gid else f"{g.name}(id={g.id})")
                    print(f"   groups: {groups}")
                else:
                    print("   groups: (none)")
                # raw SQL sanity
                env.cr.execute("SELECT id, parent_id, active FROM ir_ui_menu WHERE id = %s", [menu.id])
                row = env.cr.fetchone()
                print(f"   sql: id={row[0]} parent_id={row[1]} active={row[2]}")

    print("\n2) app.menu.config cache (scene=web, target=__all__)")
    cfg = env["app.menu.config"].sudo().search([
        ("scene", "=", "web"),
        ("target_model", "=", "__all__"),
        ("company_id", "=", env.company.id),
        ("lang", "=", env.lang or "zh_CN"),
        ("is_active", "=", True),
    ], limit=1)
    try:
        import inspect
        import odoo.addons.smart_core.app_config_engine.models.app_nav_config as nav_mod
        print(f"   code file: {inspect.getsourcefile(nav_mod)}")
    except Exception as e:
        print(f"   code file: (failed to resolve) {e}")
    # force regenerate to validate new full_list behavior
    try:
        lang_override = os.environ.get("LANG_OVERRIDE")
        gen_env = env
        print(f"   current env.lang={env.lang}")
        if lang_override:
            gen_env = api.Environment(env.cr, env.uid, dict(env.context or {}, lang=lang_override))
            print(f"   regenerate with lang override: {lang_override}, gen_env.lang={gen_env.lang}")
        cfg = gen_env["app.menu.config"].sudo()._generate_from_menus(model_name=None, scene="web")
        print("   regenerated config via _generate_from_menus")
    except Exception as e:
        print(f"   failed to regenerate config: {e}")

    if not cfg:
        print("   ❌ no app.menu.config row found for web/__all__")
    else:
        print(f"   ✅ config id={cfg.id} version={cfg.version} hash={cfg.config_hash}")
        tree = cfg.menu_tree or []
        print(f"   tree roots={len(tree)}")
        # find root in menu tree
        if "imd" in locals() and imd and imd.res_id:
            path = find_in_tree(tree, imd.res_id)
            if not path:
                print(f"   ❌ root menu id {imd.res_id} NOT found in menu_tree")
            else:
                chain = " > ".join([f"{n.get('id')}:{n.get('name')}" for n in path])
                print(f"   ✅ found in tree: {chain}")

    print("\n2.2) app.menu.config variants (all langs/companies)")
    rows = env["app.menu.config"].sudo().search([
        ("scene", "=", "web"),
        ("target_model", "=", "__all__"),
    ])
    for c in rows:
        t = c.menu_tree or []
        has_root = False
        if "imd" in locals() and imd and imd.res_id:
            has_root = bool(find_in_tree(t, imd.res_id))
        print(f"   - id={c.id} company={c.company_id.id if c.company_id else None} lang={c.lang} version={c.version} roots={len(t)} has_root={has_root}")

    print("\n2.1) ir.ui.menu root list check")
    roots = env["ir.ui.menu"].sudo().search([("parent_id", "=", False)], order="sequence,id")
    root_ids = [r.id for r in roots]
    print(f"   root count={len(root_ids)}")
    print("   orm roots:")
    for r in roots:
        print(f"     - {r.id}:{r.name} (active={r.active})")
    roots_full = env["ir.ui.menu"].sudo().with_context(**{"ir.ui.menu.full_list": True}).search(
        [("parent_id", "=", False)], order="sequence,id"
    )
    print(f"   orm roots (full_list) count={len(roots_full)}")
    for r in roots_full:
        print(f"     - {r.id}:{r.name} (active={r.active})")
    if "imd" in locals() and imd and imd.res_id:
        print(f"   root_id includes {imd.res_id}: {imd.res_id in root_ids}")
        if imd.res_id in root_ids:
            r = env["ir.ui.menu"].sudo().browse(imd.res_id)
            print(f"   root menu name={r.name} active={r.active} sequence={r.sequence}")
    env.cr.execute("SELECT COUNT(*) FROM ir_ui_menu WHERE parent_id IS NULL")
    cnt = env.cr.fetchone()[0]
    print(f"   sql root count={cnt}")
    env.cr.execute("SELECT id, name, active FROM ir_ui_menu WHERE parent_id IS NULL ORDER BY sequence,id")
    sql_roots = env.cr.fetchall()
    print("   sql roots:")
    for rid, name, active in sql_roots:
        print(f"     - {rid}:{name} (active={active})")
    if "imd" in locals() and imd and imd.res_id:
        env.cr.execute("SELECT id FROM ir_ui_menu WHERE parent_id IS NULL AND id = %s", [imd.res_id])
        hit = env.cr.fetchone()
        print(f"   sql root includes {imd.res_id}: {bool(hit)}")

    print("\n3) user access check")
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    if not user:
        print(f"   ⚠️ user not found: {login}")
    else:
        print(f"   ✅ user id={user.id} groups={len(user.groups_id)}")
        if "menu" in locals() and menu and menu.exists():
            if not menu.groups_id or (menu.groups_id & user.groups_id):
                print("   ✅ user has access to root menu (group check)")
            else:
                print("   ❌ user lacks required groups for root menu")

    print("\n3.1) ir.rule on ir.ui.menu")
    rules = env["ir.rule"].sudo().search([("model_id.model", "=", "ir.ui.menu")])
    if not rules:
        print("   (no rules)")
    else:
        for r in rules:
            print(f"   - {r.name} (domain={r.domain_force})")

    if os.environ.get("DUMP_MENU_CODE") == "1":
        import inspect
        from odoo.addons.base.models import ir_ui_menu
        print(f"\n4) ir.ui.menu code hints (DUMP_MENU_CODE={os.environ.get('DUMP_MENU_CODE')})")
        for name in ("search", "search_fetch", "_search", "_filter_visible_menus", "_load_menus", "load_menus", "get_user_roots"):
            fn = getattr(ir_ui_menu.IrUiMenu, name, None)
            if not fn:
                continue
            try:
                src = inspect.getsource(fn)
                print(f"\n--- {name} ---")
                print(src)
            except Exception as e:
                print(f"   failed to read {name}: {e}")
PY

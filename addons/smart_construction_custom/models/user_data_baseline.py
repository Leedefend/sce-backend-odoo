# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET

from odoo import api, models
from odoo.tools.misc import file_path


LEGACY_USER_MASTER_XML = "user_master_v1.xml"


def _clean_text(value):
    text = str(value or "").strip()
    if not text or text.lower() == "null":
        return False
    return text


def _bool_text(value):
    return str(value or "").strip().lower() in {"1", "true", "yes"}


class ScUserPreferenceInitialization(models.TransientModel):
    _inherit = "sc.user.preference.initialization"

    @api.model
    def apply_user_data_baseline(self):
        super().apply_user_data_baseline()
        summary = {
            "legacy_users": self.apply_legacy_user_master_data_baseline(),
            "partner_business_data": self.apply_partner_business_data_baseline(),
        }
        self.env["ir.config_parameter"].sudo().set_param(
            "sc.custom.user_data_baseline_summary",
            json.dumps(summary, ensure_ascii=False, sort_keys=True),
        )
        return True

    @api.model
    def apply_legacy_user_master_data_baseline(self):
        xml_path = file_path("smart_construction_custom/data/%s" % LEGACY_USER_MASTER_XML)
        if not xml_path:
            return {"status": "SKIP", "reason": "missing_legacy_user_master_xml"}

        root = ET.parse(xml_path).getroot()
        User = self.env["res.users"].sudo().with_context(
            active_test=False,
            install_mode=True,
            no_reset_password=True,
            tracking_disable=True,
            mail_create_nolog=True,
        )
        Imd = self.env["ir.model.data"].sudo()

        created = 0
        updated = 0
        reused_by_login = 0
        bound_xmlids = 0
        skipped = 0
        for node in root.findall(".//record"):
            if node.attrib.get("model") != "res.users":
                continue
            xmlid_name = str(node.attrib.get("id") or "").strip()
            fields = {
                field.attrib.get("name"): _clean_text(field.text)
                for field in node.findall("field")
                if field.attrib.get("name")
            }
            login = _clean_text(fields.get("login"))
            name = _clean_text(fields.get("name"))
            if not xmlid_name or not login or not name:
                skipped += 1
                continue

            user = self._find_existing_legacy_user(Imd, User, xmlid_name, login)
            vals = {
                "name": name,
                "login": login,
                "active": _bool_text(fields.get("active")),
            }
            email = _clean_text(fields.get("email"))
            if email:
                vals["email"] = email

            if user:
                if user.login == login:
                    reused_by_login += 1
                user.write(vals)
                updated += 1
            else:
                user = User.create(vals)
                created += 1
            if self._ensure_user_baseline_xmlid(Imd, xmlid_name, user.id):
                bound_xmlids += 1

        return {
            "status": "PASS",
            "source": "smart_construction_custom/data/%s" % LEGACY_USER_MASTER_XML,
            "created": created,
            "updated": updated,
            "reused_by_login": reused_by_login,
            "bound_xmlids": bound_xmlids,
            "skipped": skipped,
        }

    @api.model
    def apply_partner_business_data_baseline(self):
        Partner = self.env["res.partner"].sudo().with_context(active_test=False)
        if not hasattr(Partner, "action_sc_align_partner_roles_from_business_facts"):
            return {"status": "SKIP", "reason": "missing_partner_business_fact_alignment"}
        summary = Partner.action_sc_align_partner_roles_from_business_facts(demote_no_fact=False)
        summary["demote_no_fact"] = False
        return summary

    @api.model
    def _find_existing_legacy_user(self, Imd, User, xmlid_name, login):
        for module in ("smart_construction_custom", "migration_assets"):
            row = Imd.search(
                [
                    ("module", "=", module),
                    ("name", "=", xmlid_name),
                    ("model", "=", "res.users"),
                ],
                limit=1,
            )
            if row:
                user = User.browse(row.res_id).exists()
                if user:
                    return user
        return User.search([("login", "=", login)], limit=1)

    @api.model
    def _ensure_user_baseline_xmlid(self, Imd, xmlid_name, user_id):
        existing = Imd.search(
            [
                ("module", "=", "smart_construction_custom"),
                ("name", "=", xmlid_name),
                ("model", "=", "res.users"),
            ],
            limit=1,
        )
        if existing:
            if existing.res_id != user_id:
                existing.write({"res_id": user_id})
                return True
            return False
        Imd.create(
            {
                "module": "smart_construction_custom",
                "name": xmlid_name,
                "model": "res.users",
                "res_id": user_id,
                "noupdate": True,
            }
        )
        return True

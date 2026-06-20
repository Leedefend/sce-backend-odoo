# -*- coding: utf-8 -*-
import json
import xml.etree.ElementTree as ET

from odoo import api, models
from odoo.tools.misc import file_path


LEGACY_USER_MASTER_XML = "user_master_v1.xml"
HISTORY_BUSINESS_BASELINE_MANIFEST = "user_history_business_data_baseline_manifest_v1.json"
USER_DATA_REBASELINE_SOURCE_MANIFEST = "user_data_rebaseline_source_manifest_v1.json"
USER_DATA_REBASELINE_REPLAY_PREFLIGHT = "user_data_rebaseline_replay_asset_preflight_v1.json"
USER_MODULE_DATA_BASELINE_CONTRACT = "user_module_data_baseline_contract_v1.json"


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
            "history_business_data": self.apply_history_business_data_baseline_manifest(),
            "rebaseline_contract": self.apply_user_data_rebaseline_contract(),
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
        inactive_applied = 0
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
            desired_active = _bool_text(fields.get("active"))
            vals = {
                "name": name,
                "login": login,
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
            if bool(user.active) != desired_active:
                user.write({"active": desired_active})
                if not desired_active:
                    inactive_applied += 1

        return {
            "status": "PASS",
            "source": "smart_construction_custom/data/%s" % LEGACY_USER_MASTER_XML,
            "created": created,
            "updated": updated,
            "reused_by_login": reused_by_login,
            "bound_xmlids": bound_xmlids,
            "inactive_applied": inactive_applied,
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
    def apply_history_business_data_baseline_manifest(self):
        manifest_path = file_path(
            "smart_construction_custom/data/%s" % HISTORY_BUSINESS_BASELINE_MANIFEST
        )
        if not manifest_path:
            return {"status": "SKIP", "reason": "missing_history_business_baseline_manifest"}

        with open(manifest_path, encoding="utf-8") as handle:
            payload = json.load(handle)

        standard = payload.get("completeness_standard") or {}
        external_lock = payload.get("external_payload_lock") or {}
        legacy_catalog = payload.get("legacy_asset_catalog") or {}
        post_asset = payload.get("post_asset_closure") or {}
        restore_entry = payload.get("restore_entry") or {}
        families = payload.get("visible_business_families") or []
        targets = post_asset.get("targets") or []
        unavailable_targets = [
            item.get("target")
            for item in targets
            if isinstance(item, dict) and not item.get("available_in_makefile")
        ]
        errors = []
        if standard.get("basis") != "locked_user_visible_business_surface":
            errors.append("basis_must_be_locked_user_visible_business_surface")
        if not standard.get("not_complete_if_only_legacy_asset_catalog"):
            errors.append("must_reject_legacy_asset_catalog_only_completion")
        if len(families) != int(standard.get("required_family_count") or 0):
            errors.append("visible_business_family_count_mismatch")
        if int(legacy_catalog.get("source_asset_package_count") or 0) < 23:
            errors.append("legacy_asset_catalog_package_count_too_small")
        if int(post_asset.get("target_count") or 0) < 70:
            errors.append("post_asset_closure_target_count_too_small")
        if unavailable_targets:
            errors.append("post_asset_closure_target_missing_in_makefile")

        return {
            "status": "PASS" if not errors else "FAIL",
            "source": "smart_construction_custom/data/%s" % HISTORY_BUSINESS_BASELINE_MANIFEST,
            "basis": standard.get("basis"),
            "visible_business_family_count": len(families),
            "required_family_count": int(standard.get("required_family_count") or 0),
            "legacy_asset_package_count": int(legacy_catalog.get("source_asset_package_count") or 0),
            "post_asset_closure_target_count": int(post_asset.get("target_count") or 0),
            "external_payload_lock": external_lock.get("path"),
            "external_payload_package_id": external_lock.get("package_id"),
            "restore_target": restore_entry.get("make_target"),
            "restore_default_mode": restore_entry.get("default_mode"),
            "unavailable_targets": unavailable_targets,
            "errors": errors,
        }

    @api.model
    def apply_user_data_rebaseline_contract(self):
        source_manifest = self._load_user_data_baseline_json(USER_DATA_REBASELINE_SOURCE_MANIFEST)
        preflight = self._load_user_data_baseline_json(USER_DATA_REBASELINE_REPLAY_PREFLIGHT)
        contract = self._load_user_data_baseline_json(USER_MODULE_DATA_BASELINE_CONTRACT)
        errors = []

        if source_manifest.get("status") != "PASS":
            errors.append("source_manifest_must_be_pass")
        policy = source_manifest.get("policy") if isinstance(source_manifest.get("policy"), dict) else {}
        if policy.get("attachment_policy") != "link_only_until_prod_attachment_ready":
            errors.append("source_attachment_policy_must_be_link_only_until_prod_attachment_ready")
        forbidden_inputs = set(policy.get("forbidden_inputs") or [])
        for forbidden in ("obsolete_20260513_release_package", "manual_development_database_residue"):
            if forbidden not in forbidden_inputs:
                errors.append("source_manifest_missing_forbidden_input_%s" % forbidden)

        online_sources = source_manifest.get("online_sources") if isinstance(source_manifest.get("online_sources"), dict) else {}
        scbs55 = online_sources.get("scbs55") if isinstance(online_sources.get("scbs55"), dict) else {}
        scbsly = online_sources.get("scbsly_v2") if isinstance(online_sources.get("scbsly_v2"), dict) else {}
        if int(scbs55.get("surface_count") or 0) != 42:
            errors.append("scbs55_surface_count_must_be_42")
        if int(scbs55.get("total_row_count") or 0) < 140000:
            errors.append("scbs55_total_rows_too_small")
        if int(scbsly.get("surface_count") or 0) != 32:
            errors.append("scbsly_v2_surface_count_must_be_32")
        if int(scbsly.get("total_row_count") or 0) < 76000:
            errors.append("scbsly_v2_total_rows_too_small")

        structured_sources = source_manifest.get("structured_db_sources")
        structured_sources = structured_sources if isinstance(structured_sources, dict) else {}
        legacy_counts = structured_sources.get("legacy_counts") if isinstance(structured_sources.get("legacy_counts"), list) else []
        if len(legacy_counts) < 9:
            errors.append("legacy_mssql_counts_must_include_core_tables")

        if preflight.get("status") != "PASS":
            errors.append("replay_asset_preflight_must_be_pass")
        checks = preflight.get("checks") if isinstance(preflight.get("checks"), dict) else {}
        history_payloads = checks.get("history_payloads") if isinstance(checks.get("history_payloads"), dict) else {}
        if int(history_payloads.get("present") or 0) != 52 or int(history_payloads.get("required") or 0) != 52:
            errors.append("history_payloads_must_be_52_of_52")
        core_assets = checks.get("core_replay_assets") if isinstance(checks.get("core_replay_assets"), list) else []
        if len(core_assets) != 7 or any(not item.get("exists") for item in core_assets if isinstance(item, dict)):
            errors.append("core_replay_assets_must_be_7_of_7")
        for source_key, expected_entries in (("scbs55", 42), ("scbsly_v2", 32)):
            link_check = checks.get("stable_online_dump_links_%s" % source_key)
            link_check = link_check if isinstance(link_check, dict) else {}
            if int(link_check.get("entries") or 0) != expected_entries:
                errors.append("stable_online_dump_links_%s_mismatch" % source_key)
            if link_check.get("broken_links"):
                errors.append("stable_online_dump_links_%s_has_broken_links" % source_key)

        if contract.get("version") != "user_module_data_baseline_contract.v1":
            errors.append("user_module_contract_version_mismatch")
        if contract.get("status") != "READY_FOR_USER_MODULE_PACKAGING":
            errors.append("user_module_contract_must_be_ready_for_packaging")
        contract_attachment_policy = contract.get("attachment_policy")
        contract_attachment_policy = contract_attachment_policy if isinstance(contract_attachment_policy, dict) else {}
        if contract_attachment_policy.get("mode") != "link_only":
            errors.append("contract_attachment_policy_must_be_link_only")
        installation_standard = contract.get("installation_standard")
        installation_standard = installation_standard if isinstance(installation_standard, dict) else {}
        acceptance = installation_standard.get("fresh_database_acceptance") or []
        for required in (
            "source manifest status PASS",
            "replay asset preflight PASS",
            "history payloads present 52/52",
            "attachments remain link-only until production attachment source is prepared",
        ):
            if required not in acceptance:
                errors.append("fresh_database_acceptance_missing_%s" % required)

        return {
            "status": "PASS" if not errors else "FAIL",
            "source_manifest": "smart_construction_custom/data/%s" % USER_DATA_REBASELINE_SOURCE_MANIFEST,
            "replay_asset_preflight": "smart_construction_custom/data/%s" % USER_DATA_REBASELINE_REPLAY_PREFLIGHT,
            "contract": "smart_construction_custom/data/%s" % USER_MODULE_DATA_BASELINE_CONTRACT,
            "scbs55_surface_count": int(scbs55.get("surface_count") or 0),
            "scbs55_total_row_count": int(scbs55.get("total_row_count") or 0),
            "scbsly_v2_surface_count": int(scbsly.get("surface_count") or 0),
            "scbsly_v2_total_row_count": int(scbsly.get("total_row_count") or 0),
            "legacy_count_table_count": len(legacy_counts),
            "history_payload_count": int(history_payloads.get("present") or 0),
            "core_replay_asset_count": len(core_assets),
            "attachment_policy": contract_attachment_policy.get("mode"),
            "errors": errors,
        }

    @api.model
    def _load_user_data_baseline_json(self, filename):
        json_path = file_path("smart_construction_custom/data/%s" % filename)
        if not json_path:
            raise ValueError("missing user data baseline JSON: %s" % filename)
        with open(json_path, encoding="utf-8") as handle:
            return json.load(handle)

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

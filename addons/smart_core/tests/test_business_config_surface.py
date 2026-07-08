# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _BaseIntentHandler:
    def __init__(self, env=None, params=None, payload=None, context=None):
        self.env = env or {}
        self.params = params or {}
        self.payload = payload or {}
        self.context = context or {}


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_handler():
    root = Path(__file__).resolve().parents[1]
    exc_mod = _install_module(
        "odoo.exceptions",
        AccessError=type("AccessError", (Exception,), {}),
        ValidationError=type("ValidationError", (Exception,), {}),
    )
    _install_module("odoo", exceptions=exc_mod)
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    handlers_mod = _install_module("odoo.addons.smart_core.handlers")
    core_mod = _install_module("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    handlers_mod.__path__ = [str(root / "handlers")]
    core_mod.__path__ = [str(root / "core")]
    _install_module("odoo.addons.smart_core.core.base_handler", BaseIntentHandler=_BaseIntentHandler)

    sys.modules.pop("odoo.addons.smart_core.handlers.business_config_surface", None)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.handlers.business_config_surface",
        root / "handlers" / "business_config_surface.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _User:
    def has_group(self, xmlid):
        return xmlid in {
            "smart_core.group_smart_core_business_config_admin",
            "smart_core.group_smart_core_admin",
        }


class _Contract:
    def __init__(
        self,
        model,
        view_type,
        *,
        action_id=0,
        view_id=0,
        role_key="",
        status="published",
        contract_json=None,
        version_no=1,
    ):
        self.model = model
        self.view_type = view_type
        self.action_id = types.SimpleNamespace(id=action_id) if action_id else False
        self.view_id = types.SimpleNamespace(id=view_id) if view_id else False
        self.action_id_value = action_id
        self.view_id_value = view_id
        self.role_key = role_key
        self.status = status
        self.name = "%s:%s:%s" % (model, view_type, action_id)
        self.id = action_id or view_id or 1
        self.contract_json = contract_json if isinstance(contract_json, dict) else {"views": {view_type or "all": []}}
        self.version_no = version_no


class _ContractModel(list):
    def sudo(self):
        return self

    def _effective_view_orchestration_contracts(self, model, **kwargs):
        view_type = kwargs.get("view_type")
        action_id = kwargs.get("action_id") or 0
        view_id = kwargs.get("view_id") or 0
        role_key = kwargs.get("role_key") or ""
        return [
            row for row in self
            if row.status == "published"
            and row.model == model
            and (not view_type or row.view_type == view_type)
            and (not action_id or row.action_id_value in {0, action_id})
            and (not view_id or row.view_id_value in {0, view_id})
            and (not role_key or row.role_key in {"", role_key})
        ]

    def search_count(self, domain):
        model = next((value for field, op, value in domain if field == "model" and op == "="), "")
        view_types = next((value for field, op, value in domain if field == "view_type" and op == "in"), [])
        action_ids = next((value for field, op, value in domain if field == "action_id" and op == "in"), [])
        view_ids = next((value for field, op, value in domain if field == "view_id" and op == "in"), [])
        role_keys = next((value for field, op, value in domain if field == "role_key" and op == "in"), [])
        status = next((value for field, op, value in domain if field == "status" and op == "="), "")
        return len([
            row for row in self
            if (not model or row.model == model)
            and (not view_types or row.view_type in view_types)
            and (not action_ids or (row.action_id_value or False) in action_ids)
            and (not view_ids or (row.view_id_value or False) in view_ids)
            and (not role_keys or (row.role_key or False) in role_keys)
            and (not status or row.status == status)
        ])

    def search(self, domain, limit=None, order=None):
        self.domain = domain
        self.limit = limit
        self.order = order
        rows = list(self)
        return rows[:limit] if limit else rows


class _Action:
    def __init__(self, ident, name, model, view_mode):
        self.id = ident
        self.name = name
        self.res_model = model
        self.view_mode = view_mode


class _ActionModel(list):
    def sudo(self):
        return self

    def browse(self, ident):
        rows = [row for row in self if row.id == ident]

        class _RecordSet(list):
            def exists(self):
                return self[0] if self else None

        return _RecordSet(rows)

    def search(self, domain, limit=None, order=None):
        self.domain = domain
        self.limit = limit
        self.order = order
        model = next((value for field, op, value in domain if field == "res_model" and op == "="), "")
        ids = next((value for field, op, value in domain if field == "id" and op == "in"), [])
        rows = [
            row for row in self
            if row.res_model
            and (not model or row.res_model == model)
            and (not ids or row.id in ids)
        ]
        return rows[:limit] if limit else rows


class _MenuModel:
    def __init__(self, action_refs):
        self.action_refs = action_refs
        self.search_domains = []

    def sudo(self):
        return self

    def search(self, domain, limit=None):
        self.search_domain = domain
        self.search_domains.append(domain)
        rows = [
            types.SimpleNamespace(id=index + 1, action=ref, parent_id=None)
            for index, ref in enumerate(self.action_refs)
        ]
        return rows[:limit] if limit else rows

    def search_count(self, domain):
        self.domain = domain
        action_ref = next((value for field, op, value in domain if field == "action" and op == "="), "")
        return len([ref for ref in self.action_refs if ref == action_ref])


class _ApprovalPolicyModel(list):
    def sudo(self):
        return self

    def search_count(self, domain):
        self.domain = domain
        target_model = next((value for field, op, value in domain if field == "target_model" and op == "="), "")
        active = next((value for field, op, value in domain if field == "active" and op == "="), None)
        return len([
            row for row in self
            if (not target_model or row.get("target_model") == target_model)
            and (active is None or bool(row.get("active", True)) is bool(active))
        ])


class _VisibleMenuModel(_MenuModel):
    def __init__(self, action_refs, visible_ids):
        super().__init__(action_refs)
        self.visible_ids = visible_ids
        self.rows = [
            types.SimpleNamespace(id=index + 1, action=ref, parent_id=None)
            for index, ref in enumerate(action_refs)
        ]

    def _visible_menu_ids(self, debug=False):
        del debug
        return list(self.visible_ids)

    def browse(self, ids):
        rows = [row for row in self.rows if row.id in set(ids)]

        class _RecordSet(list):
            def exists(self):
                return self

        return _RecordSet(rows)

    def search(self, domain, limit=None):
        self.search_domain = domain
        self.search_domains.append(domain)
        return self.rows[:limit] if limit else list(self.rows)


class _PreferenceModel:
    def __init__(self, rows):
        self.rows = rows

    def sudo(self):
        return self

    def search_count(self, domain):
        self.domain = domain
        model_name = next((value for field, op, value in domain if field == "model_name" and op == "="), "")
        action_id = next((value for field, op, value in domain if field == "action_id" and op == "="), 0)
        return len([
            row for row in self.rows
            if row.get("model_name") == model_name
            and row.get("action_id") == action_id
            and row.get("preference_key") == "list_columns"
            and row.get("view_type") in {"list", "tree"}
        ])


class _Env(dict):
    company = types.SimpleNamespace(id=7)
    user = _User()
    context = {}
    cr = types.SimpleNamespace(dbname="sc_demo")

    def ref(self, xmlid, raise_if_not_found=True):
        refs = {
            "smart_construction_core.action_sc_approval_policy": types.SimpleNamespace(id=901),
            "smart_construction_core.menu_sc_approval_policy": types.SimpleNamespace(id=902),
        }
        record = refs.get(xmlid)
        if record or not raise_if_not_found:
            return record
        raise ValueError(xmlid)


class BusinessConfigSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def test_surface_reports_business_config_sections(self):
        env = _Env({
            "sc.approval.policy": _ApprovalPolicyModel([
                {"target_model": "res.partner", "active": True},
                {"target_model": "project.project", "active": True},
            ]),
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11, view_id=22, role_key="sales"),
                _Contract("res.partner", "tree", action_id=11, view_id=22, role_key="sales"),
                _Contract("res.partner", "search", action_id=11, view_id=22, role_key="sales"),
                _Contract("res.partner", "pivot", action_id=11, view_id=22, role_key="sales"),
                _Contract("res.partner", "graph", action_id=11, view_id=22, role_key="sales"),
                _Contract("res.partner", "search", action_id=99, view_id=22, role_key="sales"),
                _Contract("ir.ui.menu", False),
            ]),
        })
        handler = self.module.BusinessConfigSurfaceGetHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11, "view_id": 22, "role_key": "sales"},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        sections = {row["key"]: row for row in result["data"]["sections"]}
        self.assertEqual(sections["form"]["contract_count"], 1)
        self.assertEqual(sections["list_search"]["contract_count"], 2)
        self.assertEqual(sections["analysis"]["contract_count"], 2)
        self.assertEqual(sections["menu"]["contract_count"], 1)
        self.assertEqual(sections["approval"]["contract_count"], 1)
        self.assertEqual(sections["approval"]["boundary"], "industry_policy_runtime")
        self.assertEqual(sections["approval"]["route"]["path"], "/a/901")
        self.assertEqual(sections["approval"]["route"]["query"]["menu_id"], "902")
        self.assertEqual(sections["approval"]["route"]["query"]["target_model"], "res.partner")
        self.assertEqual(sections["approval"]["route"]["query"]["domain_raw"], "[('target_model', '=', 'res.partner')]")
        self.assertEqual(result["data"]["role_key"], "sales")
        self.assertEqual(sections["list_search"]["boundary"], "business_contract_not_user_preference")
        self.assertEqual(sections["analysis"]["boundary"], "business_contract")
        readiness = result["data"]["delivery_readiness"]
        self.assertEqual(readiness["schema_version"], "low_code_delivery_readiness.v1")
        self.assertEqual(readiness["overall_status"], "ready")
        self.assertEqual(readiness["ready_count"], readiness["total_count"])
        readiness_items = {row["section_key"]: row for row in readiness["items"]}
        self.assertEqual(readiness_items["form"]["id"], "form_field_structure")
        self.assertEqual(readiness_items["list_search"]["contract_count"], 2)
        self.assertEqual(readiness_items["menu"]["boundary"], "business_contract_with_policy_runtime")
        self.assertEqual(readiness_items["version"]["contract_count"], 7)
        self.assertEqual(readiness_items["coverage"]["action"], "coverage_scan")

    def test_surface_delivery_readiness_marks_empty_authoring_sections_pending(self):
        env = _Env({
            "ui.business.config.contract": _ContractModel([]),
        })
        handler = self.module.BusinessConfigSurfaceGetHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        readiness = result["data"]["delivery_readiness"]
        self.assertEqual(readiness["overall_status"], "attention")
        self.assertGreater(readiness["blocker_count"], 0)
        readiness_items = {row["section_key"]: row for row in readiness["items"]}
        self.assertEqual(readiness_items["form"]["status"], "pending")
        self.assertEqual(readiness_items["list_search"]["status"], "pending")
        self.assertEqual(readiness_items["coverage"]["status"], "ready")

    def test_surface_exposes_analysis_section_from_action_view_mode(self):
        env = _Env({
            "ir.actions.act_window": _ActionModel([
                _Action(11, "经营分析", "res.partner", "pivot,graph"),
            ]),
            "ui.business.config.contract": _ContractModel([]),
        })
        handler = self.module.BusinessConfigSurfaceGetHandler(
            env=env,
            params={"model": "res.partner", "action_id": 11},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        sections = {row["key"]: row for row in result["data"]["sections"]}
        self.assertIn("analysis", sections)
        self.assertEqual(sections["analysis"]["contract_count"], 0)

    def test_snapshot_summary_reports_contract_distribution(self):
        env = _Env({
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11, role_key="sales"),
                _Contract("res.partner", "tree", action_id=11),
                _Contract("res.partner", "search", status="draft"),
                _Contract("project.project", "form", action_id=12),
            ]),
        })
        handler = self.module.BusinessConfigSnapshotSummaryHandler(env=env, params={})

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["database"], "sc_demo")
        self.assertEqual(data["contract_count"], 4)
        self.assertEqual(data["status_counts"], {"draft": 1, "published": 3})
        self.assertEqual(data["view_type_counts"], {"form": 2, "search": 1, "tree": 1})
        self.assertEqual(data["role_scope_count"], 1)
        self.assertEqual(data["action_scope_count"], 3)

    def test_snapshot_export_returns_contract_rows_for_download(self):
        env = _Env({
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11, contract_json={"fields": ["name"]}),
                _Contract("res.partner", "tree", action_id=11, status="draft", contract_json={"columns": ["name"]}),
            ]),
        })
        handler = self.module.BusinessConfigSnapshotExportHandler(env=env, params={})

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["database"], "sc_demo")
        self.assertEqual(data["contract_count"], 2)
        self.assertEqual(data["status_counts"], {"draft": 1, "published": 1})
        self.assertEqual([row["view_type"] for row in data["contracts"]], ["form", "tree"])
        self.assertTrue(data["contracts"][0]["payload_hash"])

    def test_snapshot_compare_reports_added_removed_and_changed_contracts(self):
        env = _Env({
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11, contract_json={"fields": ["name", "phone"]}, version_no=2),
                _Contract("project.project", "tree", action_id=12, contract_json={"columns": ["name"]}),
            ]),
        })
        previous_hash = self.module._hash_payload({"fields": ["name"]})
        removed_hash = self.module._hash_payload({"columns": ["name"]})
        baseline = {
            "database": "sc_dev",
            "contracts": [
                {
                    "name": "res.partner:form:11",
                    "model": "res.partner",
                    "view_type": "form",
                    "action_id": 11,
                    "view_id": 0,
                    "role_key": "",
                    "status": "published",
                    "version_no": 1,
                    "payload_hash": previous_hash,
                },
                {
                    "name": "sale.order:tree:99",
                    "model": "sale.order",
                    "view_type": "tree",
                    "action_id": 99,
                    "view_id": 0,
                    "role_key": "",
                    "status": "published",
                    "version_no": 1,
                    "payload_hash": removed_hash,
                },
            ],
        }
        handler = self.module.BusinessConfigSnapshotCompareHandler(env=env, params={"snapshot": baseline})

        result = handler.handle()

        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertEqual(data["current_database"], "sc_demo")
        self.assertEqual(data["baseline_database"], "sc_dev")
        self.assertEqual(data["current_contract_count"], 2)
        self.assertEqual(data["baseline_contract_count"], 2)
        self.assertEqual(data["added_count"], 1)
        self.assertEqual(data["removed_count"], 1)
        self.assertEqual(data["changed_count"], 1)
        self.assertEqual(data["added"][0]["model"], "project.project")
        self.assertEqual(data["removed"][0]["model"], "sale.order")
        self.assertEqual(data["changed"][0]["model"], "res.partner")
        self.assertEqual(data["changed"][0]["previous_version_no"], 1)
        self.assertEqual(data["changed"][0]["current_version_no"], 2)

    def test_coverage_scan_reports_action_contract_gaps(self):
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
            _Action(12, "项目", "project.project", "tree,form"),
        ])
        contract_model = _ContractModel([
            _Contract("res.partner", "form", action_id=11, role_key="sales"),
            _Contract("res.partner", "tree", action_id=11, role_key="sales", status="draft"),
            _Contract("project.project", "search", action_id=12, role_key="sales"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11"]),
            "sc.user.view.preference": _PreferenceModel([
                {"model_name": "res.partner", "action_id": 11, "preference_key": "list_columns", "view_type": "list"},
                {"model_name": "res.partner", "action_id": 11, "preference_key": "list_columns", "view_type": "tree"},
            ]),
            "ui.business.config.contract": contract_model,
        })
        handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={"role_key": "sales", "model": "res.partner", "limit": 50},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(action_model.domain, [
            ("res_model", "!=", False),
            ("id", "in", [11]),
            ("res_model", "=", "res.partner"),
        ])
        self.assertEqual(action_model.limit, 50)
        self.assertEqual(result["data"]["model"], "res.partner")
        self.assertFalse(result["data"]["include_unreachable_actions"])
        self.assertEqual(
            result["data"]["runtime_evidence_source"],
            "ui.business.config.contract._effective_view_orchestration_contracts",
        )
        summary = result["data"]["summary"]
        self.assertEqual(summary["action_count"], 1)
        self.assertEqual(summary["missing_count"], 1)
        self.assertEqual(summary["runtime_missing_count"], 1)
        self.assertEqual(summary["missing_form_count"], 0)
        self.assertEqual(summary["missing_list_count"], 0)
        self.assertEqual(summary["missing_search_count"], 1)
        self.assertEqual(summary["runtime_missing_form_count"], 0)
        self.assertEqual(summary["runtime_missing_list_count"], 1)
        self.assertEqual(summary["runtime_missing_search_count"], 1)
        self.assertEqual(summary["not_published_gap_count"], 1)
        self.assertEqual(summary["not_runtime_applicable_gap_count"], 0)
        self.assertEqual(summary["no_menu_count"], 0)
        self.assertEqual(summary["user_preference_count"], 2)
        self.assertEqual(summary["remediation_action_counts"], {
            "configure_contract": 1,
            "publish_contract": 1,
            "review_user_preference_boundary": 1,
        })
        self.assertEqual(summary["severity_counts"], {"error": 1, "warning": 0, "notice": 0, "ok": 0})
        self.assertEqual(summary["overall_status"], "blocked")
        rows = {row["action_id"]: row for row in result["data"]["items"]}
        self.assertEqual(rows[11]["missing_view_types"], ["search"])
        self.assertEqual(rows[11]["runtime_missing_view_types"], ["tree", "search"])
        self.assertEqual(rows[11]["runtime_gap_reasons"], {
            "tree": "not_published",
            "search": "missing_contract",
        })
        self.assertEqual(rows[11]["remediation_actions"], [
            {
                "code": "configure_contract",
                "label": "补配置",
                "target": "business_contract_editor",
                "priority": 10,
            },
            {
                "code": "publish_contract",
                "label": "看版本",
                "target": "business_contract_versions",
                "priority": 20,
            },
            {
                "code": "review_user_preference_boundary",
                "label": "查偏好",
                "target": "list_search_audit",
                "priority": 50,
            },
        ])
        self.assertEqual(rows[11]["severity"], "error")
        self.assertEqual(rows[11]["sort_priority"], 1010)
        self.assertFalse(rows[11]["is_runtime_complete"])
        self.assertEqual(rows[11]["coverage"], {"form": 1, "tree": 1, "search": 0})
        self.assertEqual(rows[11]["published_coverage"], {"form": 1, "tree": 0, "search": 0})
        self.assertEqual(rows[11]["runtime_coverage"], {"form": 1, "tree": 0, "search": 0})
        self.assertEqual(rows[11]["runtime_evidence"]["tree"], {
            "source": "ui.business.config.contract._effective_view_orchestration_contracts",
            "configured_count": 1,
            "published_count": 0,
            "runtime_count": 0,
        })
        self.assertEqual(rows[11]["menu_count"], 1)
        self.assertEqual(rows[11]["menu_ids"], [1])
        self.assertEqual(rows[11]["runtime_route"], {
            "path": "/a/11",
            "query": {"action_id": "11", "menu_id": "1"},
        })
        self.assertTrue(rows[11]["has_menu"])
        self.assertEqual(rows[11]["user_preference_count"], 2)
        self.assertEqual(rows[11]["user_preference_boundary"], "ui_only")

    def test_coverage_scan_honors_view_scope(self):
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11, view_id=99, role_key="sales"),
                _Contract("res.partner", "tree", action_id=11, view_id=22, role_key="sales"),
                _Contract("res.partner", "search", action_id=11, view_id=22, role_key="sales"),
            ]),
        })
        handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={"role_key": "sales", "model": "res.partner", "view_id": 22, "limit": 50},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["view_id"], 22)
        row = result["data"]["items"][0]
        self.assertEqual(row["view_id"], 22)
        self.assertEqual(row["missing_view_types"], ["form"])
        self.assertEqual(row["runtime_missing_view_types"], ["form"])
        self.assertEqual(row["runtime_gap_reasons"], {"form": "missing_contract"})

    def test_coverage_scan_can_include_unreachable_actions_for_audit(self):
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
            _Action(12, "孤立动作", "res.partner", "tree"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([]),
        })
        handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={"model": "res.partner", "limit": 50, "include_unreachable_actions": True},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["include_unreachable_actions"])
        self.assertEqual(action_model.domain, [("res_model", "!=", False), ("res_model", "=", "res.partner")])
        self.assertEqual(result["data"]["summary"]["action_count"], 2)
        rows = {row["action_id"]: row for row in result["data"]["items"]}
        self.assertTrue(rows[11]["has_menu"])
        self.assertFalse(rows[12]["has_menu"])

    def test_coverage_scan_includes_analysis_view_gaps(self):
        action_model = _ActionModel([
            _Action(11, "经营分析", "res.partner", "pivot,graph"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "pivot", action_id=11),
            ]),
        })
        handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={"model": "res.partner", "limit": 50},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        summary = result["data"]["summary"]
        self.assertEqual(summary["missing_analysis_count"], 1)
        self.assertEqual(summary["runtime_missing_analysis_count"], 1)
        self.assertEqual(summary["missing_count"], 1)
        self.assertEqual(summary["runtime_missing_count"], 1)
        row = result["data"]["items"][0]
        self.assertEqual(row["target_view_types"], ["pivot", "graph"])
        self.assertEqual(row["missing_view_types"], ["graph"])
        self.assertEqual(row["runtime_missing_view_types"], ["graph"])
        self.assertEqual(row["runtime_gap_reasons"], {"graph": "missing_contract"})
        self.assertEqual(row["severity"], "error")

    def test_coverage_scan_can_include_all_root_menu_actions_for_system_remediation(self):
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
            _Action(12, "项目", "project.project", "tree,form"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _VisibleMenuModel(["ir.actions.act_window,11", "ir.actions.act_window,12"], visible_ids=[1]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([]),
        })
        default_handler = self.module.BusinessConfigCoverageScanHandler(env=env, params={"limit": 50})
        system_handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={"limit": 50, "include_all_root_menu_actions": True},
        )

        default_result = default_handler.handle()
        system_result = system_handler.handle()

        self.assertTrue(default_result["ok"])
        self.assertFalse(default_result["data"]["include_all_root_menu_actions"])
        self.assertEqual(default_result["data"]["summary"]["action_count"], 1)
        self.assertEqual([row["action_id"] for row in default_result["data"]["items"]], [11])
        self.assertTrue(system_result["ok"])
        self.assertTrue(system_result["data"]["include_all_root_menu_actions"])
        self.assertIn([], env["ir.ui.menu"].search_domains)
        self.assertEqual(system_result["data"]["summary"]["action_count"], 2)
        self.assertEqual(
            sorted(row["action_id"] for row in system_result["data"]["items"]),
            [11, 12],
        )

    def test_coverage_scan_can_skip_unavailable_models_for_migration_remediation(self):
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
            _Action(12, "场景治理", "sc.scene.governance.wizard", "form"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11", "ir.actions.act_window,12"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([]),
            "res.partner": object(),
        })
        handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={
                "limit": 50,
                "include_all_root_menu_actions": True,
                "skip_unavailable_models": True,
            },
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["skip_unavailable_models"])
        self.assertEqual(result["data"]["summary"]["action_count"], 1)
        self.assertEqual([row["action_id"] for row in result["data"]["items"]], [11])

    def test_coverage_scan_treats_user_preferences_as_audit_signal_not_gap(self):
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11"]),
            "sc.user.view.preference": _PreferenceModel([
                {"model_name": "res.partner", "action_id": 11, "preference_key": "list_columns", "view_type": "list"},
            ]),
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11),
                _Contract("res.partner", "tree", action_id=11),
                _Contract("res.partner", "search", action_id=11),
            ]),
        })
        handler = self.module.BusinessConfigCoverageScanHandler(
            env=env,
            params={"model": "res.partner", "limit": 50},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        summary = result["data"]["summary"]
        self.assertEqual(summary["overall_status"], "pass")
        self.assertEqual(summary["severity_counts"], {"error": 0, "warning": 0, "notice": 0, "ok": 1})
        self.assertEqual(summary["user_preference_count"], 1)
        self.assertEqual(summary["remediation_action_counts"], {"review_user_preference_boundary": 1})
        row = result["data"]["items"][0]
        self.assertEqual(row["severity"], "ok")
        self.assertTrue(row["is_complete"])
        self.assertTrue(row["is_runtime_complete"])
        self.assertEqual(row["user_preference_count"], 1)
        self.assertEqual(row["remediation_actions"], [{
            "code": "review_user_preference_boundary",
            "label": "查偏好",
            "target": "list_search_audit",
            "priority": 50,
        }])

    def test_coverage_bootstrap_list_search_batches_runtime_gaps(self):
        calls = []

        class FakeBootstrapHandler:
            def __init__(self, env=None, payload=None, **kwargs):
                self.env = env
                self.payload = payload or {}
                self.params = self.payload.get("params") or {}

            def handle(self, payload=None, ctx=None):
                del payload, ctx
                calls.append(dict(self.params))
                return {
                    "ok": True,
                    "data": {
                        "saved_count": len(self.params.get("view_types") or []),
                    },
                }

        _install_module(
            "odoo.addons.smart_core.handlers.form_field_configuration",
            BusinessConfigListSearchBootstrapHandler=FakeBootstrapHandler,
        )
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
            _Action(12, "项目", "project.project", "tree,form"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11", "ir.actions.act_window,12"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([
                _Contract("res.partner", "form", action_id=11),
                _Contract("project.project", "form", action_id=12),
                _Contract("project.project", "search", action_id=12),
            ]),
        })
        handler = self.module.BusinessConfigCoverageBootstrapListSearchHandler(
            env=env,
            params={"limit": 50, "batch_limit": 10},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["candidate_count"], 2)
        self.assertEqual(result["data"]["saved_count"], 3)
        self.assertEqual(result["data"]["failed_count"], 0)
        self.assertEqual(result["data"]["personal_preference_boundary"], "not_a_source")
        self.assertEqual(
            [(call["model"], call["action_id"], call["view_types"]) for call in calls],
            [
                ("project.project", 12, ["tree"]),
                ("res.partner", 11, ["tree", "search"]),
            ],
        )

    def test_coverage_bootstrap_only_batches_missing_contract_gaps(self):
        row = {
            "runtime_missing_view_types": ["form", "tree", "search", "pivot", "graph"],
            "runtime_gap_reasons": {
                "form": "missing_contract",
                "tree": "not_published",
                "search": "not_runtime_applicable",
                "pivot": "missing_contract",
                "graph": "not_published",
            },
        }

        self.assertEqual(
            self.module.BusinessConfigCoverageBootstrapListSearchHandler._bootstrap_view_types(row, {"tree", "search"}),
            [],
        )
        self.assertEqual(
            self.module.BusinessConfigCoverageBootstrapMissingHandler._bootstrap_view_types(
                row,
                {"form", "tree", "search", "pivot", "graph"},
            ),
            ["form", "pivot"],
        )

    def test_coverage_bootstrap_missing_batches_form_list_and_search_gaps(self):
        calls = []

        class FakeFormBootstrapHandler:
            def __init__(self, env=None, payload=None, **kwargs):
                self.env = env
                self.payload = payload or {}
                self.params = self.payload.get("params") or {}

            def handle(self, payload=None, ctx=None):
                del payload, ctx
                calls.append(("form", dict(self.params)))
                return {
                    "ok": True,
                    "data": {
                        "field_count": 5,
                    },
                }

        class FakeListSearchBootstrapHandler:
            def __init__(self, env=None, payload=None, **kwargs):
                self.env = env
                self.payload = payload or {}
                self.params = self.payload.get("params") or {}

            def handle(self, payload=None, ctx=None):
                del payload, ctx
                calls.append(("list_search", dict(self.params)))
                return {
                    "ok": True,
                    "data": {
                        "saved_count": len(self.params.get("view_types") or []),
                    },
                }

        class FakeAnalysisBootstrapHandler(FakeListSearchBootstrapHandler):
            pass

        _install_module(
            "odoo.addons.smart_core.handlers.form_field_configuration",
            BusinessConfigAnalysisBootstrapHandler=FakeAnalysisBootstrapHandler,
            BusinessConfigFormBootstrapHandler=FakeFormBootstrapHandler,
            BusinessConfigListSearchBootstrapHandler=FakeListSearchBootstrapHandler,
        )
        action_model = _ActionModel([
            _Action(11, "客户", "res.partner", "tree,form"),
            _Action(12, "项目", "project.project", "tree,form"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11", "ir.actions.act_window,12"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([
                _Contract("project.project", "form", action_id=12),
                _Contract("project.project", "tree", action_id=12),
                _Contract("project.project", "search", action_id=12),
            ]),
        })
        handler = self.module.BusinessConfigCoverageBootstrapMissingHandler(
            env=env,
            params={"limit": 50, "batch_limit": 10, "role_key": "finance_user"},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["candidate_count"], 1)
        self.assertEqual(result["data"]["saved_count"], 3)
        self.assertEqual(result["data"]["failed_count"], 0)
        self.assertEqual(result["data"]["personal_preference_boundary"], "not_a_source")
        self.assertEqual(
            calls,
            [
                ("form", {
                    "model": "res.partner",
                    "action_id": 11,
                    "role_key": "finance_user",
                    "publish": True,
                }),
                ("list_search", {
                    "model": "res.partner",
                    "action_id": 11,
                    "role_key": "finance_user",
                    "view_types": ["tree", "search"],
                    "publish": True,
                }),
            ],
        )
        self.assertEqual(result["data"]["results"][0]["view_types"], ["form", "tree", "search"])

    def test_coverage_bootstrap_missing_batches_analysis_gaps(self):
        calls = []

        class FakeFormBootstrapHandler:
            def __init__(self, env=None, payload=None, **kwargs):
                self.env = env
                self.payload = payload or {}
                self.params = self.payload.get("params") or {}

            def handle(self, payload=None, ctx=None):
                del payload, ctx
                calls.append(("form", dict(self.params)))
                return {"ok": True, "data": {"field_count": 5}}

        class FakeListSearchBootstrapHandler(FakeFormBootstrapHandler):
            def handle(self, payload=None, ctx=None):
                del payload, ctx
                calls.append(("list_search", dict(self.params)))
                return {"ok": True, "data": {"saved_count": len(self.params.get("view_types") or [])}}

        class FakeAnalysisBootstrapHandler(FakeFormBootstrapHandler):
            def handle(self, payload=None, ctx=None):
                del payload, ctx
                calls.append(("analysis", dict(self.params)))
                return {"ok": True, "data": {"saved_count": len(self.params.get("view_types") or [])}}

        _install_module(
            "odoo.addons.smart_core.handlers.form_field_configuration",
            BusinessConfigAnalysisBootstrapHandler=FakeAnalysisBootstrapHandler,
            BusinessConfigFormBootstrapHandler=FakeFormBootstrapHandler,
            BusinessConfigListSearchBootstrapHandler=FakeListSearchBootstrapHandler,
        )
        action_model = _ActionModel([
            _Action(11, "经营分析", "res.partner", "pivot,graph"),
        ])
        env = _Env({
            "ir.actions.act_window": action_model,
            "ir.ui.menu": _MenuModel(["ir.actions.act_window,11"]),
            "sc.user.view.preference": _PreferenceModel([]),
            "ui.business.config.contract": _ContractModel([]),
        })
        handler = self.module.BusinessConfigCoverageBootstrapMissingHandler(
            env=env,
            params={"limit": 50, "batch_limit": 10, "role_key": "finance_user"},
        )

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["candidate_count"], 1)
        self.assertEqual(result["data"]["saved_count"], 2)
        self.assertEqual(calls, [("analysis", {
            "model": "res.partner",
            "action_id": 11,
            "role_key": "finance_user",
            "view_types": ["pivot", "graph"],
            "publish": True,
        })])
        self.assertEqual(result["data"]["results"][0]["view_types"], ["pivot", "graph"])


if __name__ == "__main__":
    unittest.main()

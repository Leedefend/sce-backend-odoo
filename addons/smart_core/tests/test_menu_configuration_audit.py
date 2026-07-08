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


def _lowcode_system_config_menu_xmlids_hook(env, hook_name, *args, **kwargs):
    del env, args, kwargs
    if hook_name != "smart_core_lowcode_system_config_menu_xmlids":
        return None
    return [
        "smart_construction_core.menu_sc_business_config_center",
        "smart_construction_core.menu_sc_business_config_workbench",
        "smart_construction_core.menu_ui_menu_config_policy_business_config",
    ]


def _lowcode_config_boundary_hooks(env, hook_name, *args, **kwargs):
    if hook_name == "smart_core_native_config_delivery_excluded_menu_xmlids":
        return []
    return _lowcode_system_config_menu_xmlids_hook(env, hook_name, *args, **kwargs)


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

    sys.modules.pop("odoo.addons.smart_core.handlers.menu_configuration", None)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.handlers.menu_configuration",
        root / "handlers" / "menu_configuration.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_policy_model():
    root = Path(__file__).resolve().parents[1]
    api_mod = types.SimpleNamespace(
        model=lambda fn: fn,
        model_create_multi=lambda fn: fn,
        depends=lambda *args, **kwargs: (lambda fn: fn),
        onchange=lambda *args, **kwargs: (lambda fn: fn),
        constrains=lambda *args, **kwargs: (lambda fn: fn),
    )
    fields_mod = types.SimpleNamespace(
        Char=lambda *args, **kwargs: None,
        Many2one=lambda *args, **kwargs: None,
        Many2many=lambda *args, **kwargs: None,
        Integer=lambda *args, **kwargs: None,
        Boolean=lambda *args, **kwargs: None,
        Text=lambda *args, **kwargs: None,
    )
    models_mod = types.SimpleNamespace(Model=object)
    exc_mod = _install_module(
        "odoo.exceptions",
        AccessError=type("AccessError", (Exception,), {}),
        ValidationError=type("ValidationError", (Exception,), {}),
    )
    _install_module("odoo", api=api_mod, fields=fields_mod, models=models_mod, exceptions=exc_mod)

    sys.modules.pop("odoo.addons.smart_core.model.ui_menu_config_policy", None)
    spec = importlib.util.spec_from_file_location(
        "odoo.addons.smart_core.model.ui_menu_config_policy",
        root / "model" / "ui_menu_config_policy.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _RecordSet(list):
    @property
    def ids(self):
        return [int(getattr(record, "id", 0) or 0) for record in self]

    def sudo(self):
        return self

    def with_context(self, **kwargs):
        self.context = kwargs
        return self

    def browse(self, record_id):
        for record in self:
            if int(getattr(record, "id", 0) or 0) == int(record_id or 0):
                return record
        return _RecordSet([])

    def exists(self):
        return self

    def mapped(self, name):
        values = _RecordSet([])
        scalars = []
        for record in self:
            value = getattr(record, name, None)
            if isinstance(value, (list, _RecordSet)):
                values.extend(value)
            elif hasattr(value, "id"):
                values.append(value)
            elif value is not None:
                scalars.append(value)
        return values if values else scalars

    def sorted(self, key=None, reverse=False):
        return _RecordSet(sorted(list(self), key=key, reverse=reverse))


class _Group:
    def __init__(self, ident, name):
        self.id = ident
        self.name = name
        self.display_name = name


class _Menu:
    def __init__(self, ident, name, complete_name=None, parent=None, sequence=10, action="", web_icon=""):
        self.id = ident
        self.name = name
        self.display_name = name
        self.complete_name = complete_name or name
        self.parent_id = parent
        self.sequence = sequence
        self.action = action
        self.web_icon = web_icon
        self.groups_id = _RecordSet([])
        self._owner = None

    def exists(self):
        return self

    def unlink(self):
        if self._owner is not None and self in self._owner:
            self._owner.remove(self)
        return True


class _MenuModel(_RecordSet):
    def __init__(self, menus=(), visible_ids=None):
        super().__init__(menus)
        self.visible_ids = visible_ids
        for menu in self:
            menu._owner = self

    def sudo(self):
        return self

    def with_context(self, **kwargs):
        self.context = kwargs
        return self

    def _visible_menu_ids(self, debug=False):
        if self.visible_ids is None:
            raise AttributeError("_visible_menu_ids")
        return list(self.visible_ids)

    def browse(self, record_id):
        if isinstance(record_id, (list, tuple, set)):
            wanted = {int(item or 0) for item in record_id}
            return _RecordSet([record for record in self if int(record.id or 0) in wanted])
        for record in self:
            if int(record.id or 0) == int(record_id or 0):
                return record
        return _RecordSet([])

    def search(self, domain, order=None, limit=None):
        parent_filter = None
        id_values = None
        for field, op, value in domain:
            if field == "parent_id" and op == "=":
                parent_filter = int(value or 0)
            if field == "id" and op == "in":
                id_values = {int(item or 0) for item in value}
        rows = list(self)
        if parent_filter is not None:
            rows = [row for row in rows if int(getattr(getattr(row, "parent_id", None), "id", 0) or 0) == parent_filter]
        if id_values is not None:
            rows = [row for row in rows if int(row.id or 0) in id_values]
        rows.sort(key=lambda row: (int(getattr(row, "sequence", 0) or 0), int(row.id or 0)), reverse=bool(order and "desc" in order))
        if limit == 1:
            return rows[0] if rows else _RecordSet([])
        return _RecordSet(rows[:limit] if limit else rows)

    def create(self, vals):
        parent_id = vals.get("parent_id")
        parent = self.browse(parent_id).exists() if parent_id else None
        menu = _Menu(
            max([int(getattr(row, "id", 0) or 0) for row in self] + [0]) + 1,
            vals.get("name"),
            vals.get("name"),
            parent=parent if parent else None,
            sequence=int(vals.get("sequence") or 0),
            action=vals.get("action") or "",
            web_icon=vals.get("web_icon") or "",
        )
        menu._owner = self
        self.append(menu)
        return menu


class _ModelDataModel(_RecordSet):
    def sudo(self):
        return self

    def search(self, domain):
        model = next((value for field, op, value in domain if field == "model" and op == "="), "")
        res_ids = next((value for field, op, value in domain if field == "res_id" and op == "in"), None)
        rows = list(self)
        if model:
            rows = [row for row in rows if getattr(row, "model", "") == model]
        if res_ids is not None:
            ids = {int(item or 0) for item in res_ids}
            rows = [row for row in rows if int(getattr(row, "res_id", 0) or 0) in ids]
        return _RecordSet(rows)


class _ActionWindow:
    def __init__(self, ident, res_model="", view_mode="tree,form"):
        self.id = ident
        self.res_model = res_model
        self.view_mode = view_mode

    def exists(self):
        return self


class _ActionWindowModel(_RecordSet):
    def sudo(self):
        return self

    def browse(self, record_id):
        for record in self:
            if int(getattr(record, "id", 0) or 0) == int(record_id or 0):
                return record
        return _RecordSet([])


class _Policy:
    def __init__(
        self,
        ident,
        menu,
        *,
        company,
        visible=True,
        custom_label="",
        sequence_override=0,
        target_parent=None,
        role_groups=None,
        active=True,
    ):
        self.id = ident
        self.menu_id = menu
        self.company_id = company
        self.visible = visible
        self.custom_label = custom_label
        self.sequence_override = sequence_override
        self.target_parent_menu_id = target_parent
        self.role_group_ids = _RecordSet(role_groups or [])
        self.active = active
        self.note = ""
        self.scope_summary = "、".join(group.display_name for group in self.role_group_ids) or "所有业务角色"
        self.effect_summary = "隐藏菜单" if not visible else "保持原样显示"
        self.preview_summary = ""

    def exists(self):
        return self

    def write(self, vals):
        if "company_id" in vals:
            self.company_id = vals["company_id"] if hasattr(vals["company_id"], "id") else types.SimpleNamespace(id=vals["company_id"])
        if "menu_id" in vals:
            self.menu_id = vals["menu_id"] if hasattr(vals["menu_id"], "id") else _Menu(vals["menu_id"], "菜单%s" % vals["menu_id"])
        if "target_parent_menu_id" in vals:
            value = vals["target_parent_menu_id"]
            self.target_parent_menu_id = value if hasattr(value, "id") else (_Menu(value, "分组%s" % value) if value else None)
        if "custom_label" in vals:
            self.custom_label = vals["custom_label"] or ""
        if "sequence_override" in vals:
            self.sequence_override = int(vals["sequence_override"] or 0)
        if "visible" in vals:
            self.visible = bool(vals["visible"])
        if "active" in vals:
            self.active = bool(vals["active"])
        if "note" in vals:
            self.note = vals["note"] or ""
        if "role_group_ids" in vals:
            command = vals["role_group_ids"][0] if vals["role_group_ids"] else None
            ids = command[2] if command and len(command) >= 3 else []
            self.role_group_ids = _RecordSet([_Group(group_id, "用户组%s" % group_id) for group_id in ids])
        return True


class _PolicyModel(_RecordSet):
    def __init__(self, policies, user):
        super().__init__(policies)
        self.user = user
        self.domain = None
        self.order = None

    def search(self, domain, order=None, limit=None):
        self.domain = domain
        self.order = order
        company_id = next((value for field, op, value in domain if field == "company_id" and op == "="), 0)
        menu_id = next((value for field, op, value in domain if field == "menu_id" and op == "="), 0)
        menu_ids = next((value for field, op, value in domain if field == "menu_id" and op == "in"), None)
        menu_id_set = {int(item or 0) for item in (menu_ids or [])} if menu_ids is not None else set()
        active_required = any(field == "active" and op == "=" and value is True for field, op, value in domain)
        rows = [
            policy
            for policy in self
            if int(policy.company_id.id or 0) == int(company_id or 0)
            and policy.menu_id
            and (not menu_id or int(policy.menu_id.id or 0) == int(menu_id or 0))
            and (not menu_id_set or int(policy.menu_id.id or 0) in menu_id_set)
            and (not active_required or policy.active)
        ]
        if order and "menu_id" in order:
            rows.sort(key=lambda policy: (
                int(policy.menu_id.id or 0),
                -int(policy.id or 0) if "id desc" in order else int(policy.id or 0),
            ))
        elif order:
            rows.sort(key=lambda policy: int(policy.id or 0), reverse="desc" in order)
        result = _RecordSet(rows)
        return _RecordSet(result[:limit]) if limit else result

    def create(self, vals):
        menu_value = vals.get("menu_id")
        target_value = vals.get("target_parent_menu_id")
        company_value = vals.get("company_id")
        role_command = vals.get("role_group_ids")[0] if vals.get("role_group_ids") else None
        role_group_ids = role_command[2] if role_command and len(role_command) >= 3 else []
        policy = _Policy(
            max([int(getattr(row, "id", 0) or 0) for row in self] + [0]) + 1,
            menu_value if hasattr(menu_value, "id") else _Menu(menu_value, "菜单%s" % menu_value),
            company=company_value if hasattr(company_value, "id") else types.SimpleNamespace(id=company_value),
            visible=bool(vals.get("visible", True)),
            custom_label=vals.get("custom_label") or "",
            sequence_override=int(vals.get("sequence_override") or 0),
            target_parent=target_value if hasattr(target_value, "id") else (_Menu(target_value, "分组%s" % target_value) if target_value else None),
            role_groups=[_Group(group_id, "用户组%s" % group_id) for group_id in role_group_ids],
            active=bool(vals.get("active", True)),
        )
        self.append(policy)
        return policy

    def _runtime_policies_for_user(self, user=None):
        user = user or self.user
        user_group_ids = set(group.id for group in user.groups_id)
        applicable = {}
        for policy in reversed(self):
            if not policy.active:
                continue
            role_group_ids = set(group.id for group in policy.role_group_ids)
            if role_group_ids and not (role_group_ids & user_group_ids):
                continue
            menu_id = int(policy.menu_id.id)
            existing = applicable.get(menu_id)
            if existing and existing.role_group_ids and not policy.role_group_ids:
                continue
            if existing and bool(existing.role_group_ids) == bool(policy.role_group_ids):
                continue
            applicable[menu_id] = policy
        return applicable


class _CompanyModel(_RecordSet):
    pass


class _Contract:
    def __init__(self, ident, vals):
        self.id = ident
        self.version_no = 1
        self.write(vals)

    def write(self, vals):
        for key, value in vals.items():
            setattr(self, key, value)
        return True

    def action_publish(self):
        self.status = "published"
        self.version_no = int(getattr(self, "version_no", 1) or 1) + 1


class _ContractModel(_RecordSet):
    def sudo(self):
        return self

    def search(self, domain, order=None, limit=None):
        name = next((value for field, op, value in domain if field == "name" and op == "="), "")
        company_id = next((value for field, op, value in domain if field == "company_id" and op == "="), 0)
        rows = [
            contract
            for contract in self
            if getattr(contract, "name", "") == name
            and int(getattr(getattr(contract, "company_id", None), "id", getattr(contract, "company_id", 0)) or 0) == int(company_id or 0)
        ]
        if limit == 1:
            return rows[0] if rows else _RecordSet([])
        return _RecordSet(rows[:limit] if limit else rows)

    def create(self, vals):
        contract = _Contract(max([int(getattr(row, "id", 0) or 0) for row in self] + [0]) + 1, vals)
        self.append(contract)
        return contract


class _RuntimeContractModel(_RecordSet):
    def sudo(self):
        return self

    def search(self, domain, order=None, limit=None):
        name = next((value for field, op, value in domain if field == "name" and op == "="), "")
        model = next((value for field, op, value in domain if field == "model" and op == "="), "")
        rows = [
            contract
            for contract in self
            if getattr(contract, "name", "") == name
            and getattr(contract, "model", "") == model
            and getattr(contract, "active", True)
            and getattr(contract, "status", "") == "published"
        ]
        rows.sort(key=lambda row: (int(getattr(row, "version_no", 0) or 0), int(getattr(row, "id", 0) or 0)), reverse=True)
        if limit == 1:
            return rows[0] if rows else _RecordSet([])
        return _RecordSet(rows[:limit] if limit else rows)


class _ContractVersion:
    def __init__(self, ident, contract, version_no, snapshot_json):
        self.id = ident
        self.contract_id = contract
        self.version_no = version_no
        self.snapshot_json = snapshot_json
        self.status = "published"
        self.created_by = None


class _ContractVersionModel(_RecordSet):
    def sudo(self):
        return self

    def search(self, domain, order=None, limit=None):
        contract_id = next((value for field, op, value in domain if field == "contract_id" and op == "="), 0)
        version_no = next((value for field, op, value in domain if field == "version_no" and op == "="), None)
        rows = [
            version
            for version in self
            if int(getattr(version.contract_id, "id", 0) or 0) == int(contract_id or 0)
            and (version_no is None or int(version.version_no or 0) == int(version_no or 0))
        ]
        rows.sort(key=lambda version: (int(version.version_no or 0), int(version.id or 0)), reverse=True)
        if limit == 1:
            return rows[0] if rows else _RecordSet([])
        return _RecordSet(rows[:limit] if limit else rows)


class _User:
    def __init__(self, groups):
        self.groups_id = _RecordSet(groups)

    def has_group(self, xmlid):
        return xmlid in {
            "smart_core.group_smart_core_business_config_admin",
            "smart_core.group_smart_core_admin",
        }


class _Env(dict):
    def __init__(self, *args, company, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.user = user

    def __call__(self, user=None):
        return self


class TestMenuConfigurationAudit(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

    def assertOverlayDirectoryNavigationContract(self, node):
        self.assertEqual(node["target_type"], "directory")
        self.assertEqual(node["delivery_mode"], "none")
        self.assertIsNone(node["scene_key"])
        self.assertIsNone(node["native_action_id"])
        self.assertIsNone(node["native_model"])
        self.assertIsNone(node["native_view_mode"])
        self.assertEqual(node["confidence"], "medium")
        self.assertFalse(node["compatibility_used"])
        self.assertFalse(node["is_clickable"])

    def assertOverlayActionNavigationContract(self, node, *, action_id, model, view_mode="tree,form"):
        self.assertEqual(node["target_type"], "action")
        self.assertEqual(node["delivery_mode"], "custom_action")
        self.assertIsNone(node["scene_key"])
        self.assertEqual(node["native_action_id"], action_id)
        self.assertEqual(node["native_model"], model)
        self.assertEqual(node["native_view_mode"], view_mode)
        self.assertEqual(node["confidence"], "medium")
        self.assertTrue(node["compatibility_used"])
        self.assertTrue(node["is_clickable"])
        self.assertEqual(node["target"]["action_id"], action_id)
        self.assertEqual(node["entry_target"]["type"], "compatibility")

    def test_menu_config_protected_node_exclusions_are_extension_registered(self):
        module = _load_policy_model()

        self.assertEqual(module.protected_node_excluded_fingerprint_tokens(), ())

        module.register_protected_node_excluded_fingerprint_token("legacy acceptance")
        module.register_protected_node_excluded_fingerprint_token("legacy acceptance")
        module.register_protected_node_excluded_fingerprint_token("")

        self.assertEqual(module.protected_node_excluded_fingerprint_tokens(), ("legacy acceptance",))

    def test_menu_config_audit_reports_applicable_policy_counts(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        finance_group = _Group(101, "财务")
        pm_group = _Group(102, "项目经理")
        user = _User([finance_group])
        menu_a = _Menu(11, "合同中心")
        menu_b = _Menu(12, "费用申请")
        parent = _Menu(20, "财务中心")
        policies = _PolicyModel(
            [
                _Policy(1, menu_a, company=company, visible=False),
                _Policy(2, menu_b, company=company, custom_label="费用/保证金申请", target_parent=parent, role_groups=[finance_group]),
                _Policy(3, menu_b, company=company, custom_label="项目费用申请", role_groups=[pm_group]),
            ],
            user=user,
        )
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationAuditHandler(env=env, params={"company_id": 7})

        result = handler.handle()

        self.assertTrue(result["ok"])
        summary = result["data"]["summary"]
        self.assertEqual(summary["runtime_source"], "ui.menu.config.policy")
        self.assertEqual(summary["configured_policy_count"], 3)
        self.assertEqual(summary["applicable_policy_count"], 2)
        self.assertEqual(summary["hidden_count"], 1)
        self.assertEqual(summary["renamed_count"], 1)
        self.assertEqual(summary["moved_count"], 1)
        self.assertEqual(summary["not_applicable_policy_ids"], [3])
        self.assertEqual(summary["scope_root_menu_id"], 0)
        self.assertFalse(summary["scope_root_valid"])

        applicable_ids = [row["id"] for row in result["data"]["applicable_policies"]]
        self.assertEqual(applicable_ids, [1, 2])
        self.assertEqual(result["meta"]["source_authority"]["kind"], "ui_menu_config_audit")

    def test_menu_config_audit_reports_runtime_contract_rows_not_legacy_policy_rows(self):
        module = _load_handler()
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        legacy_menu = _Menu(11, "旧表菜单")
        policies = _PolicyModel([_Policy(1, legacy_menu, company=company, visible=True)], user=user)
        policies._runtime_menu_config_source_for_user = lambda user=None: (
            {
                99: {
                    "active": True,
                    "menu_id": 99,
                    "menu_label": "合同菜单",
                    "visible": False,
                    "custom_label": "合同隐藏菜单",
                }
            },
            module.MENU_CONFIG_RUNTIME_SOURCE_CONTRACT,
        )
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = module.MenuConfigurationAuditHandler(env=env, params={"company_id": 7})

        result = handler.handle()

        self.assertTrue(result["ok"])
        summary = result["data"]["summary"]
        self.assertEqual(summary["runtime_source"], module.MENU_CONFIG_RUNTIME_SOURCE_CONTRACT)
        self.assertTrue(summary["contract_authoritative"])
        self.assertEqual(summary["policy_table_count"], 1)
        self.assertEqual(summary["runtime_policy_count"], 1)
        self.assertEqual(summary["applicable_policy_count"], 1)
        self.assertEqual(summary["hidden_count"], 1)
        self.assertEqual(result["data"]["applicable_policies"][0]["menu_id"], 99)
        self.assertEqual(result["data"]["applicable_policies"][0]["runtime_source"], module.MENU_CONFIG_RUNTIME_SOURCE_CONTRACT)

    def test_menu_config_contract_json_uses_menu_orchestration_schema(self):
        company = types.SimpleNamespace(id=7)
        group = _Group(101, "财务")
        menu = _Menu(11, "合同中心", "业务菜单 / 合同中心")
        parent = _Menu(20, "财务中心", "业务菜单 / 财务中心")
        policy = _Policy(
            1,
            menu,
            company=company,
            custom_label="合同办理",
            sequence_override=30,
            target_parent=parent,
            role_groups=[group],
        )

        payload = self.module._menu_config_contract_json(7, [policy])

        orchestration = payload["menu_orchestration"]
        self.assertEqual(orchestration["schema_version"], "menu_orchestration.v1")
        self.assertEqual(orchestration["source"], "smart_core.lowcode.menu_config")
        self.assertEqual(orchestration["source_status"], "tenant_runtime")
        self.assertEqual(orchestration["runtime_source"], "ui.menu.config.policy")
        self.assertEqual(orchestration["policy_count"], 1)
        self.assertEqual(orchestration["policies"][0]["menu_id"], 11)
        self.assertEqual(orchestration["policies"][0]["custom_label"], "合同办理")
        self.assertEqual(orchestration["policies"][0]["target_parent_menu_id"], 20)
        self.assertEqual(orchestration["policies"][0]["role_group_ids"], [101])

    def test_menu_config_save_mirrors_published_business_contract(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        policies = _PolicyModel([], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationSaveHandler(
            env=env,
            params={
                "company_id": 7,
                "rows": [
                    {
                        "menu_id": 11,
                        "target_parent_menu_id": 20,
                        "custom_label": "合同办理",
                        "sequence_override": 30,
                        "visible": True,
                    }
                ],
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["saved_count"], 1)
        self.assertEqual(len(contracts), 1)
        contract = contracts[0]
        self.assertEqual(contract.name, "menu.config.company.7")
        self.assertEqual(contract.model, "ir.ui.menu")
        self.assertEqual(contract.status, "published")
        self.assertEqual(contract.version_no, 2)
        self.assertEqual(contract.contract_json["menu_orchestration"]["policy_count"], 1)
        self.assertEqual(contract.contract_json["menu_orchestration"]["source"], "smart_core.lowcode.menu_config")
        self.assertTrue(result["meta"]["contract_mirrored"])
        self.assertEqual(result["meta"]["scope_root_menu_id"], 0)
        self.assertFalse(result["meta"]["scope_root_valid"])

    def test_menu_config_save_reports_valid_business_root_scope(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        business_root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=business_root, sequence=20)
        policies = _PolicyModel([], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ir.ui.menu": _MenuModel([business_root, project_center]),
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationSaveHandler(
            env=env,
            params={
                "company_id": 7,
                "root_menu_id": 291,
                "rows": [
                    {
                        "menu_id": 292,
                        "target_parent_menu_id": 291,
                        "custom_label": "项目中心",
                        "sequence_override": 20,
                        "visible": True,
                    }
                ],
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["saved_count"], 1)
        self.assertEqual(result["meta"]["scope_root_menu_id"], 291)
        self.assertTrue(result["meta"]["scope_root_valid"])
        self.assertEqual(len(contracts), 1)

    def test_menu_config_panel_scopes_rows_to_business_root_after_policy_moves(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        business_root = _Menu(291, "智慧施工管理平台")
        system_settings = _Menu(297, "系统设置", parent=business_root, sequence=90)
        unrelated_root = _Menu(1, "设置")
        unrelated_child = _Menu(2, "技术参数", parent=unrelated_root, sequence=10)
        menus = _MenuModel([business_root, system_settings, unrelated_root, unrelated_child])
        policies = _PolicyModel(
            [
                _Policy(1, business_root, company=company, target_parent=None),
                _Policy(2, system_settings, company=company, target_parent=business_root),
                _Policy(3, unrelated_root, company=company, target_parent=None),
                _Policy(4, unrelated_child, company=company, target_parent=unrelated_root),
            ],
            user=user,
        )
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([]),
                "ui.menu.config.policy": policies,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationLoadHandler(
            env=env,
            params={
                "company_id": 7,
                "root_menu_id": 291,
                "menu_ids": [291, 297, 1, 2],
            },
        )
        handler._group_option_records = lambda menus, policies: _RecordSet([])
        handler._expand_with_parent_ids = lambda menus: [int(menu.id) for menu in menus]

        result = handler.handle({"params": handler.params})

        self.assertEqual(result["meta"]["scope_root_menu_id"], 291)
        self.assertTrue(result["meta"]["scope_root_valid"])
        self.assertEqual([row["id"] for row in result["data"]["menus"]], [291, 297])
        self.assertEqual(set(result["data"]["policies"].keys()), {291, 297})
        self.assertEqual([(row["id"], row["name"]) for row in result["data"]["tree"]], [(291, "智慧施工管理平台")])
        self.assertEqual(
            [(row["id"], row["name"]) for row in result["data"]["tree"][0]["children"]],
            [(297, "系统设置")],
        )

    def test_menu_config_panel_excludes_hidden_menu_outside_navigation_boundary(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        business_root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=business_root, sequence=20)
        visible_entry = _Menu(379, "项目台账", parent=project_center, sequence=10)
        hidden_policy_entry = _Menu(999, "历史隐藏菜单", parent=project_center, sequence=90)
        menus = _MenuModel([business_root, project_center, visible_entry, hidden_policy_entry])
        policies = _PolicyModel(
            [
                _Policy(1, business_root, company=company),
                _Policy(2, project_center, company=company),
                _Policy(3, visible_entry, company=company),
                _Policy(4, hidden_policy_entry, company=company, visible=False),
            ],
            user=user,
        )
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([]),
                "ui.menu.config.policy": policies,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationLoadHandler(
            env=env,
            params={
                "company_id": 7,
                "root_menu_id": 291,
                "menu_ids": [291, 292, 379],
            },
        )
        handler._group_option_records = lambda menus, policies: _RecordSet([])
        handler._expand_with_parent_ids = lambda menus: [int(menu.id) for menu in menus]

        result = handler.handle({"params": handler.params})

        self.assertEqual([row["id"] for row in result["data"]["menus"]], [291, 292, 379])
        self.assertEqual(set(result["data"]["policies"].keys()), {291, 292, 379})
        self.assertNotIn(999, {row["id"] for row in result["data"]["menus"]})
        self.assertEqual(result["meta"]["scoped_menu_count"], 3)

    def test_menu_config_panel_excludes_unrequested_unconfigured_business_root_menu(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        business_root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=business_root, sequence=20)
        visible_entry = _Menu(379, "项目台账", parent=project_center, sequence=10)
        unconfigured_entry = _Menu(410, "未配置业务入口", parent=project_center, sequence=30)
        menus = _MenuModel([business_root, project_center, visible_entry, unconfigured_entry])
        policies = _PolicyModel(
            [
                _Policy(1, business_root, company=company),
                _Policy(2, project_center, company=company),
                _Policy(3, visible_entry, company=company),
            ],
            user=user,
        )
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([]),
                "ui.menu.config.policy": policies,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationLoadHandler(
            env=env,
            params={
                "company_id": 7,
                "root_menu_id": 291,
                "menu_ids": [291, 292, 379],
            },
        )
        handler._group_option_records = lambda menus, policies: _RecordSet([])
        handler._expand_with_parent_ids = lambda menus: [int(menu.id) for menu in menus]

        result = handler.handle({"params": handler.params})

        self.assertEqual([row["id"] for row in result["data"]["menus"]], [291, 292, 379])
        self.assertEqual(set(result["data"]["policies"].keys()), {291, 292, 379})
        self.assertNotIn(410, {row["id"] for row in result["data"]["menus"]})
        self.assertEqual(result["meta"]["scoped_menu_count"], 3)

    def test_menu_config_panel_excludes_hidden_policy_outside_business_root(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        business_root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=business_root, sequence=20)
        visible_entry = _Menu(379, "项目台账", parent=project_center, sequence=10)
        settings_root = _Menu(1, "设置")
        technical_menu = _Menu(42, "菜单项", parent=settings_root, sequence=10)
        menus = _MenuModel([business_root, project_center, visible_entry, settings_root, technical_menu])
        policies = _PolicyModel(
            [
                _Policy(1, business_root, company=company),
                _Policy(2, project_center, company=company),
                _Policy(3, visible_entry, company=company),
                _Policy(4, technical_menu, company=company, visible=False),
            ],
            user=user,
        )
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([]),
                "ui.menu.config.policy": policies,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationLoadHandler(
            env=env,
            params={
                "company_id": 7,
                "root_menu_id": 291,
                "menu_ids": [291, 292, 379],
            },
        )
        handler._group_option_records = lambda menus, policies: _RecordSet([])
        handler._expand_with_parent_ids = lambda menus: [int(menu.id) for menu in menus]

        result = handler.handle({"params": handler.params})

        self.assertEqual([row["id"] for row in result["data"]["menus"]], [291, 292, 379])
        self.assertEqual(set(result["data"]["policies"].keys()), {291, 292, 379})
        self.assertNotIn(42, {row["id"] for row in result["data"]["menus"]})

    def test_menu_config_save_rejects_menu_outside_business_root(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        business_root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=business_root, sequence=20)
        settings_root = _Menu(1, "设置")
        technical_menu = _Menu(42, "菜单项", parent=settings_root, sequence=10)
        policies = _PolicyModel([], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ir.ui.menu": _MenuModel([business_root, project_center, settings_root, technical_menu]),
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationSaveHandler(
            env=env,
            params={
                "company_id": 7,
                "root_menu_id": 291,
                "rows": [
                    {
                        "menu_id": 42,
                        "target_parent_menu_id": 1,
                        "visible": False,
                    }
                ],
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["reason_code"], "MENU_CONFIG_SCOPE_VIOLATION")
        self.assertEqual(len(policies), 0)
        self.assertEqual(len(contracts), 0)

    def test_menu_config_save_deactivates_superseded_same_scope_policy(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        menu = _Menu(11, "合同中心")
        old_parent = _Menu(20, "旧分组")
        new_parent = _Menu(21, "新分组")
        old_policy = _Policy(1, menu, company=company, target_parent=old_parent)
        current_policy = _Policy(2, menu, company=company, target_parent=old_parent)
        policies = _PolicyModel([old_policy, current_policy], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationSaveHandler(
            env=env,
            params={
                "company_id": 7,
                "rows": [
                    {
                        "policy_id": 2,
                        "menu_id": 11,
                        "target_parent_menu_id": 21,
                        "visible": True,
                    }
                ],
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertTrue(result["ok"])
        self.assertFalse(old_policy.active)
        self.assertTrue(current_policy.active)
        self.assertEqual(current_policy.target_parent_menu_id.id, new_parent.id)
        active_rows = [
            row for row in contracts[0].contract_json["menu_orchestration"]["policies"]
            if row["menu_id"] == 11 and row["active"]
        ]
        self.assertEqual(len(active_rows), 1)
        self.assertEqual(active_rows[0]["target_parent_menu_id"], 21)

    def test_menu_config_create_adds_menu_policy_and_contract_version(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        parent = _Menu(20, "业务配置", "智慧施工 / 业务配置")
        source = _Menu(
            30,
            "菜单配置",
            "智慧施工 / 业务配置 / 菜单配置",
            parent=parent,
            sequence=20,
            action="ir.actions.act_window,88",
        )
        menus = _MenuModel([parent, source])
        policies = _PolicyModel([], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([]),
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationCreateHandler(
            env=env,
            params={
                "company_id": 7,
                "name": "菜单配置副本",
                "parent_menu_id": 20,
                "source_menu_id": 30,
                "visible": True,
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertTrue(result["ok"])
        self.assertEqual(len(menus), 3)
        created = menus[-1]
        self.assertEqual(created.name, "菜单配置副本")
        self.assertEqual(created.parent_id.id, 20)
        self.assertEqual(created.action, "ir.actions.act_window,88")
        self.assertEqual(len(policies), 1)
        self.assertEqual(policies[0].menu_id.id, created.id)
        self.assertEqual(policies[0].target_parent_menu_id.id, 20)
        self.assertEqual(policies[0].sequence_override, 30)
        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts[0].contract_json["menu_orchestration"]["policy_count"], 1)
        self.assertEqual(contracts[0].contract_json["menu_orchestration"]["source"], "smart_core.lowcode.menu_config")
        self.assertEqual(result["meta"]["source_authority"]["kind"], "ui_menu_config_menu_create_write_proxy")
        self.assertEqual(result["meta"]["source_authority"]["lowcode_boundary"], "menu_config")
        self.assertEqual(result["meta"]["scope_root_menu_id"], 0)
        self.assertFalse(result["meta"]["scope_root_valid"])

    def test_menu_config_delete_removes_created_menu_and_deactivates_policy(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        parent = _Menu(20, "业务配置", "智慧施工 / 业务配置")
        created = _Menu(31, "临时菜单", "智慧施工 / 业务配置 / 临时菜单", parent=parent, sequence=30)
        menus = _MenuModel([parent, created])
        policy = _Policy(1, created, company=company, custom_label="临时菜单", sequence_override=30)
        policies = _PolicyModel([policy], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([]),
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationDeleteHandler(
            env=env,
            params={
                "company_id": 7,
                "menu_id": 31,
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["deleted_menu_ids"], [31])
        self.assertEqual([menu.id for menu in menus], [20])
        self.assertFalse(policy.active)
        self.assertFalse(policy.visible)
        self.assertEqual(len(contracts), 1)
        self.assertEqual(result["meta"]["source_authority"]["kind"], "ui_menu_config_menu_delete_write_proxy")
        self.assertEqual(result["meta"]["scope_root_menu_id"], 0)
        self.assertFalse(result["meta"]["scope_root_valid"])

    def test_menu_config_delete_rejects_module_menu_with_xmlid(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        menu = _Menu(31, "系统菜单", "智慧施工 / 系统菜单", sequence=30)
        menus = _MenuModel([menu])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.model.data": _ModelDataModel([
                    types.SimpleNamespace(model="ir.ui.menu", res_id=31, module="smart_core", name="menu_system"),
                ]),
                "ui.menu.config.policy": _PolicyModel([], user=user),
                "ui.business.config.contract": _ContractModel([]),
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationDeleteHandler(
            env=env,
            params={
                "company_id": 7,
                "menu_id": 31,
            },
        )

        result = handler.handle({"params": handler.params})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["reason_code"], "PROTECTED_MENU")
        self.assertEqual([row.id for row in menus], [31])

    def test_menu_config_rollback_restores_policy_rows_from_contract_version(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        menu = _Menu(11, "合同中心")
        extra_menu = _Menu(12, "费用申请")
        parent = _Menu(20, "合同中心")
        existing = _Policy(1, menu, company=company, custom_label="错误名称", sequence_override=90)
        extra = _Policy(2, extra_menu, company=company, custom_label="多余配置")
        policies = _PolicyModel([existing, extra], user=user)
        snapshot = self.module._menu_config_contract_json(7, [
            _Policy(1, menu, company=company, custom_label="合同办理", sequence_override=30, target_parent=parent)
        ])
        current_snapshot = self.module._menu_config_contract_json(7, [existing, extra])
        contract = _Contract(5, {
            "name": "menu.config.company.7",
            "model": "ir.ui.menu",
            "company_id": company,
            "view_type": False,
            "action_id": False,
            "view_id": False,
            "role_key": False,
            "contract_json": current_snapshot,
            "status": "published",
        })
        contract.version_no = 3
        versions = _ContractVersionModel([
            _ContractVersion(1, contract, 2, snapshot),
            _ContractVersion(2, contract, 3, current_snapshot),
        ])
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": _ContractModel([contract]),
                "ui.business.config.contract.version": versions,
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationRollbackHandler(env=env, params={"company_id": 7})

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["rolled_back_to_version"], 2)
        self.assertEqual(result["data"]["restored_count"], 1)
        self.assertEqual(existing.custom_label, "合同办理")
        self.assertEqual(existing.sequence_override, 30)
        self.assertEqual(existing.target_parent_menu_id.id, 20)
        self.assertFalse(extra.active)
        self.assertEqual(contract.contract_json, snapshot)
        self.assertEqual(contract.status, "published")
        self.assertEqual(contract.version_no, 3)

    def test_menu_config_versions_lists_contract_version_summaries(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        menu = _Menu(11, "合同中心")
        hidden_menu = _Menu(12, "费用申请")
        parent = _Menu(20, "财务中心")
        snapshot_v2 = self.module._menu_config_contract_json(7, [
            _Policy(1, menu, company=company, custom_label="合同办理", sequence_override=30, target_parent=parent),
            _Policy(2, hidden_menu, company=company, visible=False),
        ])
        snapshot_v3 = self.module._menu_config_contract_json(7, [
            _Policy(1, menu, company=company, custom_label="合同办理"),
        ])
        contract = _Contract(5, {
            "name": "menu.config.company.7",
            "model": "ir.ui.menu",
            "company_id": company,
            "view_type": False,
            "action_id": False,
            "view_id": False,
            "role_key": False,
            "contract_json": snapshot_v3,
            "status": "published",
        })
        contract.version_no = 3
        env = _Env(
            {
                "ui.business.config.contract": _ContractModel([contract]),
                "ui.business.config.contract.version": _ContractVersionModel([
                    _ContractVersion(1, contract, 2, snapshot_v2),
                    _ContractVersion(2, contract, 3, snapshot_v3),
                ]),
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationVersionsHandler(env=env, params={"company_id": 7})

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["contract"]["version_no"], 3)
        self.assertEqual([row["version_no"] for row in result["data"]["versions"]], [3, 2])
        version_two = result["data"]["versions"][1]
        self.assertEqual(version_two["summary"]["policy_count"], 2)
        self.assertEqual(version_two["summary"]["hidden_count"], 1)
        self.assertEqual(version_two["summary"]["renamed_count"], 1)
        self.assertEqual(version_two["summary"]["moved_count"], 1)
        self.assertEqual(version_two["summary"]["reordered_count"], 1)

    def test_menu_config_versions_does_not_bootstrap_contract_by_default(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        menu = _Menu(11, "合同中心")
        hidden_menu = _Menu(12, "费用申请")
        policies = _PolicyModel([
            _Policy(1, menu, company=company, custom_label="合同办理", sequence_override=30),
            _Policy(2, hidden_menu, company=company, visible=False),
        ], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "ui.business.config.contract.version": _ContractVersionModel([]),
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationVersionsHandler(env=env, params={"company_id": 7})

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(len(contracts), 0)
        self.assertIsNone(result["data"]["contract"])
        self.assertEqual(result["data"]["versions"], [])
        self.assertFalse(result["meta"]["bootstrapped_from_current_policies"])
        self.assertTrue(result["meta"]["bootstrap_required"])

    def test_menu_config_versions_bootstraps_contract_from_existing_policies_when_explicit(self):
        company = types.SimpleNamespace(id=7, display_name="测试公司", name="测试公司")
        user = _User([])
        menu = _Menu(11, "合同中心")
        hidden_menu = _Menu(12, "费用申请")
        policies = _PolicyModel([
            _Policy(1, menu, company=company, custom_label="合同办理", sequence_override=30),
            _Policy(2, hidden_menu, company=company, visible=False),
        ], user=user)
        contracts = _ContractModel([])
        env = _Env(
            {
                "ui.menu.config.policy": policies,
                "ui.business.config.contract": contracts,
                "ui.business.config.contract.version": _ContractVersionModel([]),
                "res.company": _CompanyModel([company]),
            },
            company=company,
            user=user,
        )
        handler = self.module.MenuConfigurationVersionsHandler(env=env, params={"company_id": 7, "allow_bootstrap": True})

        result = handler.handle()

        self.assertTrue(result["ok"])
        self.assertEqual(len(contracts), 1)
        self.assertEqual(result["data"]["contract"]["model"], "ir.ui.menu")
        self.assertEqual(result["data"]["contract"]["summary"]["policy_count"], 2)
        self.assertEqual(result["data"]["contract"]["summary"]["hidden_count"], 1)
        self.assertEqual(result["data"]["contract"]["summary"]["renamed_count"], 1)
        self.assertTrue(result["meta"]["bootstrapped_from_current_policies"])

    def test_runtime_contract_policy_skips_deleted_menu_and_ignores_deleted_target_parent(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(10, "智慧施工管理平台")
        menu = _Menu(11, "施工管理", parent=root)
        menus = _MenuModel([root, menu])
        contract_json = {
            "menu_orchestration": {
                "schema_version": "menu_orchestration.v1",
                "policies": [
                    {
                        "active": True,
                        "menu_id": 845,
                        "menu_label": "已删除临时菜单",
                        "visible": True,
                        "target_parent_menu_id": 10,
                    },
                    {
                        "active": True,
                        "menu_id": 11,
                        "menu_label": "施工管理",
                        "visible": True,
                        "target_parent_menu_id": 999,
                        "sequence_override": 40,
                    },
                ],
            },
        }
        contract = types.SimpleNamespace(
            id=1,
            active=True,
            status="published",
            name="menu.config.company.7",
            model="ir.ui.menu",
            company_id=company,
            version_no=3,
            contract_json=contract_json,
        )
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ui.business.config.contract": _RuntimeContractModel([contract]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env

        result = policy_model._runtime_contract_policies_for_user(user=user)

        self.assertNotIn(845, result)
        self.assertIn(11, result)
        self.assertEqual(result[11]["target_parent_menu_id"], 0)

    def test_runtime_menu_config_contract_is_authoritative_over_legacy_policy_rows(self):
        module = _load_policy_model()
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        contract_policy = {
            "active": True,
            "menu_id": 11,
            "menu_label": "合同中心",
            "visible": False,
        }
        legacy_policy = types.SimpleNamespace(
            menu_id=types.SimpleNamespace(id=11),
            visible=True,
            custom_label="旧表显示名称",
            role_group_ids=_RecordSet([]),
        )
        policy_model._runtime_contract_policy_source_for_user = lambda user=None: ({11: contract_policy}, True)
        policy_model._runtime_policies_for_user = lambda user=None: {11: legacy_policy, 12: legacy_policy}

        policies, runtime_source = policy_model._runtime_menu_config_source_for_user(user=_User([]))

        self.assertEqual(runtime_source, module.MENU_CONFIG_RUNTIME_SOURCE_CONTRACT)
        self.assertEqual(policies, {11: contract_policy})
        self.assertNotIn(12, policies)

    def test_runtime_empty_menu_contract_still_blocks_legacy_policy_fallback(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        menu = _Menu(11, "合同中心")
        contract = types.SimpleNamespace(
            id=1,
            active=True,
            status="published",
            name="menu.config.company.7",
            model="ir.ui.menu",
            company_id=company,
            version_no=3,
            contract_json={
                "menu_orchestration": {
                    "schema_version": "menu_orchestration.v1",
                    "policies": [],
                },
            },
        )
        legacy_policy = _Policy(1, menu, company=company, visible=True)
        env = _Env(
            {
                "ir.ui.menu": _MenuModel([menu]),
                "ui.business.config.contract": _RuntimeContractModel([contract]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_policies_for_user = lambda user=None: {11: legacy_policy}

        policies, runtime_source = policy_model._runtime_menu_config_source_for_user(user=user)

        self.assertEqual(runtime_source, module.MENU_CONFIG_RUNTIME_SOURCE_CONTRACT)
        self.assertEqual(policies, {})

    def test_runtime_overlay_creates_parent_before_child_move(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        tax_center = _Menu(840, "税务中心", parent=root, sequence=50)
        tax_group = _Menu(527, "开票与税务办理", parent=tax_center, sequence=25)
        prepaid_tax = _Menu(530, "预缴税款", parent=tax_group, sequence=30)
        menus = _MenuModel([root, tax_center, tax_group, prepaid_tax])
        env = _Env(
            {
                "ir.ui.menu": menus,
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {
                    "active": True,
                    "menu_id": 291,
                    "menu_label": "智慧施工管理平台",
                    "visible": True,
                    "sequence_override": 30,
                },
                530: {
                    "active": True,
                    "menu_id": 530,
                    "menu_label": "预缴税款",
                    "visible": True,
                    "target_parent_menu_id": 840,
                    "sequence_override": 110,
                },
                840: {
                    "active": True,
                    "menu_id": 840,
                    "menu_label": "税务中心",
                    "visible": True,
                    "target_parent_menu_id": 291,
                    "sequence_override": 50,
                },
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "sequence": 30,
                        "children": [],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        tax_node = next(child for child in root_node["children"] if child["menu_id"] == 840)
        prepaid_node = next(child for child in tax_node["children"] if child["menu_id"] == 530)
        self.assertEqual(tax_node["name"], "税务中心")
        self.assertEqual(prepaid_node["name"], "预缴税款")
        self.assertEqual(prepaid_node["sequence"], 110)
        self.assertEqual(prepaid_node["parent_id"], 840)
        self.assertEqual(stats["moved_count"], 2)

    def test_runtime_overlay_inserts_config_created_root_child(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        office = _Menu(842, "综合办公", parent=root, sequence=70, action="")
        menus = _MenuModel([root, office], visible_ids=[291])
        env = _Env(
            {
                "ir.ui.menu": menus,
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {
                    "active": True,
                    "menu_id": 291,
                    "menu_label": "智慧施工管理平台",
                    "visible": True,
                    "sequence_override": 30,
                },
                842: {
                    "active": True,
                    "menu_id": 842,
                    "menu_label": "综合办公",
                    "visible": True,
                    "target_parent_menu_id": 291,
                    "sequence_override": 70,
                },
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "sequence": 30,
                        "children": [],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        office_node = next(child for child in root_node["children"] if child["menu_id"] == 842)
        self.assertEqual(office_node["name"], "综合办公")
        self.assertEqual(office_node["parent_id"], 291)
        self.assertEqual(office_node["sequence"], 70)
        self.assertOverlayDirectoryNavigationContract(office_node)
        self.assertEqual(stats["moved_count"], 1)

    def test_runtime_overlay_moves_node_when_real_menu_id_is_in_meta(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=root, sequence=20)
        tender_group = _Menu(299, "投标管理", parent=project_center, sequence=30)
        tender_fee = _Menu(477, "投标报名费申请", parent=tender_group, sequence=40)
        menus = _MenuModel([root, project_center, tender_group, tender_fee])
        env = _Env(
            {
                "ir.ui.menu": menus,
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {
                    "active": True,
                    "menu_id": 291,
                    "menu_label": "智慧施工管理平台",
                    "visible": True,
                    "sequence_override": 30,
                },
                292: {
                    "active": True,
                    "menu_id": 292,
                    "menu_label": "项目中心",
                    "visible": True,
                    "target_parent_menu_id": 291,
                    "sequence_override": 20,
                },
                299: {
                    "active": True,
                    "menu_id": 299,
                    "menu_label": "投标管理",
                    "visible": True,
                    "target_parent_menu_id": 0,
                    "sequence_override": 30,
                },
                477: {
                    "active": True,
                    "menu_id": 477,
                    "menu_label": "投标报名费申请",
                    "visible": True,
                    "target_parent_menu_id": 299,
                    "sequence_override": 40,
                },
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "sequence": 30,
                        "children": [
                            {
                                "menu_id": 292,
                                "name": "项目中心",
                                "sequence": 20,
                                "children": [],
                            },
                            {
                                "menu_id": 900477,
                                "name": "投标报名费申请",
                                "sequence": 5,
                                "meta": {"menu_id": 477},
                                "children": [],
                            },
                        ],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        top_ids = [child["menu_id"] for child in root_node["children"]]
        project_node = next(child for child in root_node["children"] if child["menu_id"] == 292)
        tender_node = next(child for child in project_node["children"] if child["menu_id"] == 299)
        fee_node = next(child for child in tender_node["children"] if child.get("meta", {}).get("menu_id") == 477)
        self.assertNotIn(900477, top_ids)
        self.assertEqual(fee_node["parent_id"], 299)
        self.assertEqual(fee_node["sequence"], 40)
        self.assertEqual(fee_node["meta"]["parent_menu_id"], 299)
        self.assertEqual(stats["moved_count"], 2)

    def test_runtime_overlay_materializes_visible_menu_even_when_odoo_menu_hidden(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        finance = _Menu(306, "财务中心", parent=root, sequence=30)
        payment = _Menu(342, "付款申请明细", parent=finance, sequence=25, action="ir.actions.act_window,624")
        menus = _MenuModel([root, finance, payment], visible_ids=[291, 306])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([_ActionWindow(624, "account.payment.request")]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                306: {"active": True, "menu_id": 306, "menu_label": "财务中心", "visible": True},
                342: {"active": True, "menu_id": 342, "menu_label": "付款申请明细", "visible": True, "sequence_override": 25},
            },
            "ui.menu.config.policy",
        )

        overlaid, _stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [{"menu_id": 306, "name": "财务中心", "children": []}],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        finance_node = next(child for child in root_node["children"] if child["menu_id"] == 306)
        payment_node = next(child for child in finance_node["children"] if child["menu_id"] == 342)
        self.assertEqual(payment_node["name"], "付款申请明细")
        self.assertEqual(payment_node["sequence"], 25)

    def test_runtime_overlay_materializes_missing_parent_and_child_once(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        finance = _Menu(306, "财务中心", parent=root, sequence=30)
        deposit_group = _Menu(570, "保证金管理", parent=finance, sequence=60)
        deposit_payment = _Menu(615, "付款还保证金", parent=deposit_group, sequence=80, action="ir.actions.act_window,814")
        menus = _MenuModel([root, finance, deposit_group, deposit_payment])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([_ActionWindow(814, "sc.deposit.payment")]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                306: {"active": True, "menu_id": 306, "menu_label": "财务中心", "visible": True},
                570: {"active": True, "menu_id": 570, "menu_label": "保证金管理", "visible": True, "sequence_override": 60},
                615: {"active": True, "menu_id": 615, "menu_label": "付款还保证金", "visible": True, "sequence_override": 30},
            },
            "ui.menu.config.policy",
        )

        overlaid, _stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [{"menu_id": 306, "name": "财务中心", "children": []}],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        seen = []

        def walk(nodes):
            for node in nodes:
                seen.append(node["menu_id"])
                walk(node.get("children") or [])

        walk(overlaid["tree"])
        root_node = overlaid["tree"][0]
        finance_node = next(child for child in root_node["children"] if child["menu_id"] == 306)
        deposit_node = next(child for child in finance_node["children"] if child["menu_id"] == 570)
        payment_node = next(child for child in deposit_node["children"] if child["menu_id"] == 615)
        self.assertEqual(seen.count(615), 1)
        self.assertEqual(payment_node["sequence"], 30)
        self.assertEqual(payment_node["meta"]["parent_menu_id"], 570)

    def test_runtime_overlay_reparents_existing_orphan_to_configured_parent(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        finance = _Menu(306, "财务中心", parent=root, sequence=30)
        deposit_group = _Menu(570, "保证金管理", parent=finance, sequence=60)
        deposit_collect = _Menu(612, "保证金收取", parent=deposit_group, sequence=70, action="ir.actions.act_window,812")
        menus = _MenuModel([root, finance, deposit_group, deposit_collect])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([_ActionWindow(812, "sc.deposit.collect")]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                306: {"active": True, "menu_id": 306, "menu_label": "财务中心", "visible": True},
                570: {"active": True, "menu_id": 570, "menu_label": "保证金管理", "visible": True, "sequence_override": 60},
                612: {"active": True, "menu_id": 612, "menu_label": "保证金收取", "visible": True, "sequence_override": 70},
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [{"menu_id": 306, "name": "财务中心", "children": []}],
                    },
                    {"menu_id": 612, "name": "保证金收取", "children": []},
                ],
                "flat": [],
            },
            user=user,
        )

        top_level_ids = [node["menu_id"] for node in overlaid["tree"]]
        root_node = next(node for node in overlaid["tree"] if node["menu_id"] == 291)
        finance_node = next(child for child in root_node["children"] if child["menu_id"] == 306)
        deposit_node = next(child for child in finance_node["children"] if child["menu_id"] == 570)
        collect_node = next(child for child in deposit_node["children"] if child["menu_id"] == 612)
        self.assertNotIn(612, top_level_ids)
        self.assertEqual(collect_node["meta"]["parent_menu_id"], 570)
        self.assertGreaterEqual(stats["parent_aligned_count"], 1)

    def test_runtime_overlay_attaches_visible_child_to_nearest_visible_parent_when_parent_hidden(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        contract = _Menu(293, "合同中心", parent=root, sequence=40)
        expense_group = _Menu(488, "支出合同台账", parent=contract, sequence=20)
        material_contract = _Menu(602, "材料合同", parent=expense_group, sequence=11, action="ir.actions.act_window,799")
        menus = _MenuModel([root, contract, expense_group, material_contract])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([_ActionWindow(799, "sc.material.contract")]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                293: {"active": True, "menu_id": 293, "menu_label": "合同中心", "visible": True},
                488: {"active": True, "menu_id": 488, "menu_label": "支出合同台账", "visible": False},
                602: {"active": True, "menu_id": 602, "menu_label": "材料合同", "visible": True, "sequence_override": 11},
            },
            "ui.menu.config.policy",
        )

        overlaid, _stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [{"menu_id": 293, "name": "合同中心", "children": []}],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        contract_node = next(child for child in root_node["children"] if child["menu_id"] == 293)
        child_ids = [child["menu_id"] for child in contract_node["children"]]
        material_node = next(child for child in contract_node["children"] if child["menu_id"] == 602)
        self.assertIn(602, child_ids)
        self.assertNotIn(488, child_ids)
        self.assertEqual(material_node["name"], "材料合同")
        self.assertEqual(material_node["meta"]["parent_menu_id"], 293)

    def test_runtime_overlay_does_not_treat_same_label_different_menu_as_present(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        contract = _Menu(293, "合同中心", parent=root, sequence=40)
        old_fact = _Menu(425, "历史采购/一般合同事实", parent=contract, sequence=90, action="ir.actions.act_window,714")
        new_fact = _Menu(601, "历史采购/一般合同事实", parent=contract, sequence=60, action="ir.actions.act_window,798")
        menus = _MenuModel([root, contract, old_fact, new_fact])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([
                    _ActionWindow(714, "sc.legacy.purchase.contract.fact"),
                    _ActionWindow(798, "sc.general.contract.fact"),
                ]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                293: {"active": True, "menu_id": 293, "menu_label": "合同中心", "visible": True},
                425: {"active": True, "menu_id": 425, "menu_label": "历史采购/一般合同事实", "visible": True, "sequence_override": 90},
                601: {"active": True, "menu_id": 601, "menu_label": "历史采购/一般合同事实", "visible": True, "sequence_override": 60},
            },
            "ui.menu.config.policy",
        )

        overlaid, _stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [
                            {
                                "menu_id": 293,
                                "name": "合同中心",
                                "children": [
                                    {
                                        "menu_id": 425,
                                        "name": "历史采购/一般合同事实",
                                        "meta": {"menu_id": 425, "parent_menu_id": 293},
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        contract_node = next(child for child in root_node["children"] if child["menu_id"] == 293)
        child_ids = [child["menu_id"] for child in contract_node["children"]]
        self.assertIn(425, child_ids)
        self.assertIn(601, child_ids)
        self.assertEqual(child_ids.count(601), 1)

    def test_runtime_overlay_config_only_removes_unconfigured_system_menu_root(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        home = _Menu(464, "首页", parent=root, sequence=10)
        menus = _MenuModel([root, home])
        env = _Env(
            {
                "ir.ui.menu": menus,
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                464: {"active": True, "menu_id": 464, "menu_label": "首页", "visible": True, "sequence_override": 10},
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 880204900,
                        "name": "系统菜单",
                        "children": [
                            {
                                "menu_id": 880204901,
                                "name": "菜单配置",
                                "model": "ui.menu.config.policy",
                                "meta": {"delivery_bucket": "delivery_business_config"},
                                "children": [],
                            }
                        ],
                    },
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [{"menu_id": 464, "name": "首页", "children": []}],
                    },
                ],
                "flat": [],
            },
            user=user,
        )

        self.assertEqual([node["menu_id"] for node in overlaid["tree"]], [291])
        self.assertEqual([child["menu_id"] for child in overlaid["tree"][0]["children"]], [464])
        self.assertEqual(stats["protected_count"], 0)

    def test_runtime_overlay_config_only_keeps_hidden_config_recovery_entries(self):
        module = _load_policy_model()
        module.call_extension_hook_first = _lowcode_system_config_menu_xmlids_hook
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        home = _Menu(464, "首页", parent=root, sequence=10)
        settings = _Menu(297, "配置中心", parent=root, sequence=70)
        workbench = _Menu(827, "配置工作台", parent=settings, sequence=10, action="ir.actions.act_window(1009,)")
        menu_config = _Menu(646, "菜单配置", parent=settings, sequence=20, action="ir.actions.act_window(1014,)")
        menus = _MenuModel([root, home, settings, workbench, menu_config], visible_ids=[291, 464, 297, 827, 646])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([
                    _ActionWindow(1009, res_model="sc.business.config.workbench"),
                    _ActionWindow(1014, res_model="ui.menu.config.policy"),
                ]),
                "ir.model.data": _ModelDataModel([
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=297,
                        module="smart_construction_core",
                        name="menu_sc_business_config_center",
                    ),
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=827,
                        module="smart_construction_core",
                        name="menu_sc_business_config_workbench",
                    ),
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=646,
                        module="smart_construction_core",
                        name="menu_ui_menu_config_policy_business_config",
                    ),
                ]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                464: {"active": True, "menu_id": 464, "menu_label": "首页", "visible": True, "sequence_override": 10},
                297: {
                    "active": True,
                    "menu_id": 297,
                    "menu_label": "基础设置",
                    "visible": False,
                    "custom_label": "系统设置",
                    "sequence_override": 70,
                },
                827: {
                    "active": True,
                    "menu_id": 827,
                    "menu_label": "配置中心",
                    "visible": False,
                    "sequence_override": 10,
                },
                646: {
                    "active": True,
                    "menu_id": 646,
                    "menu_label": "菜单配置",
                    "visible": False,
                    "sequence_override": 20,
                },
            },
            "ui.business.config.contract.menu_orchestration",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [{"menu_id": 464, "name": "首页", "children": []}],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        settings_node = next(child for child in root_node["children"] if child["menu_id"] == 297)
        self.assertEqual(settings_node["name"], "配置中心")
        self.assertEqual([child["menu_id"] for child in settings_node["children"]], [827, 646])
        self.assertOverlayDirectoryNavigationContract(settings_node)
        workbench_node = next(child for child in settings_node["children"] if child["menu_id"] == 827)
        menu_config_node = next(child for child in settings_node["children"] if child["menu_id"] == 646)
        self.assertOverlayActionNavigationContract(
            workbench_node,
            action_id=1009,
            model="sc.business.config.workbench",
        )
        self.assertOverlayActionNavigationContract(
            menu_config_node,
            action_id=1014,
            model="ui.menu.config.policy",
        )
        self.assertEqual(stats["hidden_count"], 0)
        self.assertTrue(stats["config_only"])

    def test_runtime_overlay_config_recovery_entries_do_not_bypass_menu_acl(self):
        module = _load_policy_model()
        module.call_extension_hook_first = _lowcode_system_config_menu_xmlids_hook
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        settings = _Menu(297, "系统设置", parent=root, sequence=70)
        menu_config = _Menu(646, "菜单配置", parent=settings, sequence=20, action="ir.actions.act_window(1014,)")
        menus = _MenuModel([root, settings, menu_config], visible_ids=[291])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([
                    _ActionWindow(1014, res_model="ui.menu.config.policy"),
                ]),
                "ir.model.data": _ModelDataModel([
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=297,
                        module="smart_construction_core",
                        name="menu_sc_business_config_center",
                    ),
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=646,
                        module="smart_construction_core",
                        name="menu_ui_menu_config_policy_business_config",
                    ),
                ]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                297: {"active": True, "menu_id": 297, "menu_label": "系统设置", "visible": False},
                646: {"active": True, "menu_id": 646, "menu_label": "菜单配置", "visible": False},
            },
            "ui.business.config.contract.menu_orchestration",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [{"menu_id": 291, "name": "智慧施工管理平台", "children": []}],
                "flat": [],
            },
            user=user,
        )

        self.assertEqual(len(overlaid["tree"]), 1)
        self.assertEqual(overlaid["tree"][0]["menu_id"], 291)
        self.assertEqual(overlaid["tree"][0]["name"], "智慧施工管理平台")
        self.assertEqual(overlaid["tree"][0]["children"], [])
        self.assertTrue(overlaid["tree"][0]["configurable"])
        self.assertEqual(overlaid["tree"][0]["config_menu_id"], 291)
        self.assertEqual(overlaid["tree"][0]["config_ref"], {"model": "ir.ui.menu", "id": 291})
        self.assertEqual(stats["hidden_count"], 0)

    def test_runtime_overlay_protected_workbench_ignores_confusing_custom_label(self):
        module = _load_policy_model()
        module.call_extension_hook_first = _lowcode_config_boundary_hooks
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        settings = _Menu(297, "配置中心", parent=root, sequence=70)
        workbench = _Menu(827, "配置工作台", parent=settings, sequence=10, action="ir.actions.act_window(1009,)")
        menu_config = _Menu(646, "菜单配置", parent=settings, sequence=20, action="ir.actions.act_window(1014,)")
        menus = _MenuModel([root, settings, workbench, menu_config], visible_ids=[291, 297, 827, 646])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([
                    _ActionWindow(1009, res_model="ui.business.config.contract"),
                    _ActionWindow(1014, res_model="ui.menu.config.policy"),
                ]),
                "ir.model.data": _ModelDataModel([
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=297,
                        module="smart_construction_core",
                        name="menu_sc_business_config_center",
                    ),
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=827,
                        module="smart_construction_core",
                        name="menu_sc_business_config_workbench",
                    ),
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=646,
                        module="smart_construction_core",
                        name="menu_ui_menu_config_policy_business_config",
                    ),
                ]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                297: {"active": True, "menu_id": 297, "menu_label": "配置中心", "visible": True},
                827: {
                    "active": True,
                    "menu_id": 827,
                    "menu_label": "配置工作台",
                    "visible": True,
                    "custom_label": "配置中心",
                },
                646: {"active": True, "menu_id": 646, "menu_label": "菜单配置", "visible": True},
            },
            "ui.business.config.contract.menu_orchestration",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [
                            {
                                "menu_id": 297,
                                "name": "配置中心",
                                "sequence": 70,
                                "children": [
                                    {"menu_id": 827, "name": "配置工作台", "sequence": 10, "children": []},
                                    {"menu_id": 646, "name": "菜单配置", "sequence": 20, "children": []},
                                ],
                            }
                        ],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        settings_node = overlaid["tree"][0]["children"][0]
        self.assertEqual([child["menu_id"] for child in settings_node["children"]], [827, 646])
        workbench_node = settings_node["children"][0]
        self.assertEqual(workbench_node["name"], "配置工作台")
        self.assertNotEqual(workbench_node.get("name"), settings_node.get("name"))
        self.assertEqual(stats["hidden_count"], 0)

    def test_runtime_overlay_config_only_does_not_recover_hidden_acceptance_entries(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        home = _Menu(464, "首页", parent=root, sequence=10)
        acceptance_root = _Menu(650, "用户核对菜单", parent=root, sequence=100)
        acceptance_child = _Menu(
            655,
            "施工合同",
            parent=acceptance_root,
            sequence=30,
            action="ir.actions.act_window(909,)",
        )
        menus = _MenuModel([root, home, acceptance_root, acceptance_child], visible_ids=[291, 464, 650, 655])
        env = _Env(
            {
                "ir.ui.menu": menus,
                "ir.actions.act_window": _ActionWindowModel([
                    _ActionWindow(909, res_model="sc.legacy.direct.acceptance.fact", view_mode="tree"),
                ]),
                "ir.model.data": _ModelDataModel([
                    types.SimpleNamespace(
                        model="ir.ui.menu",
                        res_id=650,
                        module="smart_construction_core",
                        name="menu_scbs55_user_acceptance_root",
                    ),
                ]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                464: {"active": True, "menu_id": 464, "menu_label": "首页", "visible": True},
                650: {"active": True, "menu_id": 650, "menu_label": "用户核对菜单", "visible": False},
                655: {"active": True, "menu_id": 655, "menu_label": "施工合同", "visible": False},
            },
            "ui.business.config.contract.menu_orchestration",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [
                            {"menu_id": 464, "name": "首页", "children": []},
                            {
                                "menu_id": 650,
                                "name": "用户核对菜单",
                                "children": [{"menu_id": 655, "name": "施工合同", "children": []}],
                            },
                        ],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        child_ids = [child["menu_id"] for child in root_node["children"]]
        self.assertEqual(child_ids, [464])
        self.assertNotIn(650, child_ids)
        self.assertGreaterEqual(stats["hidden_count"], 1)

    def test_runtime_overlay_config_only_with_no_policies_blocks_system_fallback(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        env = _Env(
            {
                "ir.ui.menu": _MenuModel([]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: ({}, "ui.menu.config.policy")

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "children": [
                            {"menu_id": 464, "name": "首页", "children": []},
                            {"menu_id": 900, "name": "系统菜单", "children": []},
                        ],
                    }
                ],
                "flat": [
                    {"menu_id": 291, "name": "智慧施工管理平台"},
                    {"menu_id": 464, "name": "首页"},
                    {"menu_id": 900, "name": "系统菜单"},
                ],
            },
            user=user,
        )

        self.assertEqual(overlaid["tree"], [])
        self.assertEqual(overlaid["flat"], [])
        self.assertTrue(stats["config_only"])
        self.assertEqual(stats["unconfigured_hidden_count"], 3)

    def test_runtime_overlay_config_only_does_not_match_unconfigured_node_by_label(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        business_customer = _Menu(500, "客户", parent=root, sequence=10)
        menus = _MenuModel([root, business_customer])
        env = _Env(
            {
                "ir.ui.menu": menus,
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {"active": True, "menu_id": 291, "menu_label": "智慧施工管理平台", "visible": True},
                500: {"active": True, "menu_id": 500, "menu_label": "客户", "visible": True},
            },
            "ui.business.config.contract.menu_orchestration",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {"menu_id": 145, "name": "客户", "children": [{"menu_id": 151, "name": "客户", "children": []}]},
                    {"menu_id": 291, "name": "智慧施工管理平台", "children": []},
                ],
                "flat": [
                    {"menu_id": 145, "name": "客户"},
                    {"menu_id": 151, "name": "客户"},
                    {"menu_id": 291, "name": "智慧施工管理平台"},
                ],
            },
            user=user,
        )

        def collect_ids(nodes):
            out = []
            for node in nodes:
                out.append(node["menu_id"])
                out.extend(collect_ids(node.get("children") or []))
            return out

        runtime_ids = collect_ids(overlaid["tree"])
        self.assertIn(500, runtime_ids)
        self.assertNotIn(145, runtime_ids)
        self.assertNotIn(151, runtime_ids)
        self.assertTrue(stats["config_only"])

    def test_runtime_overlay_builds_children_for_missing_moved_group(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        root = _Menu(291, "智慧施工管理平台")
        project_center = _Menu(292, "项目中心", parent=root, sequence=20)
        material_center = _Menu(295, "物资与分包", parent=root, sequence=45)
        labor_group = _Menu(301, "劳务管理", parent=material_center, sequence=20)
        labor_plan = _Menu(500, "劳务计划", parent=labor_group, sequence=10)
        labor_request = _Menu(501, "劳务申请", parent=labor_group, sequence=20)
        labor_check = _Menu(822, "劳务结算候选核对", parent=labor_group, sequence=39)
        menus = _MenuModel([root, project_center, material_center, labor_group, labor_plan, labor_request, labor_check])
        env = _Env(
            {
                "ir.ui.menu": menus,
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                291: {
                    "active": True,
                    "menu_id": 291,
                    "menu_label": "智慧施工管理平台",
                    "visible": True,
                    "sequence_override": 30,
                },
                292: {
                    "active": True,
                    "menu_id": 292,
                    "menu_label": "项目中心",
                    "visible": True,
                    "target_parent_menu_id": 291,
                    "sequence_override": 20,
                },
                301: {
                    "active": True,
                    "menu_id": 301,
                    "menu_label": "劳务管理",
                    "visible": True,
                    "target_parent_menu_id": 292,
                    "sequence_override": 60,
                },
                500: {
                    "active": True,
                    "menu_id": 500,
                    "menu_label": "劳务计划",
                    "visible": True,
                    "sequence_override": 10,
                },
                501: {
                    "active": True,
                    "menu_id": 501,
                    "menu_label": "劳务申请",
                    "visible": False,
                    "sequence_override": 20,
                },
                822: {
                    "active": True,
                    "menu_id": 822,
                    "menu_label": "劳务结算候选核对",
                    "visible": True,
                    "sequence_override": 39,
                },
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "sequence": 30,
                        "children": [
                            {
                                "menu_id": 292,
                                "name": "项目中心",
                                "sequence": 20,
                                "children": [],
                            }
                        ],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        root_node = overlaid["tree"][0]
        project_node = next(child for child in root_node["children"] if child["menu_id"] == 292)
        labor_node = next(child for child in project_node["children"] if child["menu_id"] == 301)
        child_ids = [child["menu_id"] for child in labor_node["children"]]
        self.assertEqual(labor_node["sequence"], 60)
        self.assertEqual(labor_node["parent_id"], 292)
        self.assertIn(500, child_ids)
        self.assertIn(822, child_ids)
        self.assertNotIn(501, child_ids)
        self.assertEqual(stats["moved_count"], 2)

    def test_runtime_overlay_config_only_hides_unconfigured_leaf(self):
        module = _load_policy_model()
        company = types.SimpleNamespace(id=7)
        user = _User([])
        configured_menu = _Menu(11, "合同办理")
        hidden_menu = _Menu(12, "未配置办理")
        env = _Env(
            {
                "ir.ui.menu": _MenuModel([configured_menu, hidden_menu]),
            },
            company=company,
            user=user,
        )
        policy_model = object.__new__(module.UiMenuConfigPolicy)
        policy_model.env = env
        policy_model._runtime_menu_config_source_for_user = lambda user=None: (
            {
                11: {
                    "active": True,
                    "menu_id": 11,
                    "menu_label": "合同办理",
                    "visible": True,
                    "sequence_override": 10,
                },
            },
            "ui.menu.config.policy",
        )

        overlaid, stats = policy_model.apply_runtime_overlay(
            {
                "tree": [
                    {
                        "menu_id": 291,
                        "name": "智慧施工管理平台",
                        "sequence": 30,
                        "children": [
                            {"menu_id": 11, "name": "合同办理", "sequence": 10, "children": []},
                            {"menu_id": 12, "name": "未配置办理", "sequence": 20, "children": []},
                        ],
                    }
                ],
                "flat": [],
            },
            user=user,
        )

        self.assertEqual([node["menu_id"] for node in overlaid["tree"]], [11])
        self.assertEqual(stats["unconfigured_hidden_count"], 2)

    def test_runtime_navigation_state_marks_hidden_parent_with_visible_child_as_carrier(self):
        module = _load_handler()

        runtime = module._build_runtime_navigation_states(
            [
                {
                    "menu_id": 291,
                    "name": "智慧施工管理平台",
                    "children": [
                        {
                            "menu_id": 295,
                            "name": "物资与分包",
                            "children": [
                                {"menu_id": 500, "name": "材料合同", "children": []},
                            ],
                        }
                    ],
                }
            ],
            {
                295: {"visible": False},
                500: {"visible": True},
            },
        )

        material_state = runtime["states"]["295"]
        self.assertTrue(material_state["runtime_visible"])
        self.assertFalse(material_state["configured_visible"])
        self.assertEqual(material_state["runtime_state"], "visible_carrier")
        self.assertEqual(material_state["runtime_visibility_reason"], "visible_descendant_carrier")
        self.assertIn(295, runtime["carrier_menu_ids"])

    def test_runtime_navigation_state_marks_configured_visible_absent_menu_explicitly(self):
        module = _load_handler()

        runtime = module._build_runtime_navigation_states(
            [
                {
                    "menu_id": 291,
                    "name": "智慧施工管理平台",
                    "children": [
                        {"menu_id": 361, "name": "一般合同", "children": []},
                    ],
                }
            ],
            {
                293: {"visible": True},
                361: {"visible": True},
            },
        )

        contract_center_state = runtime["states"]["293"]
        self.assertFalse(contract_center_state["runtime_visible"])
        self.assertTrue(contract_center_state["configured_visible"])
        self.assertEqual(contract_center_state["runtime_state"], "configured_visible_runtime_absent")
        self.assertEqual(contract_center_state["runtime_visibility_reason"], "configured_visible_runtime_absent")

    def test_runtime_navigation_state_maps_release_group_config_ref_to_configured_menu(self):
        module = _load_handler()

        runtime = module._build_runtime_navigation_states(
            [
                {
                    "menu_id": 880000001,
                    "name": "系统菜单",
                    "children": [
                        {
                            "menu_id": 889777446,
                            "label": "合同中心",
                            "config_menu_id": 293,
                            "config_ref": {"model": "ir.ui.menu", "id": 293},
                            "children": [
                                {"menu_id": 361, "label": "一般合同", "children": []},
                            ],
                        },
                    ],
                }
            ],
            {
                293: {"visible": True},
                361: {"visible": True},
            },
        )

        contract_center_state = runtime["states"]["293"]
        self.assertTrue(contract_center_state["runtime_visible"])
        self.assertTrue(contract_center_state["configured_visible"])
        self.assertEqual(contract_center_state["runtime_node_id"], 889777446)
        self.assertEqual(contract_center_state["runtime_state"], "visible_release_navigation_group")
        self.assertEqual(contract_center_state["runtime_visibility_reason"], "visible_release_navigation_group")

    def test_runtime_navigation_state_does_not_map_release_group_by_label(self):
        module = _load_handler()

        runtime = module._build_runtime_navigation_states(
            [
                {
                    "menu_id": 880000001,
                    "name": "系统菜单",
                    "children": [
                        {
                            "menu_id": 889777446,
                            "label": "合同中心",
                            "children": [
                                {"menu_id": 361, "label": "一般合同", "children": []},
                            ],
                        },
                    ],
                }
            ],
            {
                293: {"visible": True},
                361: {"visible": True},
            },
        )

        contract_center_state = runtime["states"]["293"]
        self.assertFalse(contract_center_state["runtime_visible"])
        self.assertEqual(contract_center_state["runtime_state"], "configured_visible_runtime_absent")


if __name__ == "__main__":
    unittest.main()

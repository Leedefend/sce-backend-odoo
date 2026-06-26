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

    def exists(self):
        return self


class _MenuModel(_RecordSet):
    def sudo(self):
        return self

    def with_context(self, **kwargs):
        self.context = kwargs
        return self

    def browse(self, record_id):
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
        self.append(menu)
        return menu


class _ModelDataModel(_RecordSet):
    def sudo(self):
        return self

    def search(self, domain):
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
        self.scope_summary = "、".join(group.display_name for group in self.role_group_ids) or "当前公司所有用户"
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
        active_required = any(field == "active" and op == "=" and value is True for field, op, value in domain)
        rows = [
            policy
            for policy in self
            if int(policy.company_id.id or 0) == int(company_id or 0)
            and policy.menu_id
            and (not menu_id or int(policy.menu_id.id or 0) == int(menu_id or 0))
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


class TestMenuConfigurationAudit(unittest.TestCase):
    def setUp(self):
        self.module = _load_handler()

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

        applicable_ids = [row["id"] for row in result["data"]["applicable_policies"]]
        self.assertEqual(applicable_ids, [1, 2])
        self.assertEqual(result["meta"]["source_authority"]["kind"], "ui_menu_config_audit")

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
        self.assertEqual(policies[0].sequence_override, 30)
        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts[0].contract_json["menu_orchestration"]["policy_count"], 1)
        self.assertEqual(contracts[0].contract_json["menu_orchestration"]["source"], "smart_core.lowcode.menu_config")
        self.assertEqual(result["meta"]["source_authority"]["kind"], "ui_menu_config_menu_create_write_proxy")
        self.assertEqual(result["meta"]["source_authority"]["lowcode_boundary"], "menu_config")

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

    def test_menu_config_versions_bootstraps_contract_from_existing_policies(self):
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
                301: {
                    "active": True,
                    "menu_id": 301,
                    "menu_label": "劳务管理",
                    "visible": True,
                    "target_parent_menu_id": 292,
                    "sequence_override": 60,
                },
                501: {
                    "active": True,
                    "menu_id": 501,
                    "menu_label": "劳务申请",
                    "visible": False,
                    "sequence_override": 20,
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
        self.assertEqual(stats["moved_count"], 1)


if __name__ == "__main__":
    unittest.main()

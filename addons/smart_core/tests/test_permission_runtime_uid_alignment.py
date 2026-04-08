# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "smart_core", "permission_runtime")
class TestPermissionRuntimeUidAlignment(TransactionCase):
    def test_permission_contract_runtime_uid_overrides_sudo_uid(self):
        probe_group = self.env["res.groups"].sudo().create({"name": "Runtime UID Probe Group"})
        probe_user = self.env["res.users"].sudo().create(
            {
                "name": "runtime uid probe",
                "login": "runtime_uid_probe_user",
                "email": "runtime_uid_probe_user@example.com",
                "groups_id": [(6, 0, [probe_group.id])],
            }
        )

        cfg = self.env["app.permission.config"].sudo().create(
            {
                "target_type": "model",
                "target_ref": "x_runtime_uid_probe_model",
                "permission_def": {
                    "model": "x_runtime_uid_probe_model",
                    "perms_by_group": {
                        "__all__": {"read": False, "write": False, "create": False, "unlink": False},
                        f"id:{probe_group.id}": {"read": True, "write": True, "create": True, "unlink": False},
                    },
                    "field_groups": {},
                    "rules": {
                        "read": {"mode": "OR", "clauses": []},
                        "write": {"mode": "OR", "clauses": []},
                        "create": {"mode": "OR", "clauses": []},
                        "unlink": {"mode": "OR", "clauses": []},
                    },
                    "order_default": "id desc",
                    "domain_default": [],
                },
            }
        )

        sudo_effective = cfg.sudo().get_permission_contract(filter_runtime=True).get("effective") or {}
        sudo_rights = sudo_effective.get("rights") or {}
        self.assertFalse(bool(sudo_rights.get("create")))

        runtime_effective = (
            cfg.sudo().with_context(runtime_uid=probe_user.id).get_permission_contract(filter_runtime=True).get("effective")
            or {}
        )
        runtime_rights = runtime_effective.get("rights") or {}

        self.assertTrue(bool(runtime_rights.get("read")))
        self.assertTrue(bool(runtime_rights.get("write")))
        self.assertTrue(bool(runtime_rights.get("create")))
        self.assertFalse(bool(runtime_rights.get("unlink")))


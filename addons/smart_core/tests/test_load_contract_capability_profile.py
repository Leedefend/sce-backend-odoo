# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from ..handlers.load_contract import LoadContractHandler


@tagged("post_install", "-at_install", "smart_core", "load_contract_capability_profile")
class TestLoadContractCapabilityProfile(TransactionCase):
    def _make_handler(self):
        return LoadContractHandler.__new__(LoadContractHandler)

    def test_tree_searchpanel_recommends_native_fallback(self):
        handler = self._make_handler()
        data = {
            "views": {
                "tree": {
                    "columns": ["name", "state"],
                    "capabilities": {"inline_edit": False},
                }
            },
            "search": {
                "filters": [{"name": "mine", "string": "My"}],
                "search_panel": {"enabled": True, "sections": [{"key": "state"}]},
            },
            "fields": {"name": {"type": "char"}, "state": {"type": "selection"}},
            "head": {"model": "project.task", "view_type": "tree"},
            "permissions": {"read": True, "write": True, "create": True, "unlink": False},
        }

        handler._inject_semantic_contract(data)

        capability_profile = ((data.get("semantic_page") or {}).get("capability_profile") or {})
        list_semantics = ((data.get("semantic_page") or {}).get("list_semantics") or {})
        render_policy = capability_profile.get("render_policy") or {}
        primary = (capability_profile.get("view_profiles") or {}).get("tree") or {}

        self.assertEqual(capability_profile.get("primary_view_type"), "tree")
        self.assertEqual(render_policy.get("recommended_runtime"), "native")
        self.assertEqual((render_policy.get("fallback_action") or {}).get("key"), "open_native")
        self.assertIn("searchpanel_full_ecosystem", primary.get("unsupported_features") or [])
        self.assertEqual(list_semantics.get("page_size"), 50)
        self.assertTrue(list_semantics.get("supports_export_current_result"))

    def test_form_inline_subview_recommends_native_fallback(self):
        handler = self._make_handler()
        data = {
            "views": {
                "form": {
                    "layout": [{"type": "group", "children": []}],
                    "subviews": {
                        "line_ids": {
                            "policies": {"inline_edit": True},
                            "tree": {"columns": ["name", "amount"]},
                        }
                    },
                }
            },
            "fields": {
                "name": {"type": "char"},
                "line_ids": {"type": "one2many", "relation": "x.line"},
            },
            "head": {"model": "x.form", "view_type": "form"},
            "permissions": {"read": True, "write": True, "create": True, "unlink": False},
        }

        handler._inject_semantic_contract(data)

        capability_profile = ((data.get("semantic_page") or {}).get("capability_profile") or {})
        form_semantics = ((data.get("semantic_page") or {}).get("form_semantics") or {})
        render_policy = capability_profile.get("render_policy") or {}
        primary = (capability_profile.get("view_profiles") or {}).get("form") or {}

        self.assertEqual(render_policy.get("recommended_runtime"), "native")
        self.assertIn("complex_one2many_inline_edit", primary.get("unsupported_features") or [])
        self.assertIn("FORM_INLINE_SUBVIEW_NATIVE_FALLBACK", primary.get("reason_codes") or [])
        relations = form_semantics.get("relation_fields") or []
        self.assertEqual(relations[0].get("takeover_hint"), "native")
        self.assertIn("line_ids", form_semantics.get("field_behavior_map") or {})

    def test_kanban_keeps_lightweight_frontend_profile(self):
        handler = self._make_handler()
        data = {
            "views": {
                "kanban": {
                    "fields": ["name", "stage_id", "amount_total"],
                    "quick_actions": [{"name": "action_open"}],
                    "stages_field": "stage_id",
                }
            },
            "fields": {
                "name": {"type": "char"},
                "stage_id": {"type": "many2one"},
                "amount_total": {"type": "monetary"},
            },
            "head": {"model": "project.project", "view_type": "kanban"},
            "permissions": {"read": True, "write": True, "create": True, "unlink": False},
        }

        handler._inject_semantic_contract(data)

        capability_profile = ((data.get("semantic_page") or {}).get("capability_profile") or {})
        kanban_semantics = ((data.get("semantic_page") or {}).get("kanban_semantics") or {})
        render_policy = capability_profile.get("render_policy") or {}
        primary = (capability_profile.get("view_profiles") or {}).get("kanban") or {}

        self.assertEqual(render_policy.get("recommended_runtime"), "frontend")
        self.assertEqual(primary.get("support_tier"), "lightweight")
        self.assertIn("drag_drop", primary.get("unsupported_features") or [])
        self.assertEqual(kanban_semantics.get("group_by_field"), "stage_id")
        self.assertEqual(kanban_semantics.get("support_tier"), "lightweight")

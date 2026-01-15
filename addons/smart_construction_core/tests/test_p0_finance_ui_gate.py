# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate")
class TestP0FinanceUiGate(TransactionCase):
    """P0 gate for finance form buttons (payment.request, settlement.order)."""

    def _get_form_arch(self, model):
        model_env = self.env[model]
        if hasattr(model_env, "get_view"):
            view_def = model_env.get_view(view_type="form")
        else:
            view_def = model_env.fields_view_get(view_type="form", toolbar=False)
        arch = view_def.get("arch") or view_def.get("arch_db")
        self.assertTrue(arch, f"missing form arch for model={model}")
        return arch

    def _iter_buttons(self, arch):
        root = etree.fromstring(arch.encode("utf-8"))
        return root.xpath(".//button")

    def _is_high_risk_button(self, btn):
        btn_type = (btn.get("type") or "").strip()
        name = (btn.get("name") or "").strip()
        if btn_type in ("object", "action"):
            return True
        if name.startswith("%(") and name.endswith(")d"):
            return True
        return False

    def _assert_buttons_have_groups(self, model, ignore_names=None):
        ignore_names = set(ignore_names or [])
        offenders = []

        for btn in self._iter_buttons(self._get_form_arch(model)):
            if not self._is_high_risk_button(btn):
                continue
            name = (btn.get("name") or "").strip()
            if name in ignore_names:
                continue
            groups = (btn.get("groups") or "").strip()
            if groups:
                continue
            offenders.append(
                {
                    "model": model,
                    "name": name,
                    "string": (btn.get("string") or "").strip(),
                    "type": (btn.get("type") or "").strip(),
                }
            )

        self.assertFalse(
            offenders,
            "Finance form has high-risk buttons without groups:\n"
            + "\n".join([str(x) for x in offenders]),
        )

    def test_ui_buttons_groups_payment_request(self):
        self._assert_buttons_have_groups("payment.request")

    def test_ui_buttons_groups_settlement_order(self):
        self._assert_buttons_have_groups("sc.settlement.order")

# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "smart_core", "native_action_selection")
class TestNativeActionSelectionAlignment(TransactionCase):
    def test_parser_form_header_object_button_uses_record_context(self):
        parser = self.env["app.view.parser"]
        root = etree.fromstring(
            b"""
            <form string="Demo">
              <header>
                <button name="action_confirm" type="object" string="Confirm"/>
              </header>
            </form>
            """
        )
        btn = root.xpath(".//header//button")[0]

        row = parser._button_to_action(btn, level="header")

        self.assertEqual(row.get("level"), "header")
        self.assertEqual(row.get("selection"), "none")
        self.assertEqual(row.get("visible_profiles"), ["create", "edit", "readonly"])

    def test_parser_tree_row_object_button_is_not_selection_action(self):
        parser = self.env["app.view.parser"]
        root = etree.fromstring(
            b"""
            <tree string="Demo">
              <field name="name"/>
              <button name="action_open" type="object" string="Open"/>
            </tree>
            """
        )
        btn = root.xpath(".//button")[0]

        row = parser._button_to_action(btn, level="row")

        self.assertEqual(row.get("level"), "row")
        self.assertEqual(row.get("selection"), "none")
        self.assertEqual(row.get("visible_profiles"), ["readonly", "list"])

    def test_parser_tree_header_object_button_uses_multi_selection(self):
        parser = self.env["app.view.parser"]
        root = etree.fromstring(
            b"""
            <tree string="Demo">
              <header>
                <button name="action_batch" type="object" string="Batch"/>
              </header>
              <field name="name"/>
            </tree>
            """
        )
        btn = root.xpath(".//header//button")[0]

        row = parser._button_to_action(btn, level="row")

        self.assertEqual(row.get("level"), "toolbar")
        self.assertEqual(row.get("selection"), "multi")
        self.assertEqual(row.get("visible_profiles"), ["readonly", "list"])

    def test_app_action_config_server_action_scope_respects_binding_view_types(self):
        config = self.env["app.action.config"]

        list_scope = config._native_server_action_scope("list")
        form_scope = config._native_server_action_scope("form")
        mixed_scope = config._native_server_action_scope("tree,form")

        self.assertEqual(list_scope.get("selection"), "multi")
        self.assertEqual(list_scope.get("visible_profiles"), ["readonly", "list"])
        self.assertEqual(form_scope.get("selection"), "none")
        self.assertEqual(form_scope.get("visible_profiles"), ["create", "edit", "readonly"])
        self.assertEqual(mixed_scope.get("selection"), "multi")
        self.assertEqual(mixed_scope.get("visible_profiles"), ["readonly", "list"])

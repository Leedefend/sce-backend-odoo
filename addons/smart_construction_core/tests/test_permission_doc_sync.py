# -*- coding: utf-8 -*-
import json
import os
import re

from odoo.tests.common import TransactionCase, tagged

from .perm_matrix import PERM_MATRIX


@tagged("post_install", "-at_install", "sc_perm", "sc_upgrade")
class TestPermissionDocSync(TransactionCase):
    """文档与矩阵一致性：防止代码/文档漂移。"""

    def test_perm_matrix_doc_block_matches_code(self):
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        doc_path = os.path.join(repo_root, "docs", "audit", "permission_matrix_v0.2.md")
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        block = re.search(
            r"<!-- PERM_MATRIX_START -->(.*?)<!-- PERM_MATRIX_END -->",
            content,
            re.S,
        )
        self.assertTrue(block, "文档缺少 PERM_MATRIX_START/END 标记块")
        json_block = re.search(r"```json\s*(\{.*?\})\s*```", block.group(1), re.S)
        self.assertTrue(json_block, "标记块内缺少 json 代码块")
        doc_matrix = json.loads(json_block.group(1))
        self.assertEqual(doc_matrix, PERM_MATRIX, "文档矩阵与代码矩阵不一致")

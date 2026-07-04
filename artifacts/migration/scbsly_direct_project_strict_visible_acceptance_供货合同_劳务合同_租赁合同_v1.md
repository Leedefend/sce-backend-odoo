# SCBSLY Direct Project Strict Visible Acceptance v1

Status: `FAIL`
Old: `https://www.builderp.cn/SCBSLY_V2`
New: `http://1.95.85.92:18081` / DB `sc_demo`
Generated: `2026-06-02T06:49:24.424475+00:00`

| 分类 | 菜单 | 旧数 | 新数 | 旧可见列 | 新可见列 | 行级 | 状态 |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 合同类单据 | 租赁合同 | 221 | 221 | 21 | 21 | FAIL | FAIL |
| 合同类单据 | 供货合同 | 849 | 849 | 15 | 15 | FAIL | FAIL |
| 合同类单据 | 劳务合同 | 187 | 187 | 20 | 20 | FAIL | FAIL |

## Failures

```json
[
  {
    "category": "合同类单据",
    "label": "租赁合同",
    "status": "FAIL",
    "failures": [
      "visible_cell_value_mismatch"
    ],
    "old_route_kind": "lowcode_form_list",
    "old_config_id": "a83d43fc44fa43d2abf8b94739e7f7be",
    "old_count": 221,
    "old_headers": [
      "单据状态",
      "单据编号",
      "合同编号",
      "项目名称",
      "合同标题",
      "租赁单位",
      "租赁内容",
      "总数量",
      "已开票金额",
      "已付款金额",
      "未付款金额",
      "未开票金额",
      "总金额",
      "签订时间",
      "经办人及电话",
      "税率",
      "增值税类型",
      "备注",
      "附件",
      "录入人",
      "录入时间"
    ],
    "old_fields": [
      "DJZTText",
      "DJBH",
      "HTBH",
      "XMMC",
      "HTBT",
      "FBDW",
      "FBNR",
      "ZSL",
      "YKPJE",
      "YFKJE",
      "WFKJE",
      "WKPJE",
      "ZJE",
      "QDSJ",
      "JBRJDH",
      "SLV",
      "ZZSLX",
      "BZ1",
      "f_FJ",
      "LRR",
      "LRSJ"
    ],
    "old_header_count": 21,
    "new_match_mode": "exact",
    "new_menu_id": 745,
    "new_action_id": 911,
    "new_model": "sc.legacy.direct.acceptance.fact",
    "new_count": 221,
    "new_headers": [
      "单据状态",
      "单据编号",
      "合同编号",
      "项目名称",
      "合同标题",
      "租赁单位",
      "租赁内容",
      "总数量",
      "已开票金额",
      "已付款金额",
      "未付款金额",
      "未开票金额",
      "总金额",
      "签订时间",
      "经办人及电话",
      "税率",
      "增值税类型",
      "备注",
      "附件",
      "录入人",
      "录入时间"
    ],
    "new_fields": [
      "legacy_visible_01",
      "legacy_visible_02",
      "legacy_visible_03",
      "legacy_visible_04",
      "legacy_visible_05",
      "legacy_visible_06",
      "legacy_visible_07",
      "legacy_visible_08",
      "legacy_visible_09",
      "legacy_visible_10",
      "legacy_visible_11",
      "legacy_visible_12",
      "legacy_visible_13",
      "legacy_visible_14",
      "legacy_visible_15",
      "legacy_visible_16",
      "legacy_visible_17",
      "legacy_visible_18",
      "legacy_visible_19",
      "legacy_visible_20",
      "legacy_visible_21"
    ],
    "new_header_count": 21,
    "row_compare_status": "FAIL",
    "row_compare": {
      "identity_field": "DJBH",
      "old_identity_count": 221,
      "new_identity_count": 221,
      "parse_failures": 0,
      "missing_sample": [],
      "extra_sample": [],
      "hash_mismatch_sample": []
    },
    "visible_cell_compare": {
      "status": "FAIL",
      "compared_nonempty_pairs": 4285,
      "old_nonempty_new_empty_count": 220,
      "old_empty_new_nonempty_count": 0,
      "visible_mismatch_count": 0,
      "missing_samples": [
        {
          "identity": "JX-20260527-002",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260527-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260331-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260325-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260324-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260323-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260320-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260316-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260310-003",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260310-002",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260201-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260130-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260129-003",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260129-002",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260129-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260128-001",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260126-005",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260126-004",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260126-003",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "JX-20260126-002",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_19",
          "old_value": "附件(1)",
          "new_value": ""
        }
      ],
      "extra_samples": [],
      "mismatch_samples": []
    }
  },
  {
    "category": "合同类单据",
    "label": "供货合同",
    "status": "FAIL",
    "failures": [
      "visible_cell_value_mismatch"
    ],
    "old_route_kind": "lowcode_form_list",
    "old_config_id": "77585134a02a48e7bd578e8ee3dd5bf2",
    "old_count": 849,
    "old_headers": [
      "单据状态",
      "合同编号",
      "标题",
      "供应商",
      "购货单位",
      "总金额",
      "已开票金额",
      "已付款金额",
      "未付款金额",
      "未开票金额",
      "项目名称",
      "录入时间",
      "税率",
      "录入人",
      "附件"
    ],
    "old_fields": [
      "DJZTText",
      "f_HTBH",
      "BT",
      "f_GYSName",
      "TSXMMC",
      "ZJE",
      "YKPJE",
      "YFKJE",
      "WFKJE",
      "WKPJE",
      "ProjectName",
      "f_LRRQ",
      "D_SCBSJS_SL1",
      "f_LRR",
      "f_FJ"
    ],
    "old_header_count": 15,
    "new_match_mode": "exact",
    "new_menu_id": 746,
    "new_action_id": 912,
    "new_model": "sc.legacy.direct.acceptance.fact",
    "new_count": 849,
    "new_headers": [
      "单据状态",
      "合同编号",
      "标题",
      "供应商",
      "购货单位",
      "总金额",
      "已开票金额",
      "已付款金额",
      "未付款金额",
      "未开票金额",
      "项目名称",
      "录入时间",
      "税率",
      "录入人",
      "附件"
    ],
    "new_fields": [
      "legacy_visible_01",
      "legacy_visible_02",
      "legacy_visible_03",
      "legacy_visible_04",
      "legacy_visible_05",
      "legacy_visible_06",
      "legacy_visible_07",
      "legacy_visible_08",
      "legacy_visible_09",
      "legacy_visible_10",
      "legacy_visible_11",
      "legacy_visible_12",
      "legacy_visible_13",
      "legacy_visible_14",
      "legacy_visible_15"
    ],
    "new_header_count": 15,
    "row_compare_status": "FAIL",
    "row_compare": {
      "identity_field": "Id",
      "old_identity_count": 849,
      "new_identity_count": 849,
      "parse_failures": 0,
      "missing_sample": [],
      "extra_sample": [],
      "hash_mismatch_sample": []
    },
    "visible_cell_compare": {
      "status": "FAIL",
      "compared_nonempty_pairs": 12246,
      "old_nonempty_new_empty_count": 38,
      "old_empty_new_nonempty_count": 0,
      "visible_mismatch_count": 0,
      "missing_samples": [
        {
          "identity": "03e286969eb049faa964a17edcec3c7e",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "d1af20ccad5d45d08250cdee486a12be",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "3200d5ecb824467595cc60cfa1c1cc8f",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "1210730b8d754534a249c12f10d8b6ec",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "4e765b90176d4112a2e3b556ab30fc4d",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "761de1e5eaee4018b54b1297d993ffab",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "b6b3727485154ecda40b577f5c66d8ab",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "acd4edec1ccc43e2bfb1a785336424ed",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "d31c64f4acd84b908fb56f7340a198e3",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "e1751fb19ac64597a916ca94e5878ace",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "eb8ec4aebd0e4decad29f371cabac3af",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "b2e47ba305f543678912ecc40d6beb94",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "ba94d38d921d4f05a3a94b6818e55eb7",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "c0155179e70944cca4b0b4767c1ed8bc",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "59bedfeffc3f44909755357dbe6f1087",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "93493a117c374f81b117934aa6045f49",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "437871715b444e5e8f8fa7637f41b88b",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "410b5c7721c14905a34f33db1b9a2fc6",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "3d80fc01fcc04a4d84618fe32440dbe4",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        },
        {
          "identity": "0fb10f737f384e58bbd9778388a83805",
          "header": "附件",
          "old_field": "f_FJ",
          "new_field": "legacy_visible_15",
          "old_value": "附件(1)",
          "new_value": ""
        }
      ],
      "extra_samples": [],
      "mismatch_samples": []
    }
  },
  {
    "category": "合同类单据",
    "label": "劳务合同",
    "status": "FAIL",
    "failures": [
      "visible_cell_value_mismatch"
    ],
    "old_route_kind": "lowcode_form_list",
    "old_config_id": "838f5d5f02f34770977a6195d072ba30",
    "old_count": 187,
    "old_headers": [
      "单据状态",
      "单据编号",
      "项目名称",
      "签订日期",
      "标题",
      "劳务单位",
      "施工队负责人",
      "总含税金额",
      "结算比列",
      "已开票金额",
      "已付款金额",
      "未付款金额",
      "未开票金额",
      "计价方式",
      "施工部位",
      "合同编号",
      "附件",
      "录入人",
      "支付条款",
      "推送项目名称"
    ],
    "old_fields": [
      "DJZTText",
      "DJBH",
      "f_GCMC",
      "f_QDRQ",
      "BT",
      "f_BZZ",
      "SGDFZR",
      "ZHSJE",
      "JDJSBL",
      "YKPJE",
      "YFKJE",
      "WFKJE",
      "WKPJE",
      "JJFSTEXT",
      "SGBWMC",
      "f_HTBH",
      "f_HTWB",
      "f_LRR",
      "f_HTNR",
      "TSXMMC"
    ],
    "old_header_count": 20,
    "new_match_mode": "exact",
    "new_menu_id": 747,
    "new_action_id": 913,
    "new_model": "sc.legacy.direct.acceptance.fact",
    "new_count": 187,
    "new_headers": [
      "单据状态",
      "单据编号",
      "项目名称",
      "签订日期",
      "标题",
      "劳务单位",
      "施工队负责人",
      "总含税金额",
      "结算比列",
      "已开票金额",
      "已付款金额",
      "未付款金额",
      "未开票金额",
      "计价方式",
      "施工部位",
      "合同编号",
      "附件",
      "录入人",
      "支付条款",
      "推送项目名称"
    ],
    "new_fields": [
      "legacy_visible_01",
      "legacy_visible_02",
      "legacy_visible_03",
      "legacy_visible_04",
      "legacy_visible_05",
      "legacy_visible_06",
      "legacy_visible_07",
      "legacy_visible_08",
      "legacy_visible_09",
      "legacy_visible_10",
      "legacy_visible_11",
      "legacy_visible_12",
      "legacy_visible_13",
      "legacy_visible_14",
      "legacy_visible_15",
      "legacy_visible_16",
      "legacy_visible_17",
      "legacy_visible_18",
      "legacy_visible_19",
      "legacy_visible_20"
    ],
    "new_header_count": 20,
    "row_compare_status": "FAIL",
    "row_compare": {
      "identity_field": "DJBH",
      "old_identity_count": 187,
      "new_identity_count": 187,
      "parse_failures": 0,
      "missing_sample": [],
      "extra_sample": [],
      "hash_mismatch_sample": []
    },
    "visible_cell_compare": {
      "status": "FAIL",
      "compared_nonempty_pairs": 2765,
      "old_nonempty_new_empty_count": 0,
      "old_empty_new_nonempty_count": 0,
      "visible_mismatch_count": 175,
      "missing_samples": [],
      "extra_samples": [],
      "mismatch_samples": [
        {
          "identity": "BZHTGL-20260527-002",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "0829dd1f49989ef4d9003ce7e8cd9fd7",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260527-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "453fbca3b09ca683b8c6dc2242f66ec0",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260520-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "eab702735f49a652dd39d88d602a29f4",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260512-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "bfac1a650e9c2253e3b779ba8da5a455",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260323-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "f1d9d08efec5569b10cc623d4f1aa7b9",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260316-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "c9bbbc880886836fb4f52797700b6b2a",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260201-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "06b43b5cc84f3e9839ddff0e1fa1dc5f",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260131-002",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "64312d6d3bb8135fb3412003015b6b55",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260131-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "133105438411229bfec4c9a82478efd0",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260127-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "7ad8a844cb7d30c5f0e247e01402847d",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260126-007",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "4ff65e0e3c1de4175e4e32a05d622c2e",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260126-006",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "f2c87876ce2f635ade04b4d0f801e4cb",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260126-004",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "4da708cf8855e49d93b1a24e49c039de",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260126-002",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "00dcf56989d10786c83ccc53cf864f85",
          "new_value": "附件(2)"
        },
        {
          "identity": "BZHTGL-20260126-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "17b29b4e869abfa77c2071ee065296b5",
          "new_value": "附件(5)"
        },
        {
          "identity": "BZHTGL-20260122-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "19d1e11eda490dcce4ff0781e996e647",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260118-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "d02966daa9a546fe24bbe78de3997a43",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260117-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "5899b765c27a924b220edfc5c8ad1902",
          "new_value": "附件(2)"
        },
        {
          "identity": "BZHTGL-20260115-001",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "ff23f3ba700f259fe77f436ec2aeddd5",
          "new_value": "附件(1)"
        },
        {
          "identity": "BZHTGL-20260113-002",
          "header": "附件",
          "old_field": "f_HTWB",
          "new_field": "legacy_visible_17",
          "old_value": "f964e4a690b0b090763d61d63e10c57c",
          "new_value": "附件(1)"
        }
      ]
    }
  }
]
```

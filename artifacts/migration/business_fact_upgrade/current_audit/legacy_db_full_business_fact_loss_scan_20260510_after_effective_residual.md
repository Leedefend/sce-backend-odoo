# Legacy DB Full Business Fact Loss Scan v1

Status: `PASS`

Source: `legacy-mssql-restore:LegacyDb`

## Summary

```json
{
  "total_tables": 4312,
  "non_empty_tables": 1128,
  "candidate_tables": 150,
  "candidate_rows": 56833,
  "classification_counts": {
    "known_replayed_or_assetized": 348,
    "system_or_audit_noise": 362,
    "candidate_needs_manual_screen": 8,
    "reference_or_import_catalog": 489,
    "low_business_fact_signal": 2963,
    "candidate_secondary_business_fact": 142
  },
  "classification_row_counts": {
    "known_replayed_or_assetized": 3738395,
    "system_or_audit_noise": 1245813,
    "candidate_needs_manual_screen": 22997,
    "reference_or_import_catalog": 2518257,
    "low_business_fact_signal": 19746,
    "candidate_secondary_business_fact": 33836
  },
  "top_candidate_families": [
    {
      "family": "pm",
      "tables": 4,
      "rows": 21693,
      "effective_tables": 0,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "Pm_Person_Department_PDuty",
          "rows": 102,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "Pm_Person_Department",
          "rows": 786,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "Pm_base_Person_RYXQSQ",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "PM_RYYDGL",
          "rows": 20804,
          "classification": "candidate_needs_manual_screen",
          "score": 25
        }
      ]
    },
    {
      "family": "t",
      "tables": 38,
      "rows": 16551,
      "effective_tables": 0,
      "secondary_tables": 37,
      "top_tables": [
        {
          "table": "T_Base_DBDW",
          "rows": 754,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "T_Base_LLDWAndLWDW",
          "rows": 91,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "T_Base_LLDWAndFBDW",
          "rows": 15,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "T_Base_CooperatCompany_Account",
          "rows": 8008,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_Base_ConstructPlaceDetail",
          "rows": 1620,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_Base_BuildMaterial_XGJL_YW",
          "rows": 199,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_base_UserAndKey",
          "rows": 38,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_Base_Import_JX_BuildMaterialDetail_XGJL_YW",
          "rows": 13,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_Base_SupplierInfo_LYPJB_CB",
          "rows": 11,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_JH_CGJH_CB",
          "rows": 11,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    },
    {
      "family": "cgpt",
      "tables": 4,
      "rows": 9516,
      "effective_tables": 0,
      "secondary_tables": 4,
      "top_tables": [
        {
          "table": "CGPT_T_Base_SupplierUser",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 60
        },
        {
          "table": "CGPT_Base_JCCLK",
          "rows": 9499,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "CGPT_T_Base_CGGGLXSZ",
          "rows": 15,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "CGPT_T_Base_HZDWKC_JX",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "office_admin",
      "tables": 27,
      "rows": 3811,
      "effective_tables": 0,
      "secondary_tables": 27,
      "top_tables": [
        {
          "table": "BGGL_TZXX_WJHQ",
          "rows": 2076,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_KQTJ_YTWC",
          "rows": 1137,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_XZ_BZ_CB",
          "rows": 77,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_QSJRW_GZQS_CB",
          "rows": 43,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_QSJRW_GZQS_HF",
          "rows": 28,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_TZXX_HY",
          "rows": 191,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "BGGL_ZCJYP_CLJY",
          "rows": 83,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "BGGL_KQTJ_WDK_New",
          "rows": 64,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "BGGL_HBZJ_XZD_JDSPD",
          "rows": 37,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "BGGL_BGYP_Base_YPKM",
          "rows": 12,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "sgbw",
      "tables": 1,
      "rows": 1439,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "SGBW_QDKM",
          "rows": 1439,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    },
    {
      "family": "sggl",
      "tables": 17,
      "rows": 987,
      "effective_tables": 0,
      "secondary_tables": 17,
      "top_tables": [
        {
          "table": "SGGL_Node_Abarbeitung",
          "rows": 16,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_Bar_ConstructionPlan_CB_Task",
          "rows": 869,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "SGGL_JBXXGL_SPJHQK",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "SGGL_Base_SGRZ_SGLH_Set",
          "rows": 9,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "SGGL_Base_AQSGRQ_GSLPHP",
          "rows": 7,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "SGGL_SBGL_SBGYDW",
          "rows": 6,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "SGGL_XXJDTX",
          "rows": 6,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "SGGL_Base_SGRZ_DZLW_NEW",
          "rows": 5,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "SGGL_Base_SGRZ_GSLPHP",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "SGGL_HJJC_HJZG",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "a",
      "tables": 1,
      "rows": 716,
      "effective_tables": 0,
      "secondary_tables": 0,
      "top_tables": [
        {
          "table": "A_HistoryRecord",
          "rows": 716,
          "classification": "candidate_needs_manual_screen",
          "score": 35
        }
      ]
    },
    {
      "family": "cwgl",
      "tables": 4,
      "rows": 422,
      "effective_tables": 0,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "CWGL_FYBX_SKDW",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "CWGL_SQGL_CCSQ",
          "rows": 177,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "CWGL_DZFPK",
          "rows": 79,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "CWGL_SQGL_CCSQ_CB",
          "rows": 165,
          "classification": "candidate_needs_manual_screen",
          "score": 20
        }
      ]
    },
    {
      "family": "gzgl",
      "tables": 1,
      "rows": 389,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "GZGL_BMSJWH",
          "rows": 389,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "jhjrz",
      "tables": 4,
      "rows": 341,
      "effective_tables": 0,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "JHJRZ_FBRW_CB",
          "rows": 96,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "JHJRZ_FBRW",
          "rows": 31,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "JHJRZ_FBRW_BLXQ",
          "rows": 9,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "JHJRZ_RWCKJLB",
          "rows": 205,
          "classification": "candidate_needs_manual_screen",
          "score": 20
        }
      ]
    },
    {
      "family": "dataspider",
      "tables": 2,
      "rows": 250,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "DataSpider_ScjstPersonInfo",
          "rows": 54,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "DataSpider_ScjstPersonCertificate",
          "rows": 196,
          "classification": "candidate_needs_manual_screen",
          "score": 20
        }
      ]
    },
    {
      "family": "zlgl",
      "tables": 2,
      "rows": 177,
      "effective_tables": 0,
      "secondary_tables": 2,
      "top_tables": [
        {
          "table": "ZLGL_Base_ZLLXAndQX",
          "rows": 156,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "ZLGL_Base_ZLLX_New",
          "rows": 21,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "xmgl",
      "tables": 5,
      "rows": 159,
      "effective_tables": 0,
      "secondary_tables": 4,
      "top_tables": [
        {
          "table": "XMGL_SRHT_QTSRHT_CB",
          "rows": 8,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "XMGL_WZGL_CKGL_YFD_CB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "XMGL_JSJSH_SH_SHWZSQD",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "XMGL_YSZJ_FXB_CLCBFXB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "XMGL_LYGL_LYRY",
          "rows": 147,
          "classification": "candidate_needs_manual_screen",
          "score": 20
        }
      ]
    },
    {
      "family": "base",
      "tables": 1,
      "rows": 125,
      "effective_tables": 0,
      "secondary_tables": 0,
      "top_tables": [
        {
          "table": "BASE_APP_COMMONOLDUSER",
          "rows": 125,
          "classification": "candidate_needs_manual_screen",
          "score": 20
        }
      ]
    },
    {
      "family": "d",
      "tables": 5,
      "rows": 61,
      "effective_tables": 0,
      "secondary_tables": 5,
      "top_tables": [
        {
          "table": "D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS_CB",
          "rows": 53,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_SCBSJS_SW_JC_GSPTFP_CB",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "D_BYK_ZZXT_HBZJ_QSJRW_RWFB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "D_SCBSJS_SW_JC_GSPTFP",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "zyjx",
      "tables": 12,
      "rows": 48,
      "effective_tables": 0,
      "secondary_tables": 12,
      "top_tables": [
        {
          "table": "ZYJX_ZY_T_SBZLJC_SBWZSQ_CB",
          "rows": 12,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "ZYJX_ZY_T_CG_CGSQ_CB",
          "rows": 6,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "ZYJX_ZY_T_SBZLJC_SBZLRK_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "ZYJX_ZY_T_CG_CGSQ",
          "rows": 15,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_SBJC_SBRK",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_SBZLJC_SBWZSQ",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_Base_ZLHT_ZLDW",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_NDJJF_SBDB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_NDJJF_SBHK",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_SBJC_SBRK_CB",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 40
        }
      ]
    },
    {
      "family": "gdzc",
      "tables": 1,
      "rows": 46,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "GDZC_WXZC",
          "rows": 46,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "invoice",
      "tables": 1,
      "rows": 21,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "Invoice_CB",
          "rows": 21,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    },
    {
      "family": "wz",
      "tables": 1,
      "rows": 21,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "WZ_Base_GYSBJ_CB",
          "rows": 21,
          "classification": "candidate_secondary_business_fact",
          "score": 40
        }
      ]
    },
    {
      "family": "other",
      "tables": 1,
      "rows": 14,
      "effective_tables": 0,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "Invoice",
          "rows": 14,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    }
  ],
  "top_candidates": [
    {
      "schema": "dbo",
      "table": "T_Base_DBDW",
      "row_count": 754,
      "column_count": 29,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 65,
      "signals": {
        "amount": [
          "IsCompleteProject"
        ],
        "date": [
          "SJBMC",
          "ImportTime"
        ],
        "project": [
          "XMID",
          "IsCompleteProject",
          "XMMC"
        ],
        "deleted": [
          "Del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "Pm_Person_Department_PDuty",
      "row_count": 102,
      "column_count": 20,
      "classification": "candidate_secondary_business_fact",
      "family": "pm",
      "business_signal_score": 65,
      "signals": {
        "amount": [
          "Ding_Userid"
        ],
        "date": [
          "SJBMC",
          "RZRQ"
        ],
        "project": [
          "XMID"
        ],
        "deleted": [
          "Del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_LLDWAndLWDW",
      "row_count": 91,
      "column_count": 12,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 65,
      "signals": {
        "amount": [
          "T_Base_LLDW2_Guid",
          "T_Base_LLDW2_Code",
          "LW_Base_LWDWSZ_Id",
          "LW_Base_LWDWSZ_Code"
        ],
        "date": [
          "SJBMC",
          "LRSJ"
        ],
        "project": [
          "XMID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGGL_Node_Abarbeitung",
      "row_count": 16,
      "column_count": 18,
      "classification": "candidate_secondary_business_fact",
      "family": "sggl",
      "business_signal_score": 65,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName"
        ],
        "date": [
          "SJBMC",
          "billDate",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_LLDWAndFBDW",
      "row_count": 15,
      "column_count": 11,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 65,
      "signals": {
        "amount": [
          "T_Base_LLDW2_Guid",
          "T_Base_LLDW2_Code",
          "LW_Base_FBDW_Id"
        ],
        "date": [
          "SJBM",
          "LRSJ"
        ],
        "project": [
          "XMID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "PJ_Bill",
      "row_count": 4,
      "column_count": 17,
      "classification": "candidate_secondary_business_fact",
      "family": "pj",
      "business_signal_score": 65,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName"
        ],
        "date": [
          "SJBMC",
          "recordDate",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CGPT_T_Base_SupplierUser",
      "row_count": 1,
      "column_count": 21,
      "classification": "candidate_secondary_business_fact",
      "family": "cgpt",
      "business_signal_score": 60,
      "signals": {
        "amount": [
          "SupplierUser_Id",
          "UserName",
          "UserType",
          "UserState"
        ],
        "date": [
          "SJBMC",
          "ImportTime",
          "DQSJ"
        ],
        "partner": [
          "SupplierUser_Id",
          "Supplier_Id"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CGPT_Base_JCCLK",
      "row_count": 9499,
      "column_count": 46,
      "classification": "candidate_secondary_business_fact",
      "family": "cgpt",
      "business_signal_score": 50,
      "signals": {
        "date": [
          "f_Tree_importTime",
          "LRSJ"
        ],
        "project": [
          "f_Tree_XMMC"
        ],
        "parent": [
          "f_Tree_Parentid",
          "f_Tree_ParentGuid",
          "ImportXmPid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_CooperatCompany_Account",
      "row_count": 8008,
      "column_count": 9,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "date": [
          "SJBMC"
        ],
        "project": [
          "f_XMID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_TZXX_WJHQ",
      "row_count": 2076,
      "column_count": 27,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 50,
      "signals": {
        "date": [
          "SJBMC",
          "WJTJRQ",
          "LRSJ",
          "XGSJ",
          "HQWCSJ",
          "D_SCBSJS_SKDF"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_ConstructPlaceDetail",
      "row_count": 1620,
      "column_count": 24,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "date": [
          "f_Tree_importTime"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "f_Tree_ParentId",
          "f_Tree_ParentGuid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGBW_QDKM",
      "row_count": 1439,
      "column_count": 10,
      "classification": "candidate_secondary_business_fact",
      "family": "sgbw",
      "business_signal_score": 50,
      "signals": {
        "date": [
          "CreatedDate"
        ],
        "project": [
          "ImportByXMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_KQTJ_YTWC",
      "row_count": 1137,
      "column_count": 27,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 50,
      "signals": {
        "date": [
          "SJBMC",
          "WCSJ",
          "FHSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGGL_Bar_ConstructionPlan_CB_Task",
      "row_count": 869,
      "column_count": 35,
      "classification": "candidate_secondary_business_fact",
      "family": "sggl",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "collapsed",
          "userids"
        ],
        "date": [
          "SJBMC",
          "BGKSSJ",
          "BGJSSJ",
          "START_DATE"
        ],
        "parent": [
          "PID",
          "PARENT_ID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_BuildMaterial_XGJL_YW",
      "row_count": 199,
      "column_count": 19,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "T_Base_BuildMaterial_XGJL_Id"
        ],
        "date": [
          "SJBMC",
          "YWDJRQ",
          "XGSJ"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "ZLGL_Base_ZLLXAndQX",
      "row_count": 156,
      "column_count": 9,
      "classification": "candidate_secondary_business_fact",
      "family": "zlgl",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "ZLGL_Base_ZLLX_Id",
          "UserId",
          "UserName"
        ],
        "date": [
          "SJBMC",
          "LRSJ"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "JHJRZ_FBRW_CB",
      "row_count": 96,
      "column_count": 21,
      "classification": "candidate_secondary_business_fact",
      "family": "jhjrz",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "RYUserID"
        ],
        "date": [
          "SJBMC",
          "JZRQ"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_XZ_BZ_CB",
      "row_count": 77,
      "column_count": 11,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "BZJE"
        ],
        "date": [
          "D_SCBSJS_BZSX"
        ],
        "parent": [
          "ZBID",
          "Pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "DataSpider_ScjstPersonInfo",
      "row_count": 54,
      "column_count": 21,
      "classification": "candidate_secondary_business_fact",
      "family": "dataspider",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "Sex"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS_CB",
      "row_count": 53,
      "column_count": 15,
      "classification": "candidate_secondary_business_fact",
      "family": "d",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JFJE",
          "DFJE"
        ],
        "date": [
          "JYRQ",
          "JYRQ_"
        ],
        "parent": [
          "PID",
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_QSJRW_GZQS_CB",
      "row_count": 43,
      "column_count": 10,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "RYUserID"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_base_UserAndKey",
      "row_count": 38,
      "column_count": 18,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "userid"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "JHJRZ_FBRW",
      "row_count": 31,
      "column_count": 24,
      "classification": "candidate_secondary_business_fact",
      "family": "jhjrz",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "FQRUserID"
        ],
        "date": [
          "SJBMC",
          "RQ",
          "LRSJ",
          "ZRWJZRQ"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_QSJRW_GZQS_HF",
      "row_count": 28,
      "column_count": 11,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "HFRUserID"
        ],
        "date": [
          "SJBMC",
          "HFLRSJ",
          "HFXGSJ"
        ],
        "parent": [
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "Invoice_CB",
      "row_count": 21,
      "column_count": 15,
      "classification": "candidate_secondary_business_fact",
      "family": "invoice",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "goodserviceName",
          "price",
          "tax",
          "taxRate",
          "zeroTaxRateSign",
          "zeroTaxRateSignName"
        ],
        "date": [
          "CreatedTime"
        ],
        "parent": [
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "Invoice",
      "row_count": 14,
      "column_count": 28,
      "classification": "candidate_secondary_business_fact",
      "family": "other",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "purchaserName",
          "salesTaxpayerAddress",
          "salesTaxpayerBankAccount",
          "salesTaxpayerNum",
          "taxDiskCode",
          "taxpayerAddressOrId",
          "taxpayerBankAccount",
          "taxpayerNumber",
          "totalAmount",
          "totalTaxNum",
          "totalTaxSum"
        ],
        "date": [
          "billingTime",
          "checkDate",
          "CreatedTime"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_Import_JX_BuildMaterialDetail_XGJL_YW",
      "row_count": 13,
      "column_count": 19,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "T_Base_Import_JX_BuildMaterialDetail_XGJL_Id"
        ],
        "date": [
          "SJBMC",
          "YWDJRQ",
          "XGSJ"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "ZYJX_ZY_T_SBZLJC_SBWZSQ_CB",
      "row_count": 12,
      "column_count": 17,
      "classification": "candidate_secondary_business_fact",
      "family": "zyjx",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_SupplierInfo_LYPJB_CB",
      "row_count": 11,
      "column_count": 9,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "RQ"
        ],
        "parent": [
          "ZBID",
          "PID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_JH_CGJH_CB",
      "row_count": 11,
      "column_count": 57,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE",
          "ZZJE",
          "SE",
          "JE_NO"
        ],
        "date": [
          "SJBMC",
          "QWDCSJ",
          "SHRQ",
          "YHSJ",
          "YJDCSJ"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "JHJRZ_FBRW_BLXQ",
      "row_count": 9,
      "column_count": 10,
      "classification": "candidate_secondary_business_fact",
      "family": "jhjrz",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "UserID"
        ],
        "date": [
          "SJBMC",
          "BLSJ"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "XMGL_SRHT_QTSRHT_CB",
      "row_count": 8,
      "column_count": 11,
      "classification": "candidate_secondary_business_fact",
      "family": "xmgl",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "PID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_StrategicSupply_Info_CB",
      "row_count": 7,
      "column_count": 12,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "ZYJX_ZY_T_CG_CGSQ_CB",
      "row_count": 6,
      "column_count": 17,
      "classification": "candidate_secondary_business_fact",
      "family": "zyjx",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_CGHT_CGDD_CB",
      "row_count": 5,
      "column_count": 23,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE",
          "JE_NO",
          "SE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_GYSHT_WDJHT_CB",
      "row_count": 5,
      "column_count": 12,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_SC_SCD_CB",
      "row_count": 4,
      "column_count": 19,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "BCHYJE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "YSZJ_CZBS_CZQDBS_CB",
      "row_count": 4,
      "column_count": 21,
      "classification": "candidate_secondary_business_fact",
      "family": "yszj",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "BQWC_JE",
          "LJJE",
          "JFHD_JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "D_SCBSJS_SW_JC_GSPTFP_CB",
      "row_count": 3,
      "column_count": 21,
      "classification": "candidate_secondary_business_fact",
      "family": "d",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE",
          "SE"
        ],
        "date": [
          "KPRQ"
        ],
        "parent": [
          "PID",
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_GYSHT_INFO_CB_Ext_XAKW",
      "row_count": 2,
      "column_count": 13,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_GYSHT_INFO_RKYSD_Ext_XAKW",
      "row_count": 2,
      "column_count": 17,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE",
          "JE_NO",
          "SE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "XMGL_WZGL_CKGL_YFD_CB",
      "row_count": 2,
      "column_count": 10,
      "classification": "candidate_secondary_business_fact",
      "family": "xmgl",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CWGL_FYBX_SKDW",
      "row_count": 1,
      "column_count": 10,
      "classification": "candidate_secondary_business_fact",
      "family": "cwgl",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "SKJE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "P_ZTB_CustomerProfile",
      "row_count": 1,
      "column_count": 51,
      "classification": "candidate_secondary_business_fact",
      "family": "bid_tender",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "XSJE"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XSJE"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "Del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGGL_JBXXGL_SPJHQK",
      "row_count": 1,
      "column_count": 12,
      "classification": "candidate_secondary_business_fact",
      "family": "sggl",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JHJE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_Import_ZL_BuildMaterialDetail_XGJL_YW",
      "row_count": 1,
      "column_count": 19,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "T_Base_Import_ZL_BuildMaterialDetail_XGJL_Id"
        ],
        "date": [
          "SJBMC",
          "YWDJRQ",
          "XGSJ"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_GYSHT_INFO_DHQD_Ext_XAKW",
      "row_count": 1,
      "column_count": 14,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "DHSJ"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "YT_SGLKYSB_CB",
      "row_count": 1,
      "column_count": 32,
      "classification": "candidate_secondary_business_fact",
      "family": "yt",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "f_Tree_JE"
        ],
        "date": [
          "SJBMC",
          "f_Tree_ImportTime"
        ],
        "parent": [
          "ZBID",
          "f_Tree_ParentId",
          "f_Tree_ParentGuid",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "ZYJX_ZY_T_SBZLJC_SBZLRK_CB",
      "row_count": 1,
      "column_count": 15,
      "classification": "candidate_secondary_business_fact",
      "family": "zyjx",
      "business_signal_score": 50,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_SupplierInfo_GHLX",
      "row_count": 3209,
      "column_count": 6,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC"
        ],
        "partner": [
          "SupplierId"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_refe",
      "row_count": 992,
      "column_count": 15,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "f_date"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "parentId"
        ],
        "deleted": [
          "Del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "Pm_Person_Department",
      "row_count": 786,
      "column_count": 27,
      "classification": "candidate_secondary_business_fact",
      "family": "pm",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "LRSJ"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ParentBH",
          "ParentId",
          "ParentGuid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_Import_JX_BuildMaterialDetail",
      "row_count": 489,
      "column_count": 31,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "f_Tree_importTime"
        ],
        "project": [
          "f_XMID",
          "XMMC"
        ],
        "parent": [
          "f_Tree_Parentid",
          "f_Tree_ParentGuid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "GZGL_BMSJWH",
      "row_count": 389,
      "column_count": 59,
      "classification": "candidate_secondary_business_fact",
      "family": "gzgl",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "ZSJT",
          "LRSJ"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ZBID",
          "Pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_Import_ZL_BuildMaterialDetail",
      "row_count": 223,
      "column_count": 29,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "f_Tree_importTime"
        ],
        "project": [
          "f_XMID",
          "XMMC"
        ],
        "parent": [
          "f_Tree_Parentid",
          "f_Tree_ParentGuid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_TZXX_HY",
      "row_count": 191,
      "column_count": 36,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "SBSJ",
          "KSSJ",
          "JSSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CWGL_SQGL_CCSQ",
      "row_count": 177,
      "column_count": 38,
      "classification": "candidate_secondary_business_fact",
      "family": "cwgl",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "SQRQ",
          "CCSJ_Star",
          "CCSJ_End",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_ZCJYP_CLJY",
      "row_count": 83,
      "column_count": 38,
      "classification": "candidate_secondary_business_fact",
      "family": "office_admin",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "SQRQ",
          "SYSJ_S",
          "SYSJ_E",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CWGL_DZFPK",
      "row_count": 79,
      "column_count": 19,
      "classification": "candidate_secondary_business_fact",
      "family": "cwgl",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "Del"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_BuildMaterial_XGJL",
      "row_count": 76,
      "column_count": 15,
      "classification": "candidate_secondary_business_fact",
      "family": "t",
      "business_signal_score": 45,
      "signals": {
        "date": [
          "SJBMC",
          "XGSJ"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "pid"
        ]
      }
    }
  ]
}
```

## Top Candidate Tables

| Table | Rows | Classification | Score | Signals |
|---|---:|---|---:|---|
| T_Base_DBDW | 754 | candidate_secondary_business_fact | 65 | amount:IsCompleteProject, date:SJBMC/ImportTime, project:XMID/IsCompleteProject/XMMC, deleted:Del |
| Pm_Person_Department_PDuty | 102 | candidate_secondary_business_fact | 65 | amount:Ding_Userid, date:SJBMC/RZRQ, project:XMID, deleted:Del |
| T_Base_LLDWAndLWDW | 91 | candidate_secondary_business_fact | 65 | amount:T_Base_LLDW2_Guid/T_Base_LLDW2_Code/LW_Base_LWDWSZ_Id/LW_Base_LWDWSZ_Code, date:SJBMC/LRSJ, project:XMID |
| SGGL_Node_Abarbeitung | 16 | candidate_secondary_business_fact | 65 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/billDate/createUserID/createUserName, project:XMID/XMMC |
| T_Base_LLDWAndFBDW | 15 | candidate_secondary_business_fact | 65 | amount:T_Base_LLDW2_Guid/T_Base_LLDW2_Code/LW_Base_FBDW_Id, date:SJBM/LRSJ, project:XMID |
| PJ_Bill | 4 | candidate_secondary_business_fact | 65 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/recordDate/createUserID/createUserName, project:XMID/XMMC, deleted:DEL |
| CGPT_T_Base_SupplierUser | 1 | candidate_secondary_business_fact | 60 | amount:SupplierUser_Id/UserName/UserType/UserState, date:SJBMC/ImportTime/DQSJ, partner:SupplierUser_Id/Supplier_Id |
| CGPT_Base_JCCLK | 9499 | candidate_secondary_business_fact | 50 | date:f_Tree_importTime/LRSJ, project:f_Tree_XMMC, parent:f_Tree_Parentid/f_Tree_ParentGuid/ImportXmPid |
| T_Base_CooperatCompany_Account | 8008 | candidate_secondary_business_fact | 50 | date:SJBMC, project:f_XMID, parent:ZBID/pid |
| BGGL_TZXX_WJHQ | 2076 | candidate_secondary_business_fact | 50 | date:SJBMC/WJTJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_Base_ConstructPlaceDetail | 1620 | candidate_secondary_business_fact | 50 | date:f_Tree_importTime, project:XMID/XMMC, parent:f_Tree_ParentId/f_Tree_ParentGuid |
| SGBW_QDKM | 1439 | candidate_secondary_business_fact | 50 | date:CreatedDate, project:ImportByXMMC, parent:pid, deleted:del |
| BGGL_KQTJ_YTWC | 1137 | candidate_secondary_business_fact | 50 | date:SJBMC/WCSJ/FHSJ/LRSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| SGGL_Bar_ConstructionPlan_CB_Task | 869 | candidate_secondary_business_fact | 50 | amount:collapsed/userids, date:SJBMC/BGKSSJ/BGJSSJ/START_DATE, parent:PID/PARENT_ID |
| T_Base_BuildMaterial_XGJL_YW | 199 | candidate_secondary_business_fact | 50 | amount:T_Base_BuildMaterial_XGJL_Id, date:SJBMC/YWDJRQ/XGSJ, parent:pid |
| ZLGL_Base_ZLLXAndQX | 156 | candidate_secondary_business_fact | 50 | amount:ZLGL_Base_ZLLX_Id/UserId/UserName, date:SJBMC/LRSJ, parent:pid |
| JHJRZ_FBRW_CB | 96 | candidate_secondary_business_fact | 50 | amount:RYUserID, date:SJBMC/JZRQ, parent:ZBID/pid |
| BGGL_XZ_BZ_CB | 77 | candidate_secondary_business_fact | 50 | amount:BZJE, date:D_SCBSJS_BZSX, parent:ZBID/Pid |
| DataSpider_ScjstPersonInfo | 54 | candidate_secondary_business_fact | 50 | amount:Sex, date:SJBMC/LRSJ/XGSJ, parent:pid, deleted:del |
| D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS_CB | 53 | candidate_secondary_business_fact | 50 | amount:JFJE/DFJE, date:JYRQ/JYRQ_, parent:PID/ZBID |
| BGGL_QSJRW_GZQS_CB | 43 | candidate_secondary_business_fact | 50 | amount:RYUserID, date:SJBMC, parent:ZBID/pid |
| T_base_UserAndKey | 38 | candidate_secondary_business_fact | 50 | amount:userid, date:SJBMC/LRSJ/XGSJ, parent:pid, deleted:del |
| JHJRZ_FBRW | 31 | candidate_secondary_business_fact | 50 | amount:FQRUserID, date:SJBMC/RQ/LRSJ/ZRWJZRQ, parent:pid |
| BGGL_QSJRW_GZQS_HF | 28 | candidate_secondary_business_fact | 50 | amount:HFRUserID, date:SJBMC/HFLRSJ/HFXGSJ, parent:ZBID |
| Invoice_CB | 21 | candidate_secondary_business_fact | 50 | amount:goodserviceName/price/tax/taxRate, date:CreatedTime, parent:ZBID |
| Invoice | 14 | candidate_secondary_business_fact | 50 | amount:purchaserName/salesTaxpayerAddress/salesTaxpayerBankAccount/salesTaxpayerNum, date:billingTime/checkDate/CreatedTime, parent:pid |
| T_Base_Import_JX_BuildMaterialDetail_XGJL_YW | 13 | candidate_secondary_business_fact | 50 | amount:T_Base_Import_JX_BuildMaterialDetail_XGJL_Id, date:SJBMC/YWDJRQ/XGSJ, parent:pid |
| ZYJX_ZY_T_SBZLJC_SBWZSQ_CB | 12 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID |
| T_Base_SupplierInfo_LYPJB_CB | 11 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC/RQ, parent:ZBID/PID |
| T_JH_CGJH_CB | 11 | candidate_secondary_business_fact | 50 | amount:JE/ZZJE/SE/JE_NO, date:SJBMC/QWDCSJ/SHRQ/YHSJ, parent:ZBID/pid |
| JHJRZ_FBRW_BLXQ | 9 | candidate_secondary_business_fact | 50 | amount:UserID, date:SJBMC/BLSJ, parent:pid |
| XMGL_SRHT_QTSRHT_CB | 8 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID/PID |
| T_StrategicSupply_Info_CB | 7 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID/pid |
| ZYJX_ZY_T_CG_CGSQ_CB | 6 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID |
| T_CGHT_CGDD_CB | 5 | candidate_secondary_business_fact | 50 | amount:JE/JE_NO/SE, date:SJBMC, parent:ZBID/pid |
| T_GYSHT_WDJHT_CB | 5 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID/pid |
| T_SC_SCD_CB | 4 | candidate_secondary_business_fact | 50 | amount:BCHYJE, date:SJBMC, parent:ZBID/pid |
| YSZJ_CZBS_CZQDBS_CB | 4 | candidate_secondary_business_fact | 50 | amount:BQWC_JE/LJJE/JFHD_JE, date:SJBMC, parent:ZBID/pid |
| D_SCBSJS_SW_JC_GSPTFP_CB | 3 | candidate_secondary_business_fact | 50 | amount:JE/SE, date:KPRQ, parent:PID/ZBID |
| T_GYSHT_INFO_CB_Ext_XAKW | 2 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID/pid |
| T_GYSHT_INFO_RKYSD_Ext_XAKW | 2 | candidate_secondary_business_fact | 50 | amount:JE/JE_NO/SE, date:SJBMC, parent:ZBID/pid |
| XMGL_WZGL_CKGL_YFD_CB | 2 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID/pid |
| CWGL_FYBX_SKDW | 1 | candidate_secondary_business_fact | 50 | amount:SKJE, date:SJBMC, parent:ZBID/pid |
| P_ZTB_CustomerProfile | 1 | candidate_secondary_business_fact | 50 | amount:XSJE, date:SJBMC/LRSJ/XSJE, parent:PID, deleted:Del |
| SGGL_JBXXGL_SPJHQK | 1 | candidate_secondary_business_fact | 50 | amount:JHJE, date:SJBMC, parent:ZBID/pid |
| T_Base_Import_ZL_BuildMaterialDetail_XGJL_YW | 1 | candidate_secondary_business_fact | 50 | amount:T_Base_Import_ZL_BuildMaterialDetail_XGJL_Id, date:SJBMC/YWDJRQ/XGSJ, parent:pid |
| T_GYSHT_INFO_DHQD_Ext_XAKW | 1 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC/DHSJ, parent:ZBID/pid |
| YT_SGLKYSB_CB | 1 | candidate_secondary_business_fact | 50 | amount:f_Tree_JE, date:SJBMC/f_Tree_ImportTime, parent:ZBID/f_Tree_ParentId/f_Tree_ParentGuid/pid |
| ZYJX_ZY_T_SBZLJC_SBZLRK_CB | 1 | candidate_secondary_business_fact | 50 | amount:JE, date:SJBMC, parent:ZBID/pid |
| T_Base_SupplierInfo_GHLX | 3209 | candidate_secondary_business_fact | 45 | date:SJBMC, partner:SupplierId, parent:pid |
| T_Base_refe | 992 | candidate_secondary_business_fact | 45 | date:SJBMC/f_date, project:XMID, parent:parentId, deleted:Del |
| Pm_Person_Department | 786 | candidate_secondary_business_fact | 45 | date:SJBMC/LRSJ, project:XMID, parent:ParentBH/ParentId/ParentGuid |
| T_Base_Import_JX_BuildMaterialDetail | 489 | candidate_secondary_business_fact | 45 | date:f_Tree_importTime, project:f_XMID/XMMC, parent:f_Tree_Parentid/f_Tree_ParentGuid, deleted:DEL |
| GZGL_BMSJWH | 389 | candidate_secondary_business_fact | 45 | date:SJBMC/ZSJT/LRSJ, project:XMID, parent:ZBID/Pid |
| T_Base_Import_ZL_BuildMaterialDetail | 223 | candidate_secondary_business_fact | 45 | date:f_Tree_importTime, project:f_XMID/XMMC, parent:f_Tree_Parentid/f_Tree_ParentGuid |
| BGGL_TZXX_HY | 191 | candidate_secondary_business_fact | 45 | date:SJBMC/SBSJ/KSSJ/JSSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| CWGL_SQGL_CCSQ | 177 | candidate_secondary_business_fact | 45 | date:SJBMC/SQRQ/CCSJ_Star/CCSJ_End, project:XMID/XMMC, parent:pid, deleted:DEL |
| BGGL_ZCJYP_CLJY | 83 | candidate_secondary_business_fact | 45 | date:SJBMC/SQRQ/SYSJ_S/SYSJ_E, project:XMID/XMMC, parent:pid, deleted:DEL |
| CWGL_DZFPK | 79 | candidate_secondary_business_fact | 45 | date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:Del |
| T_Base_BuildMaterial_XGJL | 76 | candidate_secondary_business_fact | 45 | date:SJBMC/XGSJ, project:XMID, parent:pid |

## Top Candidate Families

| Family | Tables | Rows | Effective Tables | Top Tables |
|---|---:|---:|---:|---|
| pm | 4 | 21693 | 0 | Pm_Person_Department_PDuty(102), Pm_Person_Department(786), Pm_base_Person_RYXQSQ(1), PM_RYYDGL(20804) |
| t | 38 | 16551 | 0 | T_Base_DBDW(754), T_Base_LLDWAndLWDW(91), T_Base_LLDWAndFBDW(15), T_Base_CooperatCompany_Account(8008), T_Base_ConstructPlaceDetail(1620) |
| cgpt | 4 | 9516 | 0 | CGPT_T_Base_SupplierUser(1), CGPT_Base_JCCLK(9499), CGPT_T_Base_CGGGLXSZ(15), CGPT_T_Base_HZDWKC_JX(1) |
| office_admin | 27 | 3811 | 0 | BGGL_TZXX_WJHQ(2076), BGGL_KQTJ_YTWC(1137), BGGL_XZ_BZ_CB(77), BGGL_QSJRW_GZQS_CB(43), BGGL_QSJRW_GZQS_HF(28) |
| sgbw | 1 | 1439 | 0 | SGBW_QDKM(1439) |
| sggl | 17 | 987 | 0 | SGGL_Node_Abarbeitung(16), SGGL_Bar_ConstructionPlan_CB_Task(869), SGGL_JBXXGL_SPJHQK(1), SGGL_Base_SGRZ_SGLH_Set(9), SGGL_Base_AQSGRQ_GSLPHP(7) |
| a | 1 | 716 | 0 | A_HistoryRecord(716) |
| cwgl | 4 | 422 | 0 | CWGL_FYBX_SKDW(1), CWGL_SQGL_CCSQ(177), CWGL_DZFPK(79), CWGL_SQGL_CCSQ_CB(165) |
| gzgl | 1 | 389 | 0 | GZGL_BMSJWH(389) |
| jhjrz | 4 | 341 | 0 | JHJRZ_FBRW_CB(96), JHJRZ_FBRW(31), JHJRZ_FBRW_BLXQ(9), JHJRZ_RWCKJLB(205) |
| dataspider | 2 | 250 | 0 | DataSpider_ScjstPersonInfo(54), DataSpider_ScjstPersonCertificate(196) |
| zlgl | 2 | 177 | 0 | ZLGL_Base_ZLLXAndQX(156), ZLGL_Base_ZLLX_New(21) |
| xmgl | 5 | 159 | 0 | XMGL_SRHT_QTSRHT_CB(8), XMGL_WZGL_CKGL_YFD_CB(2), XMGL_JSJSH_SH_SHWZSQD(1), XMGL_YSZJ_FXB_CLCBFXB(1), XMGL_LYGL_LYRY(147) |
| base | 1 | 125 | 0 | BASE_APP_COMMONOLDUSER(125) |
| d | 5 | 61 | 0 | D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS_CB(53), D_SCBSJS_SW_JC_GSPTFP_CB(3), D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS(3), D_BYK_ZZXT_HBZJ_QSJRW_RWFB(1), D_SCBSJS_SW_JC_GSPTFP(1) |
| zyjx | 12 | 48 | 0 | ZYJX_ZY_T_SBZLJC_SBWZSQ_CB(12), ZYJX_ZY_T_CG_CGSQ_CB(6), ZYJX_ZY_T_SBZLJC_SBZLRK_CB(1), ZYJX_ZY_T_CG_CGSQ(15), ZYJX_ZY_T_SBJC_SBRK(2) |
| gdzc | 1 | 46 | 0 | GDZC_WXZC(46) |
| invoice | 1 | 21 | 0 | Invoice_CB(21) |
| wz | 1 | 21 | 0 | WZ_Base_GYSBJ_CB(21) |
| other | 1 | 14 | 0 | Invoice(14) |

## Boundary

- Read-only legacy DB scan
- DB writes: `0`
- This is a table/column signal screen; every candidate still needs lane-level SQL and replay mapping before ingestion.

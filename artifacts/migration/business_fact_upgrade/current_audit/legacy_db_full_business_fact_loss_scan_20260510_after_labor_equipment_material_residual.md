# Legacy DB Full Business Fact Loss Scan v1

Status: `PASS`

Source: `legacy-mssql-restore:LegacyDb`

## Summary

```json
{
  "total_tables": 4312,
  "non_empty_tables": 1128,
  "candidate_tables": 253,
  "candidate_rows": 68931,
  "classification_counts": {
    "known_replayed_or_assetized": 245,
    "system_or_audit_noise": 362,
    "candidate_needs_manual_screen": 8,
    "reference_or_import_catalog": 489,
    "low_business_fact_signal": 2963,
    "candidate_secondary_business_fact": 143,
    "candidate_effective_business_fact": 102
  },
  "classification_row_counts": {
    "known_replayed_or_assetized": 3726297,
    "system_or_audit_noise": 1245813,
    "candidate_needs_manual_screen": 22997,
    "reference_or_import_catalog": 2518257,
    "low_business_fact_signal": 19746,
    "candidate_secondary_business_fact": 33841,
    "candidate_effective_business_fact": 12093
  },
  "top_candidate_families": [
    {
      "family": "pm",
      "tables": 5,
      "rows": 21773,
      "effective_tables": 1,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "Pm_base_Person",
          "rows": 80,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
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
      "tables": 55,
      "rows": 19142,
      "effective_tables": 17,
      "secondary_tables": 37,
      "top_tables": [
        {
          "table": "T_SC_SCD",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_Base_NKCLKMSZ",
          "rows": 856,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_Base_NKFBKMSZ",
          "rows": 18,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_Base_NKGZKMSZ",
          "rows": 11,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_CGJH_CGNJH",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_CGJH_CGNJH_CB",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_CGJH_CGZJH",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_CGJH_CGZJH_CB",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_CGJH_CGYJH",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_CGJH_CGYJH_CB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        }
      ]
    },
    {
      "family": "cgpt",
      "tables": 7,
      "rows": 9519,
      "effective_tables": 3,
      "secondary_tables": 4,
      "top_tables": [
        {
          "table": "CGPT_T_Base_HZDWKC_CL",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGPT_T_Base_HZDWKC_LW",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGPT_T_Base_HZDWKC_FB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
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
      "tables": 37,
      "rows": 5657,
      "effective_tables": 10,
      "secondary_tables": 27,
      "top_tables": [
        {
          "table": "BGGL_QT_HTHS",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "BGGL_XZ_BZ",
          "rows": 115,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BGGL_HBZJ_GZZB",
          "rows": 90,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BGGL_HBZJ_QT_GCBXGMJL",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BGGL_QT_GCBGTZD",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BGGL_BMYS_BMQTZCDJ",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BGGL_TZXX_WJPYCJ",
          "rows": 1616,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "BGGL_JHK_HKDJ_CB",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "BGGL_QT_YZWGYJGLB",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "BGGL_ZCJYP_CL_SCGYFCDJ",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 65
        }
      ]
    },
    {
      "family": "base",
      "tables": 3,
      "rows": 5044,
      "effective_tables": 2,
      "secondary_tables": 0,
      "top_tables": [
        {
          "table": "BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER",
          "rows": 4915,
          "classification": "candidate_effective_business_fact",
          "score": 80
        },
        {
          "table": "BASE_SYSTEM_WZCLKGXSZ",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BASE_APP_COMMONOLDUSER",
          "rows": 125,
          "classification": "candidate_needs_manual_screen",
          "score": 20
        }
      ]
    },
    {
      "family": "zlgl",
      "tables": 3,
      "rows": 1994,
      "effective_tables": 1,
      "secondary_tables": 2,
      "top_tables": [
        {
          "table": "ZLGL_Base_DataManager",
          "rows": 1817,
          "classification": "candidate_effective_business_fact",
          "score": 80
        },
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
      "tables": 32,
      "rows": 1172,
      "effective_tables": 15,
      "secondary_tables": 17,
      "top_tables": [
        {
          "table": "SGGL_HJJC_HJCF",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "SGGL_JBXXGL",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 85
        },
        {
          "table": "SGGL_DataTypeSet",
          "rows": 35,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_Node",
          "rows": 25,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_GCJBQKB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_GCJBQKB_LD",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_Base_SGRZ",
          "rows": 52,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_Bar_ConstructionPlan",
          "rows": 39,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_Node_Abarbeitung",
          "rows": 16,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_Bar_ConstructionProgressReport",
          "rows": 13,
          "classification": "candidate_effective_business_fact",
          "score": 65
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
      "family": "dataspider",
      "tables": 3,
      "rows": 469,
      "effective_tables": 1,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "DataSpider_ScjstProjectRoughInfo",
          "rows": 219,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
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
      "family": "cwgl",
      "tables": 6,
      "rows": 432,
      "effective_tables": 2,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "CWGL_CLBX_CB",
          "rows": 8,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "CWGL_CLBX",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
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
      "tables": 5,
      "rows": 344,
      "effective_tables": 1,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "JHJRZ_GZHB",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
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
      "family": "d",
      "tables": 8,
      "rows": 231,
      "effective_tables": 3,
      "secondary_tables": 5,
      "top_tables": [
        {
          "table": "D_SCBSJS_BGGL_XZ_SBRY",
          "rows": 167,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "D_HLCSXT_T_CollectionPlan_New_CB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "D_YWXT_XM_SGGL_SGZLGL_JGZL",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
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
      "family": "xmgl",
      "tables": 14,
      "rows": 182,
      "effective_tables": 9,
      "secondary_tables": 4,
      "top_tables": [
        {
          "table": "XMGL_SRHT_QTSRHT",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "XMGL_JJSB_ZLJH_JXYGSQ",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "XMGL_RKGL_SHLQYSD_CB",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "XMGL_RKGL_YSD_CB",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "XMGL_JJSB_ZLJH_JXYGSQ_CB",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "XMGL_RKGL_SHLQYSD",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XMGL_RKGL_YSD",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XMGL_WZGL_CKGL_YFD",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XMGL_LYGL_LYXM",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XMGL_SRHT_QTSRHT_CB",
          "rows": 8,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    },
    {
      "family": "project_settlement",
      "tables": 6,
      "rows": 74,
      "effective_tables": 5,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "T_ProjectContract_In",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 105
        },
        {
          "table": "XMGL_HTGL_XMJSSQ",
          "rows": 55,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_Project_GCQZD",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "XM_SBBF",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_ProjectContract_Process",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "T_ProjectContract_Out_CB_BZJ",
          "rows": 5,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    },
    {
      "family": "xm",
      "tables": 8,
      "rows": 52,
      "effective_tables": 6,
      "secondary_tables": 2,
      "top_tables": [
        {
          "table": "XM_SBZJ_CB",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "XM_SBRC",
          "rows": 20,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XM_SBSY",
          "rows": 10,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XM_SBGH",
          "rows": 7,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XM_SBZY",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XM_SBWX",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "XM_SBDL",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "XM_SBZJ_ZB",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "zyjx",
      "tables": 13,
      "rows": 49,
      "effective_tables": 1,
      "secondary_tables": 12,
      "top_tables": [
        {
          "table": "ZYJX_ZY_T_SBZLJC_SBZLRK",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
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
      "family": "yszj",
      "tables": 4,
      "rows": 43,
      "effective_tables": 3,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "YSZJ_CZBS_CZQDBS",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 115
        },
        {
          "table": "YSZJ_XMCZ_GCBGTZ",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 85
        },
        {
          "table": "YSZJ_CZBS_CZQDBS_CB_CB",
          "rows": 34,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "YSZJ_CZBS_CZQDBS_CB",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    }
  ],
  "top_candidates": [
    {
      "schema": "dbo",
      "table": "YSZJ_CZBS_CZQDBS",
      "row_count": 4,
      "column_count": 41,
      "classification": "candidate_effective_business_fact",
      "family": "yszj",
      "business_signal_score": 115,
      "signals": {
        "amount": [
          "BCJFSDHSE",
          "LJSDHSE"
        ],
        "date": [
          "SJBMC",
          "TBRQ",
          "LRSJ",
          "XGSJ",
          "SJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDW"
        ],
        "contract": [
          "HTMC"
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
      "table": "T_ProjectContract_In",
      "row_count": 4,
      "column_count": 98,
      "classification": "candidate_effective_business_fact",
      "family": "project_settlement",
      "business_signal_score": 105,
      "signals": {
        "amount": [
          "f_LRJE",
          "f_FXJDYJE",
          "HTJE"
        ],
        "date": [
          "SJBMC",
          "f_KGRQ",
          "f_MBZRSQDRQ",
          "f_SJLR",
          "f_DYDWRQ",
          "f_LRSJ",
          "f_SJDWJDH",
          "f_SJ",
          "XGRQ",
          "SCRQ",
          "XGSJ"
        ],
        "project": [
          "XMID"
        ],
        "partner": [
          "f_JSDW"
        ],
        "contract": [
          "f_NBHTBH",
          "f_NBHTBHZDY"
        ],
        "deleted": [
          "SCRID",
          "SCRQ",
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "XMGL_HTGL_XMJSSQ",
      "row_count": 55,
      "column_count": 36,
      "classification": "candidate_effective_business_fact",
      "family": "project_settlement",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "YSKJE",
          "JSJE",
          "HTJE"
        ],
        "date": [
          "SJBMC",
          "JSJE",
          "JSRQ",
          "LRSJ",
          "XGSJ",
          "JSJD",
          "D_JCLY_JSJDID"
        ],
        "project": [
          "XMID",
          "XMMC",
          "D_JCLY_LXXMMC",
          "D_JCLY_LXXMMCID"
        ],
        "contract": [
          "ZBHTID",
          "ZBHTBH"
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
      "table": "T_Project_GCQZD",
      "row_count": 6,
      "column_count": 26,
      "classification": "candidate_effective_business_fact",
      "family": "project_settlement",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "SJJE"
        ],
        "date": [
          "SJBMC",
          "SJ",
          "SJJE",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDWID",
          "JSDW",
          "JLDWID"
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
      "table": "XMGL_SRHT_QTSRHT",
      "row_count": 6,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "xmgl",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "SSJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "SSJE",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "GMDWID"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_SC_SCD",
      "row_count": 4,
      "column_count": 40,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "CPJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "YLLLDWID",
          "CPRKDWID",
          "CPJSDWID",
          "CPJSDWMC"
        ],
        "parent": [
          "Pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_QT_HTHS",
      "row_count": 3,
      "column_count": 30,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "HTJE"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "contract": [
          "HTBH",
          "HTMC"
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
      "table": "WS_ZJJLTZ_ZFTZ",
      "row_count": 3,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "ws",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZFJE",
          "KHBLKJE",
          "FPJE"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ",
          "ZFRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "SGDWID"
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
      "table": "XM_SBBF",
      "row_count": 3,
      "column_count": 31,
      "classification": "candidate_effective_business_fact",
      "family": "project_settlement",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "BFTBJE"
        ],
        "date": [
          "SJBMC",
          "BFRQ",
          "LRSJ",
          "XGRQ",
          "SCRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDWID",
          "JSDW"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "SCRID",
          "SCRQ",
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGGL_HJJC_HJCF",
      "row_count": 2,
      "column_count": 29,
      "classification": "candidate_effective_business_fact",
      "family": "sggl",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "CFJE"
        ],
        "date": [
          "SJBMC",
          "CFSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "BCFDWID"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CGPT_T_Base_HZDWKC_CL",
      "row_count": 1,
      "column_count": 63,
      "classification": "candidate_effective_business_fact",
      "family": "cgpt",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "T_Base_SupplierInfo_ID"
        ],
        "date": [
          "SJBMC",
          "KCRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMMC",
          "XMID"
        ],
        "partner": [
          "T_Base_SupplierInfo_ID"
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
      "table": "CGPT_T_Base_HZDWKC_LW",
      "row_count": 1,
      "column_count": 63,
      "classification": "candidate_effective_business_fact",
      "family": "cgpt",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "LW_Base_LWDWSZ_ID"
        ],
        "date": [
          "SJBMC",
          "KCRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMMC",
          "XMID"
        ],
        "partner": [
          "LWFBFWZL",
          "LWFBFWZL_1",
          "LWFBFWZL_2"
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
      "table": "P_ZTB_GCJCGL",
      "row_count": 1,
      "column_count": 67,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "D_DCYL_YSJE"
        ],
        "date": [
          "SJBMC",
          "f_ZBBMSJ",
          "f_TBJZSJ",
          "f_KBSJ",
          "f_JHKGSJ",
          "f_ZBGSSJ",
          "f_LRSJ",
          "f_JNJZSJ",
          "f_THJZRQ",
          "XGRQ",
          "SCRQ",
          "GLSJID"
        ],
        "project": [
          "XMID"
        ],
        "partner": [
          "f_JSDW",
          "ZBDWID"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "SCRID",
          "SCRQ",
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "WS_HTGL_HTBG",
      "row_count": 1,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "ws",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "WS_HTGL_ZBHT_JE",
          "JEBG"
        ],
        "date": [
          "SJBMC",
          "QYRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "contract": [
          "HTBH"
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
      "table": "SGGL_JBXXGL",
      "row_count": 2,
      "column_count": 46,
      "classification": "candidate_effective_business_fact",
      "family": "sggl",
      "business_signal_score": 85,
      "signals": {
        "date": [
          "SJBMC",
          "JHJGRQ",
          "SJKGRQ",
          "LRSJ",
          "GCKGRQ",
          "ZBRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDW"
        ],
        "contract": [
          "HTBH"
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
      "table": "YSZJ_XMCZ_GCBGTZ",
      "row_count": 1,
      "column_count": 26,
      "classification": "candidate_effective_business_fact",
      "family": "yszj",
      "business_signal_score": 85,
      "signals": {
        "date": [
          "SJBMC",
          "FQSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "FQDWID"
        ],
        "contract": [
          "HTBH"
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
      "table": "BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER",
      "row_count": 4915,
      "column_count": 20,
      "classification": "candidate_effective_business_fact",
      "family": "base",
      "business_signal_score": 80,
      "signals": {
        "amount": [
          "USERID",
          "USERNAME"
        ],
        "date": [
          "RZRQ",
          "ISJZ",
          "SYNC_GROUP_DATE"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "ZLGL_Base_DataManager",
      "row_count": 1817,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "zlgl",
      "business_signal_score": 80,
      "signals": {
        "amount": [
          "ZLGL_Base_ZLLX_Id",
          "ZLGL_Base_ZLLX_Name"
        ],
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
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_NKCLKMSZ",
      "row_count": 856,
      "column_count": 22,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "SFJEKZ"
        ],
        "date": [
          "SJBMC",
          "CLSJGUID",
          "CLSJCODE",
          "CLSJMC",
          "CLSJGGXH",
          "CLSJDW"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "DataSpider_ScjstProjectRoughInfo",
      "row_count": 219,
      "column_count": 22,
      "classification": "candidate_effective_business_fact",
      "family": "dataspider",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ProjectRoles",
          "ProjectNumber",
          "ProjectName",
          "ScjstProjectInfoId",
          "ProjectAddress"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "ProjectRoles",
          "ProjectNumber",
          "ProjectName",
          "ScjstProjectInfoId",
          "ProjectAddress"
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
      "table": "D_SCBSJS_BGGL_XZ_SBRY",
      "row_count": 167,
      "column_count": 32,
      "classification": "candidate_effective_business_fact",
      "family": "d",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YLJE",
          "SYJE",
          "GSJE"
        ],
        "date": [
          "DJRQ",
          "LRSJ",
          "XGSJ",
          "GSJE"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_XZ_BZ",
      "row_count": 115,
      "column_count": 25,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
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
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_HBZJ_GZZB",
      "row_count": 90,
      "column_count": 39,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "Userid"
        ],
        "date": [
          "SJBMC",
          "Star_RQ",
          "End_RQ",
          "LRSJ",
          "XGSJ",
          "ZBRQStart",
          "ZBRQEnd"
        ],
        "project": [
          "XMMC",
          "XMID"
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
      "table": "Pm_base_Person",
      "row_count": 80,
      "column_count": 67,
      "classification": "candidate_effective_business_fact",
      "family": "pm",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "IsProjectPerson",
          "IsBuySecurity",
          "UseridOther"
        ],
        "date": [
          "SJBMC",
          "RDSJ",
          "CJGZSJ",
          "BYSJ",
          "LRSJ",
          "WX_SCSJ",
          "CSRQ",
          "SJH",
          "GMRQ"
        ],
        "project": [
          "IsProjectPerson"
        ],
        "parent": [
          "FaceBillId"
        ],
        "deleted": [
          "Del",
          "WX_SCRID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGGL_DataTypeSet",
      "row_count": 35,
      "column_count": 16,
      "classification": "candidate_effective_business_fact",
      "family": "sggl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName"
        ],
        "date": [
          "SJBMC",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "parentId"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "YSZJ_CZBS_CZQDBS_CB_CB",
      "row_count": 34,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "yszj",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "BSJE",
          "HDJE",
          "LJJE"
        ],
        "date": [
          "SJBMC",
          "BSJE"
        ],
        "project": [
          "QDXMMC"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "SGGL_Node",
      "row_count": 25,
      "column_count": 17,
      "classification": "candidate_effective_business_fact",
      "family": "sggl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName"
        ],
        "date": [
          "SJBMC",
          "startDate",
          "endDate",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "parentId"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_NKFBKMSZ",
      "row_count": 18,
      "column_count": 20,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "SFJEKZ"
        ],
        "date": [
          "SJBMC",
          "FBSJGUID"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "PJ_Type_MB",
      "row_count": 16,
      "column_count": 16,
      "classification": "candidate_effective_business_fact",
      "family": "pj",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName"
        ],
        "date": [
          "SJBMC",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "parentId"
        ],
        "deleted": [
          "isDelete"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "XMGL_JJSB_ZLD_LXYG_CB",
      "row_count": 12,
      "column_count": 33,
      "classification": "candidate_effective_business_fact",
      "family": "lease_equipment",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE",
          "JE_NO",
          "SE"
        ],
        "date": [
          "SJBMC",
          "RQ",
          "QZSJ_KS",
          "QZSJ_JZ",
          "GZSJ"
        ],
        "project": [
          "XMMC"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_NKGZKMSZ",
      "row_count": 11,
      "column_count": 21,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "SFJEKZ"
        ],
        "date": [
          "SJBMC",
          "GZSJGUID"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CWGL_CLBX_CB",
      "row_count": 8,
      "column_count": 32,
      "classification": "candidate_effective_business_fact",
      "family": "cwgl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JTFJE",
          "CCJE"
        ],
        "date": [
          "SJBMC",
          "QSSJ",
          "JSSJ",
          "D_JCLY_CCSJ",
          "D_JCLY_JSSJ"
        ],
        "project": [
          "CCXMMC"
        ],
        "parent": [
          "pid",
          "ZBID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "PJ_Content",
      "row_count": 7,
      "column_count": 17,
      "classification": "candidate_effective_business_fact",
      "family": "pj",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "inBillMoney",
          "outBillMoney",
          "createUserID",
          "createUserName"
        ],
        "date": [
          "SJBMC",
          "billDate",
          "createUserID",
          "createUserName",
          "createDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "billId"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGOA_BGYPSQ",
      "row_count": 6,
      "column_count": 29,
      "classification": "candidate_effective_business_fact",
      "family": "bgoa",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YGZJE",
          "DXJE"
        ],
        "date": [
          "SJBMC",
          "SQRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "PJ_Type",
      "row_count": 6,
      "column_count": 15,
      "classification": "candidate_effective_business_fact",
      "family": "pj",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName"
        ],
        "date": [
          "SJBMC",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "parentId"
        ],
        "deleted": [
          "isDelete"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BASE_SYSTEM_WZCLKGXSZ",
      "row_count": 4,
      "column_count": 17,
      "classification": "candidate_effective_business_fact",
      "family": "base",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "SETTINGTYPE"
        ],
        "date": [
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "PID"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_HBZJ_QT_GCBXGMJL",
      "row_count": 4,
      "column_count": 26,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "BXJE"
        ],
        "date": [
          "SJBMC",
          "GMSJ",
          "BXSXSJ",
          "BXDQSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMMC",
          "XMID"
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
      "table": "JHJRZ_GZHB",
      "row_count": 3,
      "column_count": 38,
      "classification": "candidate_effective_business_fact",
      "family": "jhjrz",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "Userid"
        ],
        "date": [
          "SJBMC",
          "Star_RQ",
          "End_RQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMMC",
          "XMID"
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
      "table": "T_CGJH_CGNJH",
      "row_count": 3,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
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
      "table": "T_CGJH_CGNJH_CB",
      "row_count": 3,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "JCSJ"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_CGJH_CGZJH",
      "row_count": 3,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
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
      "table": "T_CGJH_CGZJH_CB",
      "row_count": 3,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "JCSJ"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_QT_GCBGTZD",
      "row_count": 2,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YGBGJE"
        ],
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
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CWGL_CLBX",
      "row_count": 2,
      "column_count": 46,
      "classification": "candidate_effective_business_fact",
      "family": "cwgl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "BXJE",
          "SBJE",
          "DXJE"
        ],
        "date": [
          "SJBMC",
          "TBRQ",
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
      "table": "T_CGJH_CGYJH",
      "row_count": 2,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
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
      "table": "XMGL_JJSB_ZLJH_JXYGSQ",
      "row_count": 2,
      "column_count": 27,
      "classification": "candidate_effective_business_fact",
      "family": "xmgl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "createUserID",
          "GZZJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "LRSJ",
          "XGSJ",
          "createUserID",
          "DCSJ"
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
      "table": "XMGL_RKGL_SHLQYSD_CB",
      "row_count": 2,
      "column_count": 15,
      "classification": "candidate_effective_business_fact",
      "family": "xmgl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "XMGL_RKGL_YSD_CB",
      "row_count": 2,
      "column_count": 15,
      "classification": "candidate_effective_business_fact",
      "family": "xmgl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "BGGL_BMYS_BMQTZCDJ",
      "row_count": 1,
      "column_count": 27,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ZCJE",
          "PJJE",
          "DXJE"
        ],
        "date": [
          "SJBMC",
          "ZCSJ",
          "YSSJD",
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
      "table": "CDJX_PCD_QCPCD",
      "row_count": 1,
      "column_count": 40,
      "classification": "candidate_effective_business_fact",
      "family": "cdjx",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YFJE"
        ],
        "date": [
          "SJBMC",
          "SJ",
          "ZHSJ",
          "XHSJ",
          "SHRQZ",
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
      "table": "CDJX_ZYQD_DGJDZQD",
      "row_count": 1,
      "column_count": 32,
      "classification": "candidate_effective_business_fact",
      "family": "cdjx",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "RQ",
          "KGSJ",
          "JGSJ",
          "SJ",
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
      "table": "CDJX_ZYQD_DGJYZQD",
      "row_count": 1,
      "column_count": 40,
      "classification": "candidate_effective_business_fact",
      "family": "cdjx",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YSJE",
          "ZCJE",
          "XCJE",
          "HJJE"
        ],
        "date": [
          "SJBMC",
          "RQ",
          "YSSJ_Start",
          "YSSJ_End",
          "YSJE",
          "SJ",
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
      "table": "CDJX_ZYQD_QZJDZQD",
      "row_count": 1,
      "column_count": 27,
      "classification": "candidate_effective_business_fact",
      "family": "cdjx",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "ZYSJ",
          "YFSJQZ",
          "JFJBRQZ",
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
      "table": "SGGL_GCJBQKB",
      "row_count": 1,
      "column_count": 52,
      "classification": "candidate_effective_business_fact",
      "family": "sggl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YJSFKJE",
          "JGCJE"
        ],
        "date": [
          "SJBMC",
          "TBRQ",
          "SJKGRQ",
          "SJQRCZ",
          "YJZJLRQK",
          "YJZLRQK",
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
      "table": "SGGL_GCJBQKB_LD",
      "row_count": 1,
      "column_count": 51,
      "classification": "candidate_effective_business_fact",
      "family": "sggl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YJSFKJE",
          "JGCJE"
        ],
        "date": [
          "SJBMC",
          "TBRQ",
          "SJKGRQ",
          "SJQRCZ",
          "YJZJLRQK",
          "YJZLRQK",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_CGJH_CGYJH_CB",
      "row_count": 1,
      "column_count": 20,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "JCSJ"
        ],
        "project": [
          "XMID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "WS_HTGL_HTJS",
      "row_count": 1,
      "column_count": 22,
      "classification": "candidate_effective_business_fact",
      "family": "ws",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "YHTJE",
          "BGJE",
          "JSJE"
        ],
        "date": [
          "SJBMC",
          "JSRQ",
          "JSJE",
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
      "table": "WS_HTGL_JSBG",
      "row_count": 1,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "ws",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "WS_HTGL_HTJS_JE",
          "WS_HTGL_HTBG_JE",
          "WS_HTGL_ZBHT_JE",
          "BGJE"
        ],
        "date": [
          "SJBMC",
          "BGRQ",
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
      "table": "ZJSZ_ZJJH_ZJSYJH_HA",
      "row_count": 1,
      "column_count": 31,
      "classification": "candidate_effective_business_fact",
      "family": "zjsz",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "HTJE",
          "DQKYZJJE"
        ],
        "date": [
          "SJBMC",
          "GSJHQDZJ",
          "ZJHLSJ",
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
      "table": "BGGL_TZXX_WJPYCJ",
      "row_count": 1616,
      "column_count": 31,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 70,
      "signals": {
        "date": [
          "SJBMC",
          "DJRQ",
          "LRSJ",
          "XGSJ",
          "DBYQWCSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "SSDWID"
        ],
        "parent": [
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    }
  ]
}
```

## Top Candidate Tables

| Table | Rows | Classification | Score | Signals |
|---|---:|---|---:|---|
| YSZJ_CZBS_CZQDBS | 4 | candidate_effective_business_fact | 115 | amount:BCJFSDHSE/LJSDHSE, date:SJBMC/TBRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:JSDW, contract:HTMC, parent:pid, deleted:DEL |
| T_ProjectContract_In | 4 | candidate_effective_business_fact | 105 | amount:f_LRJE/f_FXJDYJE/HTJE, date:SJBMC/f_KGRQ/f_MBZRSQDRQ/f_SJLR, project:XMID, partner:f_JSDW, contract:f_NBHTBH/f_NBHTBHZDY, deleted:SCRID/SCRQ/DEL |
| XMGL_HTGL_XMJSSQ | 55 | candidate_effective_business_fact | 95 | amount:YSKJE/JSJE/HTJE, date:SJBMC/JSJE/JSRQ/LRSJ, project:XMID/XMMC/D_JCLY_LXXMMC/D_JCLY_LXXMMCID, contract:ZBHTID/ZBHTBH, parent:pid, deleted:DEL |
| T_Project_GCQZD | 6 | candidate_effective_business_fact | 95 | amount:SJJE, date:SJBMC/SJ/SJJE/LRSJ, project:XMID/XMMC, partner:JSDWID/JSDW/JLDWID, parent:pid, deleted:DEL |
| XMGL_SRHT_QTSRHT | 6 | candidate_effective_business_fact | 95 | amount:SSJE, date:SJBMC/DJRQ/SSJE/LRSJ, project:XMID/XMMC, partner:GMDWID, parent:PID, deleted:DEL |
| T_SC_SCD | 4 | candidate_effective_business_fact | 95 | amount:CPJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:YLLLDWID/CPRKDWID/CPJSDWID/CPJSDWMC, parent:Pid, deleted:DEL |
| BGGL_QT_HTHS | 3 | candidate_effective_business_fact | 95 | amount:HTJE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, contract:HTBH/HTMC, parent:pid, deleted:DEL |
| WS_ZJJLTZ_ZFTZ | 3 | candidate_effective_business_fact | 95 | amount:ZFJE/KHBLKJE/FPJE, date:SJBMC/LRSJ/XGSJ/ZFRQ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| XM_SBBF | 3 | candidate_effective_business_fact | 95 | amount:BFTBJE, date:SJBMC/BFRQ/LRSJ/XGRQ, project:XMID/XMMC, partner:JSDWID/JSDW, parent:pid, deleted:SCRID/SCRQ/DEL |
| SGGL_HJJC_HJCF | 2 | candidate_effective_business_fact | 95 | amount:CFJE, date:SJBMC/CFSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:BCFDWID, parent:pid |
| CGPT_T_Base_HZDWKC_CL | 1 | candidate_effective_business_fact | 95 | amount:T_Base_SupplierInfo_ID, date:SJBMC/KCRQ/LRSJ/XGSJ, project:XMMC/XMID, partner:T_Base_SupplierInfo_ID, parent:pid, deleted:DEL |
| CGPT_T_Base_HZDWKC_LW | 1 | candidate_effective_business_fact | 95 | amount:LW_Base_LWDWSZ_ID, date:SJBMC/KCRQ/LRSJ/XGSJ, project:XMMC/XMID, partner:LWFBFWZL/LWFBFWZL_1/LWFBFWZL_2, parent:pid, deleted:DEL |
| P_ZTB_GCJCGL | 1 | candidate_effective_business_fact | 95 | amount:D_DCYL_YSJE, date:SJBMC/f_ZBBMSJ/f_TBJZSJ/f_KBSJ, project:XMID, partner:f_JSDW/ZBDWID, parent:PID, deleted:SCRID/SCRQ/DEL |
| WS_HTGL_HTBG | 1 | candidate_effective_business_fact | 95 | amount:WS_HTGL_ZBHT_JE/JEBG, date:SJBMC/QYRQ/LRSJ/XGSJ, project:XMID/XMMC, contract:HTBH, parent:pid, deleted:DEL |
| SGGL_JBXXGL | 2 | candidate_effective_business_fact | 85 | date:SJBMC/JHJGRQ/SJKGRQ/LRSJ, project:XMID/XMMC, partner:JSDW, contract:HTBH, parent:pid, deleted:DEL |
| YSZJ_XMCZ_GCBGTZ | 1 | candidate_effective_business_fact | 85 | date:SJBMC/FQSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:FQDWID, contract:HTBH, parent:pid, deleted:DEL |
| BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER | 4915 | candidate_effective_business_fact | 80 | amount:USERID/USERNAME, date:RZRQ/ISJZ/SYNC_GROUP_DATE, project:XMID, parent:PID, deleted:DEL |
| ZLGL_Base_DataManager | 1817 | candidate_effective_business_fact | 80 | amount:ZLGL_Base_ZLLX_Id/ZLGL_Base_ZLLX_Name, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_Base_NKCLKMSZ | 856 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/CLSJGUID/CLSJCODE/CLSJMC, project:XMID/XMMC, parent:pid |
| DataSpider_ScjstProjectRoughInfo | 219 | candidate_effective_business_fact | 75 | amount:ProjectRoles/ProjectNumber/ProjectName/ScjstProjectInfoId, date:SJBMC/LRSJ/XGSJ, project:ProjectRoles/ProjectNumber/ProjectName/ScjstProjectInfoId, parent:pid, deleted:del |
| D_SCBSJS_BGGL_XZ_SBRY | 167 | candidate_effective_business_fact | 75 | amount:YLJE/SYJE/GSJE, date:DJRQ/LRSJ/XGSJ/GSJE, project:XMID/XMMC, parent:PID, deleted:DEL |
| BGGL_XZ_BZ | 115 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| BGGL_HBZJ_GZZB | 90 | candidate_effective_business_fact | 75 | amount:Userid, date:SJBMC/Star_RQ/End_RQ/LRSJ, project:XMMC/XMID, parent:pid, deleted:DEL |
| Pm_base_Person | 80 | candidate_effective_business_fact | 75 | amount:IsProjectPerson/IsBuySecurity/UseridOther, date:SJBMC/RDSJ/CJGZSJ/BYSJ, project:IsProjectPerson, parent:FaceBillId, deleted:Del/WX_SCRID |
| SGGL_DataTypeSet | 35 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId |
| YSZJ_CZBS_CZQDBS_CB_CB | 34 | candidate_effective_business_fact | 75 | amount:BSJE/HDJE/LJJE, date:SJBMC/BSJE, project:QDXMMC, parent:pid |
| SGGL_Node | 25 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/startDate/endDate/createUserID, project:XMID/XMMC, parent:parentId |
| T_Base_NKFBKMSZ | 18 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/FBSJGUID, project:XMID/XMMC, parent:pid |
| PJ_Type_MB | 16 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete |
| XMGL_JJSB_ZLD_LXYG_CB | 12 | candidate_effective_business_fact | 75 | amount:JE/JE_NO/SE, date:SJBMC/RQ/QZSJ_KS/QZSJ_JZ, project:XMMC, parent:ZBID/pid |
| T_Base_NKGZKMSZ | 11 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/GZSJGUID, project:XMID/XMMC, parent:pid |
| CWGL_CLBX_CB | 8 | candidate_effective_business_fact | 75 | amount:JTFJE/CCJE, date:SJBMC/QSSJ/JSSJ/D_JCLY_CCSJ, project:CCXMMC, parent:pid/ZBID |
| PJ_Content | 7 | candidate_effective_business_fact | 75 | amount:inBillMoney/outBillMoney/createUserID/createUserName, date:SJBMC/billDate/createUserID/createUserName, project:XMID/XMMC, parent:billId, deleted:DEL |
| BGOA_BGYPSQ | 6 | candidate_effective_business_fact | 75 | amount:YGZJE/DXJE, date:SJBMC/SQRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:PID, deleted:DEL |
| PJ_Type | 6 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete |
| BASE_SYSTEM_WZCLKGXSZ | 4 | candidate_effective_business_fact | 75 | amount:SETTINGTYPE, date:LRSJ/XGSJ, project:XMID/XMMC, parent:PID, deleted:DEL |
| BGGL_HBZJ_QT_GCBXGMJL | 4 | candidate_effective_business_fact | 75 | amount:BXJE, date:SJBMC/GMSJ/BXSXSJ/BXDQSJ, project:XMMC/XMID, parent:pid, deleted:DEL |
| JHJRZ_GZHB | 3 | candidate_effective_business_fact | 75 | amount:Userid, date:SJBMC/Star_RQ/End_RQ/LRSJ, project:XMMC/XMID, parent:pid, deleted:DEL |
| T_CGJH_CGNJH | 3 | candidate_effective_business_fact | 75 | amount:ZJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_CGJH_CGNJH_CB | 3 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/JCSJ, project:XMID, parent:ZBID/pid |
| T_CGJH_CGZJH | 3 | candidate_effective_business_fact | 75 | amount:ZJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_CGJH_CGZJH_CB | 3 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/JCSJ, project:XMID, parent:ZBID/pid |
| BGGL_QT_GCBGTZD | 2 | candidate_effective_business_fact | 75 | amount:YGBGJE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| CWGL_CLBX | 2 | candidate_effective_business_fact | 75 | amount:BXJE/SBJE/DXJE, date:SJBMC/TBRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_CGJH_CGYJH | 2 | candidate_effective_business_fact | 75 | amount:ZJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| XMGL_JJSB_ZLJH_JXYGSQ | 2 | candidate_effective_business_fact | 75 | amount:createUserID/GZZJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| XMGL_RKGL_SHLQYSD_CB | 2 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC, project:XMID, parent:ZBID/pid |
| XMGL_RKGL_YSD_CB | 2 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC, project:XMID, parent:ZBID/pid |
| BGGL_BMYS_BMQTZCDJ | 1 | candidate_effective_business_fact | 75 | amount:ZCJE/PJJE/DXJE, date:SJBMC/ZCSJ/YSSJD/LRSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| CDJX_PCD_QCPCD | 1 | candidate_effective_business_fact | 75 | amount:YFJE, date:SJBMC/SJ/ZHSJ/XHSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| CDJX_ZYQD_DGJDZQD | 1 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/RQ/KGSJ/JGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| CDJX_ZYQD_DGJYZQD | 1 | candidate_effective_business_fact | 75 | amount:YSJE/ZCJE/XCJE/HJJE, date:SJBMC/RQ/YSSJ_Start/YSSJ_End, project:XMID/XMMC, parent:pid, deleted:DEL |
| CDJX_ZYQD_QZJDZQD | 1 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/ZYSJ/YFSJQZ/JFJBRQZ, project:XMID/XMMC, parent:pid, deleted:DEL |
| SGGL_GCJBQKB | 1 | candidate_effective_business_fact | 75 | amount:YJSFKJE/JGCJE, date:SJBMC/TBRQ/SJKGRQ/SJQRCZ, project:XMID/XMMC, parent:pid, deleted:DEL |
| SGGL_GCJBQKB_LD | 1 | candidate_effective_business_fact | 75 | amount:YJSFKJE/JGCJE, date:SJBMC/TBRQ/SJKGRQ/SJQRCZ, project:XMID/XMMC, parent:pid |
| T_CGJH_CGYJH_CB | 1 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/JCSJ, project:XMID, parent:ZBID/pid |
| WS_HTGL_HTJS | 1 | candidate_effective_business_fact | 75 | amount:YHTJE/BGJE/JSJE, date:SJBMC/JSRQ/JSJE/LRSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| WS_HTGL_JSBG | 1 | candidate_effective_business_fact | 75 | amount:WS_HTGL_HTJS_JE/WS_HTGL_HTBG_JE/WS_HTGL_ZBHT_JE/BGJE, date:SJBMC/BGRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| ZJSZ_ZJJH_ZJSYJH_HA | 1 | candidate_effective_business_fact | 75 | amount:HTJE/DQKYZJJE, date:SJBMC/GSJHQDZJ/ZJHLSJ/LRSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| BGGL_TZXX_WJPYCJ | 1616 | candidate_effective_business_fact | 70 | date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:SSDWID, parent:pid, deleted:DEL |

## Top Candidate Families

| Family | Tables | Rows | Effective Tables | Top Tables |
|---|---:|---:|---:|---|
| pm | 5 | 21773 | 1 | Pm_base_Person(80), Pm_Person_Department_PDuty(102), Pm_Person_Department(786), Pm_base_Person_RYXQSQ(1), PM_RYYDGL(20804) |
| t | 55 | 19142 | 17 | T_SC_SCD(4), T_Base_NKCLKMSZ(856), T_Base_NKFBKMSZ(18), T_Base_NKGZKMSZ(11), T_CGJH_CGNJH(3) |
| cgpt | 7 | 9519 | 3 | CGPT_T_Base_HZDWKC_CL(1), CGPT_T_Base_HZDWKC_LW(1), CGPT_T_Base_HZDWKC_FB(1), CGPT_T_Base_SupplierUser(1), CGPT_Base_JCCLK(9499) |
| office_admin | 37 | 5657 | 10 | BGGL_QT_HTHS(3), BGGL_XZ_BZ(115), BGGL_HBZJ_GZZB(90), BGGL_HBZJ_QT_GCBXGMJL(4), BGGL_QT_GCBGTZD(2) |
| base | 3 | 5044 | 2 | BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER(4915), BASE_SYSTEM_WZCLKGXSZ(4), BASE_APP_COMMONOLDUSER(125) |
| zlgl | 3 | 1994 | 1 | ZLGL_Base_DataManager(1817), ZLGL_Base_ZLLXAndQX(156), ZLGL_Base_ZLLX_New(21) |
| sgbw | 1 | 1439 | 0 | SGBW_QDKM(1439) |
| sggl | 32 | 1172 | 15 | SGGL_HJJC_HJCF(2), SGGL_JBXXGL(2), SGGL_DataTypeSet(35), SGGL_Node(25), SGGL_GCJBQKB(1) |
| a | 1 | 716 | 0 | A_HistoryRecord(716) |
| dataspider | 3 | 469 | 1 | DataSpider_ScjstProjectRoughInfo(219), DataSpider_ScjstPersonInfo(54), DataSpider_ScjstPersonCertificate(196) |
| cwgl | 6 | 432 | 2 | CWGL_CLBX_CB(8), CWGL_CLBX(2), CWGL_FYBX_SKDW(1), CWGL_SQGL_CCSQ(177), CWGL_DZFPK(79) |
| gzgl | 1 | 389 | 0 | GZGL_BMSJWH(389) |
| jhjrz | 5 | 344 | 1 | JHJRZ_GZHB(3), JHJRZ_FBRW_CB(96), JHJRZ_FBRW(31), JHJRZ_FBRW_BLXQ(9), JHJRZ_RWCKJLB(205) |
| d | 8 | 231 | 3 | D_SCBSJS_BGGL_XZ_SBRY(167), D_HLCSXT_T_CollectionPlan_New_CB(1), D_YWXT_XM_SGGL_SGZLGL_JGZL(2), D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS_CB(53), D_SCBSJS_SW_JC_GSPTFP_CB(3) |
| xmgl | 14 | 182 | 9 | XMGL_SRHT_QTSRHT(6), XMGL_JJSB_ZLJH_JXYGSQ(2), XMGL_RKGL_SHLQYSD_CB(2), XMGL_RKGL_YSD_CB(2), XMGL_JJSB_ZLJH_JXYGSQ_CB(4) |
| project_settlement | 6 | 74 | 5 | T_ProjectContract_In(4), XMGL_HTGL_XMJSSQ(55), T_Project_GCQZD(6), XM_SBBF(3), T_ProjectContract_Process(1) |
| xm | 8 | 52 | 6 | XM_SBZJ_CB(3), XM_SBRC(20), XM_SBSY(10), XM_SBGH(7), XM_SBZY(4) |
| zyjx | 13 | 49 | 1 | ZYJX_ZY_T_SBZLJC_SBZLRK(1), ZYJX_ZY_T_SBZLJC_SBWZSQ_CB(12), ZYJX_ZY_T_CG_CGSQ_CB(6), ZYJX_ZY_T_SBZLJC_SBZLRK_CB(1), ZYJX_ZY_T_CG_CGSQ(15) |
| gdzc | 1 | 46 | 0 | GDZC_WXZC(46) |
| yszj | 4 | 43 | 3 | YSZJ_CZBS_CZQDBS(4), YSZJ_XMCZ_GCBGTZ(1), YSZJ_CZBS_CZQDBS_CB_CB(34), YSZJ_CZBS_CZQDBS_CB(4) |

## Boundary

- Read-only legacy DB scan
- DB writes: `0`
- This is a table/column signal screen; every candidate still needs lane-level SQL and replay mapping before ingestion.

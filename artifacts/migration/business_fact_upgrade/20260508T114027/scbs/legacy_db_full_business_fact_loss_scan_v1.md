# Legacy DB Full Business Fact Loss Scan v1

Status: `PASS`

Source: `legacy-mssql-scbs:LegacyScbs20260417`

## Summary

```json
{
  "total_tables": 3893,
  "non_empty_tables": 710,
  "candidate_tables": 290,
  "candidate_rows": 23733,
  "classification_counts": {
    "system_or_audit_noise": 345,
    "known_replayed_or_assetized": 149,
    "reference_or_import_catalog": 211,
    "candidate_secondary_business_fact": 172,
    "candidate_effective_business_fact": 115,
    "candidate_needs_manual_screen": 3,
    "low_business_fact_signal": 2898
  },
  "classification_row_counts": {
    "system_or_audit_noise": 262151,
    "known_replayed_or_assetized": 230854,
    "reference_or_import_catalog": 81821,
    "candidate_secondary_business_fact": 16878,
    "candidate_effective_business_fact": 5813,
    "candidate_needs_manual_screen": 1042,
    "low_business_fact_signal": 1273
  },
  "top_candidate_families": [
    {
      "family": "lease_equipment",
      "tables": 18,
      "rows": 6846,
      "effective_tables": 8,
      "secondary_tables": 10,
      "top_tables": [
        {
          "table": "T_ZL_TBD",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "XMGL_JJSB_ZLD_LXYG_CB",
          "rows": 9,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_ZL_ZLJSD_CB_JX",
          "rows": 713,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_ZL_ZLJSD_CB",
          "rows": 55,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_ZL_ZLJH",
          "rows": 20,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "T_ZL_RentalShift",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "T_ZL_ZLJH_JX",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "T_ZL_BTD_JX",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "T_ZL_MachineShift_CB",
          "rows": 5959,
          "classification": "candidate_secondary_business_fact",
          "score": 55
        },
        {
          "table": "HTGL_ZLHT_ZLDW_Yhzhxx",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 55
        }
      ]
    },
    {
      "family": "t",
      "tables": 58,
      "rows": 4470,
      "effective_tables": 20,
      "secondary_tables": 38,
      "top_tables": [
        {
          "table": "T_JS_LLJSD",
          "rows": 18,
          "classification": "candidate_effective_business_fact",
          "score": 115
        },
        {
          "table": "T_ZJZC_ZB",
          "rows": 10,
          "classification": "candidate_effective_business_fact",
          "score": 115
        },
        {
          "table": "T_JS_XSJSD",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 115
        },
        {
          "table": "T_FK_Supplier_SD",
          "rows": 7,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_SC_SCD",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_CGHT_HTPSB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_JH_CGJH",
          "rows": 51,
          "classification": "candidate_effective_business_fact",
          "score": 85
        },
        {
          "table": "T_CG_CGDD",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 85
        },
        {
          "table": "T_ZJZC_DB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 85
        },
        {
          "table": "T_Base_NKCLKMSZ",
          "rows": 854,
          "classification": "candidate_effective_business_fact",
          "score": 75
        }
      ]
    },
    {
      "family": "cgpt",
      "tables": 3,
      "rows": 4462,
      "effective_tables": 1,
      "secondary_tables": 2,
      "top_tables": [
        {
          "table": "CGPT_T_Base_HZDWKC_CL",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGPT_Base_JCCLK",
          "rows": 4455,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "CGPT_T_Base_CGGGLXSZ",
          "rows": 6,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "labor_subcontract",
      "tables": 27,
      "rows": 3205,
      "effective_tables": 11,
      "secondary_tables": 16,
      "top_tables": [
        {
          "table": "T_JS_LWJSD_CB",
          "rows": 1175,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_JS_CLJSD_CB",
          "rows": 1003,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlanContent",
          "rows": 21,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlan",
          "rows": 13,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "LW_LWFD_KQB_CB",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "GLFY_Type",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "GLFY_GLFYJSD_CB",
          "rows": 554,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "LW_Base_LWDWSZ",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "SGGL_FBGL_MasterPlanContent",
          "rows": 33,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_FBGL_MasterPlan",
          "rows": 15,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        }
      ]
    },
    {
      "family": "cgxbj",
      "tables": 13,
      "rows": 1259,
      "effective_tables": 8,
      "secondary_tables": 4,
      "top_tables": [
        {
          "table": "CGXBJ_CGXJD",
          "rows": 136,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGXBJ_BJD",
          "rows": 20,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGXBJ_CGXJD_ZL",
          "rows": 10,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGXBJ_CGXJD_FB",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGXBJ_CGXJD_LW",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGXBJ_BJD_Supplier",
          "rows": 325,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "CGXBJ_BJD_Supplier_LW",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "CGXBJ_BJD_LW",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "CGXBJ_CGXJD_CB",
          "rows": 631,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "CGXBJ_CGXJD_ZL_CB",
          "rows": 11,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        }
      ]
    },
    {
      "family": "d",
      "tables": 13,
      "rows": 1252,
      "effective_tables": 4,
      "secondary_tables": 9,
      "top_tables": [
        {
          "table": "D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB",
          "rows": 162,
          "classification": "candidate_effective_business_fact",
          "score": 115
        },
        {
          "table": "D_SMWZ_CGHT_GC",
          "rows": 29,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "D_SMWZ_XSHT",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "D_XXJZ_JYFZ_HTGL_HTQS_JXTBQR",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB_CB",
          "rows": 852,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_SMWZ_CGHT_GC_CB",
          "rows": 87,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_SMWZ_WZ_BJ_QRD_CB",
          "rows": 67,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_SMWZ_XSHT_CB",
          "rows": 19,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_HLCSXT_T_CollectionPlan_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "D_SMWZ_WZ_BJ_QRD",
          "rows": 13,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "c",
      "tables": 1,
      "rows": 696,
      "effective_tables": 0,
      "secondary_tables": 0,
      "top_tables": [
        {
          "table": "C_JFHKLR_CCB",
          "rows": 696,
          "classification": "candidate_needs_manual_screen",
          "score": 40
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
      "family": "sggl",
      "tables": 26,
      "rows": 297,
      "effective_tables": 13,
      "secondary_tables": 13,
      "top_tables": [
        {
          "table": "SGGL_HJJC_HJCF",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "SGGL_Node",
          "rows": 25,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_DataTypeSet",
          "rows": 18,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_Bar_ConstructionPlan",
          "rows": 29,
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
          "rows": 14,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_AQJC_AQJD",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_XMJDTZ",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_Base_MBJSJD",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "SGGL_HJJC_HJJC",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 65
        }
      ]
    },
    {
      "family": "a",
      "tables": 1,
      "rows": 246,
      "effective_tables": 0,
      "secondary_tables": 0,
      "top_tables": [
        {
          "table": "A_HistoryRecord",
          "rows": 246,
          "classification": "candidate_needs_manual_screen",
          "score": 35
        }
      ]
    },
    {
      "family": "office_admin",
      "tables": 27,
      "rows": 147,
      "effective_tables": 5,
      "secondary_tables": 22,
      "top_tables": [
        {
          "table": "BGGL_QT_HTHS",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "BGGL_HBZJ_XZD_ZDYQSQ",
          "rows": 2,
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
          "table": "BGGL_XZD_ZGSTKCTJB",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "BGGL_JHK_HKDJ_CB",
          "rows": 83,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "BGGL_QSJRW_GZQS_CB",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_XZD_ZGSTKCTJB_CB",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "BGGL_BGYP_Base_YPKM",
          "rows": 8,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "BGGL_XZ_JXDJ",
          "rows": 5,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "BGGL_HBZJ_XZD_JDSPD",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "xm",
      "tables": 9,
      "rows": 62,
      "effective_tables": 6,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "XM_SBZJ_CB",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "XM_SBRC",
          "rows": 22,
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
          "table": "XM_SBWX",
          "rows": 5,
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
          "table": "XM_SBDL",
          "rows": 5,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "XM_SBDS",
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
      "family": "zlgl",
      "tables": 3,
      "rows": 58,
      "effective_tables": 1,
      "secondary_tables": 2,
      "top_tables": [
        {
          "table": "ZLGL_Base_DataManager",
          "rows": 13,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "ZLGL_Base_ZLLXAndQX",
          "rows": 44,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "ZLGL_Base_ZLLX_New",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "xmgl",
      "tables": 3,
      "rows": 47,
      "effective_tables": 3,
      "secondary_tables": 0,
      "top_tables": [
        {
          "table": "XMGL_JJSB_ZLJH_JXYGSQ",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "XMGL_JJSB_ZLJH_JXYGSQ_CB",
          "rows": 40,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "XMGL_WZGL_CKGL_ZXFD",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 65
        }
      ]
    },
    {
      "family": "aqgl",
      "tables": 16,
      "rows": 35,
      "effective_tables": 1,
      "secondary_tables": 15,
      "top_tables": [
        {
          "table": "AQGL_JSGCZGYWSHBX",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "AQGL_AQWMGDJH_CB",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_SLRYCZQK",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_ZGAQJY",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_AQFHYP",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_AQMBZB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_AQWMGDJH",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_AQWMGDMD_CB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_GSSGYBB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "AQGL_PXJLB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "bid_tender",
      "tables": 13,
      "rows": 34,
      "effective_tables": 7,
      "secondary_tables": 6,
      "top_tables": [
        {
          "table": "WS_HTGL_ZBHT",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 115
        },
        {
          "table": "WS_ZBJGL_ZBJ",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "WS_BDGL_TZEGL",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "WS_ZBJGL_BZJ",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGPT_T_Base_ZBXX",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "CGPT_T_Base_ZBXX_CB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "P_ZTB_ZZTB",
          "rows": 2,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "P_ZTB_TBQD_CB",
          "rows": 5,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "P_ZTB_CustomerProfile_CB",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "P_ZTB_BSSB",
          "rows": 3,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "pj",
      "tables": 4,
      "rows": 33,
      "effective_tables": 3,
      "secondary_tables": 1,
      "top_tables": [
        {
          "table": "PJ_Type_MB",
          "rows": 16,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "PJ_Content",
          "rows": 7,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "PJ_Type",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "PJ_Bill",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 65
        }
      ]
    },
    {
      "family": "yt",
      "tables": 3,
      "rows": 30,
      "effective_tables": 1,
      "secondary_tables": 2,
      "top_tables": [
        {
          "table": "YT_Base_NkAndYw_More",
          "rows": 28,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "YT_SGLKYSB_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "YT_NKKM",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "material_stock",
      "tables": 5,
      "rows": 21,
      "effective_tables": 1,
      "secondary_tables": 4,
      "top_tables": [
        {
          "table": "T_RK_JCYSD",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 85
        },
        {
          "table": "T_RK_JCYSD_CB",
          "rows": 6,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_RK_TRSQ_CB",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_RK_TRSQ",
          "rows": 4,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "T_CK_WasteMaterial",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        }
      ]
    },
    {
      "family": "wz",
      "tables": 3,
      "rows": 17,
      "effective_tables": 0,
      "secondary_tables": 3,
      "top_tables": [
        {
          "table": "WZ_Base_GYSBJ_QG",
          "rows": 6,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "WZ_Base_GYSBJ_LW",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "WZ_Base_GYSBJ_CB",
          "rows": 9,
          "classification": "candidate_secondary_business_fact",
          "score": 40
        }
      ]
    }
  ],
  "top_candidates": [
    {
      "schema": "dbo",
      "table": "D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB",
      "row_count": 162,
      "column_count": 34,
      "classification": "candidate_effective_business_fact",
      "family": "d",
      "business_signal_score": 115,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "DJRQ",
          "LRSJ",
          "XGSJ",
          "QYRQ",
          "JHSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "XSDWID"
        ],
        "contract": [
          "HTBH"
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
      "table": "T_JS_LLJSD",
      "row_count": 18,
      "column_count": 34,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 115,
      "signals": {
        "amount": [
          "ZJE",
          "ZKJE",
          "YFJE"
        ],
        "date": [
          "SJBMC",
          "JSRQ",
          "LRSJ",
          "XGSJ",
          "QSJSRQ",
          "ZZJSRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDWID"
        ],
        "contract": [
          "HTBH",
          "HTBH_2"
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
      "table": "T_ZJZC_ZB",
      "row_count": 10,
      "column_count": 85,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 115,
      "signals": {
        "amount": [
          "ZJE",
          "SQBXJE",
          "SJBXJE",
          "HXJE",
          "FPJE"
        ],
        "date": [
          "SJBMC",
          "LRRQ",
          "SHRQ",
          "CJRQ",
          "XGSJ",
          "SJBXJE"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "Supplier_ID",
          "GYSName",
          "JFDWID"
        ],
        "contract": [
          "HTBH"
        ],
        "parent": [
          "FPID",
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "WS_HTGL_ZBHT",
      "row_count": 2,
      "column_count": 33,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 115,
      "signals": {
        "amount": [
          "ZBJE",
          "BZJJE",
          "ZBJJE"
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
        "partner": [
          "SGDWID"
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
      "table": "T_JS_XSJSD",
      "row_count": 1,
      "column_count": 33,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 115,
      "signals": {
        "amount": [
          "ZJE",
          "ZKJE",
          "YFJE"
        ],
        "date": [
          "SJBMC",
          "JSRQ",
          "LRSJ",
          "XGSJ",
          "QSJSRQ",
          "ZZJSRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDWID"
        ],
        "contract": [
          "HTBH",
          "HTBH_2"
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
      "table": "CGXBJ_CGXJD",
      "row_count": 136,
      "column_count": 43,
      "classification": "candidate_effective_business_fact",
      "family": "cgxbj",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "XJSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "XJDWID"
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
      "table": "D_SMWZ_CGHT_GC",
      "row_count": 29,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "d",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "HTJE_KZ"
        ],
        "date": [
          "SJBMC",
          "QDSJ",
          "DJRQ",
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
          "PID"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "CGXBJ_BJD",
      "row_count": 20,
      "column_count": 30,
      "classification": "candidate_effective_business_fact",
      "family": "cgxbj",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "JYJE"
        ],
        "date": [
          "SJBMC",
          "RQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "TJDWID"
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
      "table": "CGXBJ_CGXJD_ZL",
      "row_count": 10,
      "column_count": 40,
      "classification": "candidate_effective_business_fact",
      "family": "cgxbj",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "XJSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "XJDWID"
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
      "table": "T_FK_Supplier_SD",
      "row_count": 7,
      "column_count": 27,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "f_FKJE",
          "f_FPJE",
          "f_LDJE"
        ],
        "date": [
          "SJBMC",
          "f_FKRQ",
          "f_LRSJ"
        ],
        "project": [
          "f_XMID"
        ],
        "partner": [
          "f_SupplierID",
          "f_SupplierName",
          "f_CBFLID"
        ],
        "parent": [
          "f_ZFSQGLId",
          "pid"
        ],
        "deleted": [
          "DEL"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "D_SMWZ_XSHT",
      "row_count": 6,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "d",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "HJJEDX"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "QDSJ",
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
          "PID"
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
      "table": "CGXBJ_CGXJD_FB",
      "row_count": 5,
      "column_count": 41,
      "classification": "candidate_effective_business_fact",
      "family": "cgxbj",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "XJSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "XJDWID"
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
      "table": "T_ZL_TBD",
      "row_count": 5,
      "column_count": 27,
      "classification": "candidate_effective_business_fact",
      "family": "lease_equipment",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "BTJE",
          "BTSFJE"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ",
          "DJRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "ZLDWID"
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
      "row_count": 5,
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
      "table": "CGXBJ_CGXJD_LW",
      "row_count": 4,
      "column_count": 41,
      "classification": "candidate_effective_business_fact",
      "family": "cgxbj",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "XJSJ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "XJDWID"
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
      "table": "WS_ZBJGL_ZBJ",
      "row_count": 4,
      "column_count": 20,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZBJJE"
        ],
        "date": [
          "SJBMC",
          "Date",
          "LRSJ",
          "XGSJ"
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
      "table": "SGGL_HJJC_HJCF",
      "row_count": 3,
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
      "table": "T_SC_SCD",
      "row_count": 3,
      "column_count": 38,
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
      "table": "WS_BDGL_TZEGL",
      "row_count": 3,
      "column_count": 13,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "GSZJE",
          "GSFBDZGYSJE"
        ],
        "date": [
          "SJBMC",
          "GSFBDZGYSJE",
          "GSJAGCF"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "GSFBDZGYSJE"
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
      "table": "WS_ZBJGL_BZJ",
      "row_count": 3,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZBJJE"
        ],
        "date": [
          "SJBMC",
          "Date",
          "LRSJ",
          "XGSJ"
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
      "table": "BGGL_QT_HTHS",
      "row_count": 2,
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
      "table": "CGPT_T_Base_ZBXX",
      "row_count": 1,
      "column_count": 46,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "D_XYLG_ZBJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "LRSJ",
          "XGSJ",
          "GSSJ",
          "D_XYLG_TZSJ",
          "ZBRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "ZBDWID"
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
      "table": "CGPT_T_Base_ZBXX_CB",
      "row_count": 1,
      "column_count": 14,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "ZJE"
        ],
        "date": [
          "SJBMC",
          "BJKSSJ",
          "BJJZSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "ZBDWID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "JCHT_XMHYGHFJB",
      "row_count": 1,
      "column_count": 21,
      "classification": "candidate_effective_business_fact",
      "family": "jcht",
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
        "partner": [
          "JSDW",
          "JSDWID"
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
      "table": "T_CGHT_HTPSB",
      "row_count": 1,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "HTJE",
          "HTJEDX"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMMC",
          "XMID"
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
      "table": "ZJGL_BZJGL_Branch_SBZJTH_CB",
      "row_count": 1,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "payment_fund",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "BZJJE",
          "THJE"
        ],
        "date": [
          "SJBMC",
          "THRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "DWID",
          "SKDWID"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_JH_CGJH",
      "row_count": 51,
      "column_count": 66,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 85,
      "signals": {
        "amount": [
          "CG_ZJE",
          "ZJEHJ"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "LRSJ",
          "XGRQ",
          "SCRQ",
          "DCSJ"
        ],
        "project": [
          "f_XMID",
          "XMMC",
          "GLXMMC"
        ],
        "partner": [
          "GYSID",
          "GYSMC",
          "LLDWID"
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
      "table": "T_RK_JCYSD",
      "row_count": 6,
      "column_count": 21,
      "classification": "candidate_effective_business_fact",
      "family": "material_stock",
      "business_signal_score": 85,
      "signals": {
        "date": [
          "SJBMC",
          "JHRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMMC",
          "XMID"
        ],
        "partner": [
          "GHDWID"
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
      "table": "T_CG_CGDD",
      "row_count": 3,
      "column_count": 42,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 85,
      "signals": {
        "date": [
          "SJBMC",
          "CGRQ",
          "JHRQ",
          "LRSJ",
          "XGSJ",
          "KDGSJP"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "ZBGYSID",
          "ZBGYSMC"
        ],
        "contract": [
          "D_BYK_CGHTBH",
          "D_BYK_CGHTID"
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
      "table": "T_ZJZC_DB",
      "row_count": 1,
      "column_count": 46,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 85,
      "signals": {
        "date": [
          "SJBMC",
          "LRRQ",
          "SHRQ",
          "CJRQ",
          "XGSJ"
        ],
        "project": [
          "XMID"
        ],
        "partner": [
          "Supplier_ID",
          "GYSName",
          "DBDWID"
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
      "table": "T_JS_LWJSD_CB",
      "row_count": 1175,
      "column_count": 32,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "FDJE",
          "FDJE_NO",
          "GCLJJE",
          "JE",
          "JSJE_YJS",
          "KJJE"
        ],
        "date": [
          "SJBMC",
          "JSJE_YJS"
        ],
        "partner": [
          "JSDWID",
          "JSDW",
          "LWDWID"
        ],
        "parent": [
          "ZBID",
          "FDCB_Pid",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_JS_CLJSD_CB",
      "row_count": 1003,
      "column_count": 43,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "RKJE",
          "RKJE_NO",
          "RKSE",
          "DZJE",
          "SE",
          "JE",
          "D_HLCSXT_BHS_JE"
        ],
        "date": [
          "SJBMC",
          "DJRQ"
        ],
        "partner": [
          "JSDWID",
          "JSDW"
        ],
        "parent": [
          "ZBID",
          "pid"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_Base_NKCLKMSZ",
      "row_count": 854,
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
      "table": "YT_Base_NkAndYw_More",
      "row_count": 28,
      "column_count": 28,
      "classification": "candidate_effective_business_fact",
      "family": "yt",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE",
          "JSJE"
        ],
        "date": [
          "SJBMC",
          "SJSL",
          "JSJE",
          "LRSJ"
        ],
        "project": [
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
      "table": "SGGL_FBGL_MonthPlanContent",
      "row_count": 21,
      "column_count": 25,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "planPrice",
          "planMoney",
          "createUserID",
          "createUserName"
        ],
        "date": [
          "SJBMC",
          "createUserID",
          "createUserName",
          "createDate"
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
      "table": "SGGL_DataTypeSet",
      "row_count": 18,
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
      "table": "SGGL_FBGL_MonthPlan",
      "row_count": 13,
      "column_count": 24,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName",
          "GZZJE"
        ],
        "date": [
          "SJBMC",
          "billDate",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate",
          "FBRQ",
          "JZRQ",
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
      "table": "SYSTEM_OFFICE_PERSONNELATTENDANCE",
      "row_count": 13,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "system",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "USERID",
          "USERNAME"
        ],
        "date": [
          "LRSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "parent": [
          "PID",
          "GROUPID"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "ZLGL_Base_DataManager",
      "row_count": 13,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "zlgl",
      "business_signal_score": 75,
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
      "table": "BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER",
      "row_count": 10,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "base",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "USERID",
          "USERNAME"
        ],
        "date": [
          "RZRQ",
          "ISJZ"
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
      "table": "ZJGL_BZJGL_Pay_FBZJTH_CB",
      "row_count": 10,
      "column_count": 21,
      "classification": "candidate_effective_business_fact",
      "family": "payment_fund",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "BZJJE",
          "THJE"
        ],
        "date": [
          "SJBMC",
          "BZJRQ",
          "THRQ"
        ],
        "project": [
          "XMID",
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
      "table": "XMGL_JJSB_ZLD_LXYG_CB",
      "row_count": 9,
      "column_count": 32,
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
          "QZSJ_JZ"
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
      "table": "XMGL_JJSB_ZLJH_JXYGSQ",
      "row_count": 6,
      "column_count": 25,
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
      "table": "D_XXJZ_JYFZ_HTGL_HTQS_JXTBQR",
      "row_count": 5,
      "column_count": 18,
      "classification": "candidate_effective_business_fact",
      "family": "d",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ZJEHJY"
        ],
        "date": [
          "DJRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
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
      "table": "AQGL_JSGCZGYWSHBX",
      "row_count": 3,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "aqgl",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "TBJE"
        ],
        "date": [
          "SJBMC",
          "BZRQ",
          "BXRQ",
          "LRSJ"
        ],
        "project": [
          "XMID",
          "XMMC"
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
      "table": "LW_LWFD_KQB_CB",
      "row_count": 3,
      "column_count": 12,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "SEX"
        ],
        "date": [
          "SJBMC",
          "SJH"
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
      "table": "BGGL_HBZJ_XZD_ZDYQSQ",
      "row_count": 2,
      "column_count": 34,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "ZDRQ",
          "LRSJ",
          "XGSJ",
          "ZDRQ_E",
          "YJZDRQ"
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
      "table": "BGGL_XZD_ZGSTKCTJB",
      "row_count": 2,
      "column_count": 19,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
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
      "table": "P_ZTB_ZZTB",
      "row_count": 2,
      "column_count": 33,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "XMJL_UserID",
          "LXR_UserID"
        ],
        "date": [
          "SJBMC",
          "RQ",
          "XGRQ",
          "SCRQ",
          "LRSJ",
          "BMSJ"
        ],
        "project": [
          "XMID",
          "TBXMMC",
          "D_JCLY_XMMC"
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
    }
  ]
}
```

## Top Candidate Tables

| Table | Rows | Classification | Score | Signals |
|---|---:|---|---:|---|
| D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB | 162 | candidate_effective_business_fact | 115 | amount:ZJE, date:DJRQ/LRSJ/XGSJ/QYRQ, project:XMID/XMMC, partner:XSDWID, contract:HTBH, parent:PID, deleted:DEL |
| T_JS_LLJSD | 18 | candidate_effective_business_fact | 115 | amount:ZJE/ZKJE/YFJE, date:SJBMC/JSRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:JSDWID, contract:HTBH/HTBH_2, parent:pid, deleted:DEL |
| T_ZJZC_ZB | 10 | candidate_effective_business_fact | 115 | amount:ZJE/SQBXJE/SJBXJE/HXJE, date:SJBMC/LRRQ/SHRQ/CJRQ, project:XMID/XMMC, partner:Supplier_ID/GYSName/JFDWID, contract:HTBH, parent:FPID/pid, deleted:DEL |
| WS_HTGL_ZBHT | 2 | candidate_effective_business_fact | 115 | amount:ZBJE/BZJJE/ZBJJE, date:SJBMC/QYRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:SGDWID, contract:HTBH, parent:pid, deleted:DEL |
| T_JS_XSJSD | 1 | candidate_effective_business_fact | 115 | amount:ZJE/ZKJE/YFJE, date:SJBMC/JSRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:JSDWID, contract:HTBH/HTBH_2, parent:pid, deleted:DEL |
| CGXBJ_CGXJD | 136 | candidate_effective_business_fact | 95 | amount:ZJE, date:SJBMC/XJSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:XJDWID, parent:pid, deleted:Del |
| D_SMWZ_CGHT_GC | 29 | candidate_effective_business_fact | 95 | amount:HTJE_KZ, date:SJBMC/QDSJ/DJRQ/LRSJ, project:XMID/XMMC, contract:HTBH, parent:PID, deleted:DEL |
| CGXBJ_BJD | 20 | candidate_effective_business_fact | 95 | amount:JYJE, date:SJBMC/RQ/LRSJ/XGSJ, project:XMID/XMMC, partner:TJDWID, parent:PID, deleted:DEL |
| CGXBJ_CGXJD_ZL | 10 | candidate_effective_business_fact | 95 | amount:ZJE, date:SJBMC/XJSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:XJDWID, parent:pid, deleted:Del |
| T_FK_Supplier_SD | 7 | candidate_effective_business_fact | 95 | amount:f_FKJE/f_FPJE/f_LDJE, date:SJBMC/f_FKRQ/f_LRSJ, project:f_XMID, partner:f_SupplierID/f_SupplierName/f_CBFLID, parent:f_ZFSQGLId/pid, deleted:DEL |
| D_SMWZ_XSHT | 6 | candidate_effective_business_fact | 95 | amount:HJJEDX, date:SJBMC/DJRQ/QDSJ/LRSJ, project:XMID/XMMC, contract:HTBH, parent:PID, deleted:DEL |
| T_Project_GCQZD | 6 | candidate_effective_business_fact | 95 | amount:SJJE, date:SJBMC/SJ/SJJE/LRSJ, project:XMID/XMMC, partner:JSDWID/JSDW/JLDWID, parent:pid, deleted:DEL |
| CGXBJ_CGXJD_FB | 5 | candidate_effective_business_fact | 95 | amount:ZJE, date:SJBMC/XJSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:XJDWID, parent:pid, deleted:Del |
| T_ZL_TBD | 5 | candidate_effective_business_fact | 95 | amount:BTJE/BTSFJE, date:SJBMC/LRSJ/XGSJ/DJRQ, project:XMID/XMMC, partner:ZLDWID, parent:pid, deleted:DEL |
| XM_SBBF | 5 | candidate_effective_business_fact | 95 | amount:BFTBJE, date:SJBMC/BFRQ/LRSJ/XGRQ, project:XMID/XMMC, partner:JSDWID/JSDW, parent:pid, deleted:SCRID/SCRQ/DEL |
| CGXBJ_CGXJD_LW | 4 | candidate_effective_business_fact | 95 | amount:ZJE, date:SJBMC/XJSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:XJDWID, parent:pid, deleted:Del |
| WS_ZBJGL_ZBJ | 4 | candidate_effective_business_fact | 95 | amount:ZBJJE, date:SJBMC/Date/LRSJ/XGSJ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| SGGL_HJJC_HJCF | 3 | candidate_effective_business_fact | 95 | amount:CFJE, date:SJBMC/CFSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:BCFDWID, parent:pid |
| T_SC_SCD | 3 | candidate_effective_business_fact | 95 | amount:CPJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:YLLLDWID/CPRKDWID/CPJSDWID/CPJSDWMC, parent:Pid, deleted:DEL |
| WS_BDGL_TZEGL | 3 | candidate_effective_business_fact | 95 | amount:GSZJE/GSFBDZGYSJE, date:SJBMC/GSFBDZGYSJE/GSJAGCF, project:XMID/XMMC, partner:GSFBDZGYSJE, parent:pid, deleted:DEL |
| WS_ZBJGL_BZJ | 3 | candidate_effective_business_fact | 95 | amount:ZBJJE, date:SJBMC/Date/LRSJ/XGSJ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| WS_ZJJLTZ_ZFTZ | 3 | candidate_effective_business_fact | 95 | amount:ZFJE/KHBLKJE/FPJE, date:SJBMC/LRSJ/XGSJ/ZFRQ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| BGGL_QT_HTHS | 2 | candidate_effective_business_fact | 95 | amount:HTJE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, contract:HTBH/HTMC, parent:pid, deleted:DEL |
| CGPT_T_Base_HZDWKC_CL | 1 | candidate_effective_business_fact | 95 | amount:T_Base_SupplierInfo_ID, date:SJBMC/KCRQ/LRSJ/XGSJ, project:XMMC/XMID, partner:T_Base_SupplierInfo_ID, parent:pid, deleted:DEL |
| CGPT_T_Base_ZBXX | 1 | candidate_effective_business_fact | 95 | amount:D_XYLG_ZBJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:ZBDWID, parent:pid, deleted:DEL |
| CGPT_T_Base_ZBXX_CB | 1 | candidate_effective_business_fact | 95 | amount:ZJE, date:SJBMC/BJKSSJ/BJJZSJ, project:XMID/XMMC, partner:ZBDWID, parent:ZBID/pid |
| JCHT_XMHYGHFJB | 1 | candidate_effective_business_fact | 95 | amount:HTJE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, partner:JSDW/JSDWID, parent:pid, deleted:DEL |
| T_CGHT_HTPSB | 1 | candidate_effective_business_fact | 95 | amount:HTJE/HTJEDX, date:SJBMC/LRSJ/XGSJ, project:XMMC/XMID, contract:HTMC, parent:pid, deleted:DEL |
| WS_HTGL_HTBG | 1 | candidate_effective_business_fact | 95 | amount:WS_HTGL_ZBHT_JE/JEBG, date:SJBMC/QYRQ/LRSJ/XGSJ, project:XMID/XMMC, contract:HTBH, parent:pid, deleted:DEL |
| ZJGL_BZJGL_Branch_SBZJTH_CB | 1 | candidate_effective_business_fact | 95 | amount:BZJJE/THJE, date:SJBMC/THRQ, project:XMID/XMMC, partner:DWID/SKDWID, parent:ZBID/pid |
| T_JH_CGJH | 51 | candidate_effective_business_fact | 85 | amount:CG_ZJE/ZJEHJ, date:SJBMC/DJRQ/LRSJ/XGRQ, project:f_XMID/XMMC/GLXMMC, partner:GYSID/GYSMC/LLDWID, deleted:SCRID/SCRQ/DEL |
| T_RK_JCYSD | 6 | candidate_effective_business_fact | 85 | date:SJBMC/JHRQ/LRSJ/XGSJ, project:XMMC/XMID, partner:GHDWID, contract:HTBH, parent:pid, deleted:DEL |
| T_CG_CGDD | 3 | candidate_effective_business_fact | 85 | date:SJBMC/CGRQ/JHRQ/LRSJ, project:XMID/XMMC, partner:ZBGYSID/ZBGYSMC, contract:D_BYK_CGHTBH/D_BYK_CGHTID, parent:pid, deleted:DEL |
| T_ZJZC_DB | 1 | candidate_effective_business_fact | 85 | date:SJBMC/LRRQ/SHRQ/CJRQ, project:XMID, partner:Supplier_ID/GYSName/DBDWID, contract:HTBH, parent:pid, deleted:DEL |
| T_JS_LWJSD_CB | 1175 | candidate_effective_business_fact | 75 | amount:FDJE/FDJE_NO/GCLJJE/JE, date:SJBMC/JSJE_YJS, partner:JSDWID/JSDW/LWDWID, parent:ZBID/FDCB_Pid/pid |
| T_JS_CLJSD_CB | 1003 | candidate_effective_business_fact | 75 | amount:RKJE/RKJE_NO/RKSE/DZJE, date:SJBMC/DJRQ, partner:JSDWID/JSDW, parent:ZBID/pid |
| T_Base_NKCLKMSZ | 854 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/CLSJGUID/CLSJCODE/CLSJMC, project:XMID/XMMC, parent:pid |
| YT_Base_NkAndYw_More | 28 | candidate_effective_business_fact | 75 | amount:JE/JSJE, date:SJBMC/SJSL/JSJE/LRSJ, project:XMID, parent:pid, deleted:DEL |
| SGGL_Node | 25 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/startDate/endDate/createUserID, project:XMID/XMMC, parent:parentId |
| SGGL_FBGL_MonthPlanContent | 21 | candidate_effective_business_fact | 75 | amount:planPrice/planMoney/createUserID/createUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:pid |
| SGGL_DataTypeSet | 18 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId |
| T_Base_NKFBKMSZ | 18 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/FBSJGUID, project:XMID/XMMC, parent:pid |
| PJ_Type_MB | 16 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete |
| SGGL_FBGL_MonthPlan | 13 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/billDate/createUserID/createUserName, project:XMID/XMMC, parent:pid, deleted:DEL |
| SYSTEM_OFFICE_PERSONNELATTENDANCE | 13 | candidate_effective_business_fact | 75 | amount:USERID/USERNAME, date:LRSJ, project:XMID/XMMC, parent:PID/GROUPID |
| ZLGL_Base_DataManager | 13 | candidate_effective_business_fact | 75 | amount:ZLGL_Base_ZLLX_Id/ZLGL_Base_ZLLX_Name, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_Base_NKGZKMSZ | 11 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/GZSJGUID, project:XMID/XMMC, parent:pid |
| BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER | 10 | candidate_effective_business_fact | 75 | amount:USERID/USERNAME, date:RZRQ/ISJZ, project:XMID, parent:PID, deleted:DEL |
| ZJGL_BZJGL_Pay_FBZJTH_CB | 10 | candidate_effective_business_fact | 75 | amount:BZJJE/THJE, date:SJBMC/BZJRQ/THRQ, project:XMID/XMMC, parent:ZBID/pid |
| XMGL_JJSB_ZLD_LXYG_CB | 9 | candidate_effective_business_fact | 75 | amount:JE/JE_NO/SE, date:SJBMC/RQ/QZSJ_KS/QZSJ_JZ, project:XMMC, parent:ZBID/pid |
| PJ_Content | 7 | candidate_effective_business_fact | 75 | amount:inBillMoney/outBillMoney/createUserID/createUserName, date:SJBMC/billDate/createUserID/createUserName, project:XMID/XMMC, parent:billId, deleted:DEL |
| PJ_Type | 6 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete |
| XMGL_JJSB_ZLJH_JXYGSQ | 6 | candidate_effective_business_fact | 75 | amount:createUserID/GZZJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| D_XXJZ_JYFZ_HTGL_HTQS_JXTBQR | 5 | candidate_effective_business_fact | 75 | amount:ZJEHJY, date:DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:Pid, deleted:DEL |
| AQGL_JSGCZGYWSHBX | 3 | candidate_effective_business_fact | 75 | amount:TBJE, date:SJBMC/BZRQ/BXRQ/LRSJ, project:XMID/XMMC, parent:Pid, deleted:DEL |
| LW_LWFD_KQB_CB | 3 | candidate_effective_business_fact | 75 | amount:SEX, date:SJBMC/SJH, project:XMID, parent:ZBID/pid |
| BGGL_HBZJ_XZD_ZDYQSQ | 2 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/ZDRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| BGGL_QT_GCBGTZD | 2 | candidate_effective_business_fact | 75 | amount:YGBGJE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| BGGL_XZD_ZGSTKCTJB | 2 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| P_ZTB_ZZTB | 2 | candidate_effective_business_fact | 75 | amount:XMJL_UserID/LXR_UserID, date:SJBMC/RQ/XGRQ/SCRQ, project:XMID/TBXMMC/D_JCLY_XMMC, parent:pid, deleted:SCRID/SCRQ/DEL |

## Top Candidate Families

| Family | Tables | Rows | Effective Tables | Top Tables |
|---|---:|---:|---:|---|
| lease_equipment | 18 | 6846 | 8 | T_ZL_TBD(5), XMGL_JJSB_ZLD_LXYG_CB(9), T_ZL_ZLJSD_CB_JX(713), T_ZL_ZLJSD_CB(55), T_ZL_ZLJH(20) |
| t | 58 | 4470 | 20 | T_JS_LLJSD(18), T_ZJZC_ZB(10), T_JS_XSJSD(1), T_FK_Supplier_SD(7), T_SC_SCD(3) |
| cgpt | 3 | 4462 | 1 | CGPT_T_Base_HZDWKC_CL(1), CGPT_Base_JCCLK(4455), CGPT_T_Base_CGGGLXSZ(6) |
| labor_subcontract | 27 | 3205 | 11 | T_JS_LWJSD_CB(1175), T_JS_CLJSD_CB(1003), SGGL_FBGL_MonthPlanContent(21), SGGL_FBGL_MonthPlan(13), LW_LWFD_KQB_CB(3) |
| cgxbj | 13 | 1259 | 8 | CGXBJ_CGXJD(136), CGXBJ_BJD(20), CGXBJ_CGXJD_ZL(10), CGXBJ_CGXJD_FB(5), CGXBJ_CGXJD_LW(4) |
| d | 13 | 1252 | 4 | D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB(162), D_SMWZ_CGHT_GC(29), D_SMWZ_XSHT(6), D_XXJZ_JYFZ_HTGL_HTQS_JXTBQR(5), D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB_CB(852) |
| c | 1 | 696 | 0 | C_JFHKLR_CCB(696) |
| gzgl | 1 | 389 | 0 | GZGL_BMSJWH(389) |
| sggl | 26 | 297 | 13 | SGGL_HJJC_HJCF(3), SGGL_Node(25), SGGL_DataTypeSet(18), SGGL_Bar_ConstructionPlan(29), SGGL_Node_Abarbeitung(16) |
| a | 1 | 246 | 0 | A_HistoryRecord(246) |
| office_admin | 27 | 147 | 5 | BGGL_QT_HTHS(2), BGGL_HBZJ_XZD_ZDYQSQ(2), BGGL_QT_GCBGTZD(2), BGGL_XZD_ZGSTKCTJB(2), BGGL_JHK_HKDJ_CB(83) |
| xm | 9 | 62 | 6 | XM_SBZJ_CB(3), XM_SBRC(22), XM_SBSY(10), XM_SBGH(7), XM_SBWX(5) |
| zlgl | 3 | 58 | 1 | ZLGL_Base_DataManager(13), ZLGL_Base_ZLLXAndQX(44), ZLGL_Base_ZLLX_New(1) |
| xmgl | 3 | 47 | 3 | XMGL_JJSB_ZLJH_JXYGSQ(6), XMGL_JJSB_ZLJH_JXYGSQ_CB(40), XMGL_WZGL_CKGL_ZXFD(1) |
| aqgl | 16 | 35 | 1 | AQGL_JSGCZGYWSHBX(3), AQGL_AQWMGDJH_CB(4), AQGL_SLRYCZQK(4), AQGL_ZGAQJY(3), AQGL_AQFHYP(2) |
| bid_tender | 13 | 34 | 7 | WS_HTGL_ZBHT(2), WS_ZBJGL_ZBJ(4), WS_BDGL_TZEGL(3), WS_ZBJGL_BZJ(3), CGPT_T_Base_ZBXX(1) |
| pj | 4 | 33 | 3 | PJ_Type_MB(16), PJ_Content(7), PJ_Type(6), PJ_Bill(4) |
| yt | 3 | 30 | 1 | YT_Base_NkAndYw_More(28), YT_SGLKYSB_CB(1), YT_NKKM(1) |
| material_stock | 5 | 21 | 1 | T_RK_JCYSD(6), T_RK_JCYSD_CB(6), T_RK_TRSQ_CB(4), T_RK_TRSQ(4), T_CK_WasteMaterial(1) |
| wz | 3 | 17 | 0 | WZ_Base_GYSBJ_QG(6), WZ_Base_GYSBJ_LW(2), WZ_Base_GYSBJ_CB(9) |

## Boundary

- Read-only legacy DB scan
- DB writes: `0`
- This is a table/column signal screen; every candidate still needs lane-level SQL and replay mapping before ingestion.

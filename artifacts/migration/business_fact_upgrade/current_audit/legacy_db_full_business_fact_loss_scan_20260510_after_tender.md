# Legacy DB Full Business Fact Loss Scan v1

Status: `PASS`

Source: `legacy-mssql-restore:LegacyDb`

## Summary

```json
{
  "total_tables": 4312,
  "non_empty_tables": 1128,
  "candidate_tables": 342,
  "candidate_rows": 74674,
  "classification_counts": {
    "known_replayed_or_assetized": 156,
    "system_or_audit_noise": 362,
    "candidate_needs_manual_screen": 8,
    "reference_or_import_catalog": 489,
    "low_business_fact_signal": 2963,
    "candidate_secondary_business_fact": 187,
    "candidate_effective_business_fact": 147
  },
  "classification_row_counts": {
    "known_replayed_or_assetized": 3720554,
    "system_or_audit_noise": 1245813,
    "candidate_needs_manual_screen": 22997,
    "reference_or_import_catalog": 2518257,
    "low_business_fact_signal": 19746,
    "candidate_secondary_business_fact": 34478,
    "candidate_effective_business_fact": 17199
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
      "tables": 63,
      "rows": 19166,
      "effective_tables": 25,
      "secondary_tables": 37,
      "top_tables": [
        {
          "table": "T_GYSHT_INFO_Ext_XAKW",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 105
        },
        {
          "table": "T_FK_Supplier_SD",
          "rows": 7,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_HTGL_HTBG",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_SC_SCD",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_CollectionPlan_New",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "T_CGHT_CGDD",
          "rows": 4,
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
          "table": "T_JH_CGJH",
          "rows": 2,
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
          "rows": 856,
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
      "tables": 38,
      "rows": 5779,
      "effective_tables": 11,
      "secondary_tables": 27,
      "top_tables": [
        {
          "table": "BGGL_QT_HTHS",
          "rows": 3,
          "classification": "candidate_effective_business_fact",
          "score": 95
        },
        {
          "table": "BGGL_ZTBJHT_TBBM_TBBMFSQ",
          "rows": 122,
          "classification": "candidate_effective_business_fact",
          "score": 75
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
        }
      ]
    },
    {
      "family": "labor_subcontract",
      "tables": 42,
      "rows": 5147,
      "effective_tables": 19,
      "secondary_tables": 23,
      "top_tables": [
        {
          "table": "GLFY_Dept",
          "rows": 1674,
          "classification": "candidate_effective_business_fact",
          "score": 90
        },
        {
          "table": "GLFY_Type",
          "rows": 2613,
          "classification": "candidate_effective_business_fact",
          "score": 80
        },
        {
          "table": "LW_LWFD_KQB_CB",
          "rows": 25,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlanContent",
          "rows": 16,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "GLFY_Content",
          "rows": 14,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlan",
          "rows": 11,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "GLFY_GLRYGZB_CB",
          "rows": 8,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "LW_Base_FDGL_YLYS",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "LW_Base_LWDWSZ",
          "rows": 195,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_JS_LWJSD_CB",
          "rows": 137,
          "classification": "candidate_effective_business_fact",
          "score": 70
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
      "tables": 10,
      "rows": 820,
      "effective_tables": 4,
      "secondary_tables": 5,
      "top_tables": [
        {
          "table": "A_SCBS_JXD",
          "rows": 37,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "A_SCBS_RYGZD",
          "rows": 8,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "A_SCBS_CLCKD",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "A_SCBS_FYD",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "A_SCBS_JXD_CB",
          "rows": 40,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "A_SCBS_RYGZD_CB",
          "rows": 14,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "A_SCBS_CLCKD_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "A_SCBS_FYD_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "A_SCBS_JDRB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
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
      "family": "lease_equipment",
      "tables": 15,
      "rows": 237,
      "effective_tables": 7,
      "secondary_tables": 8,
      "top_tables": [
        {
          "table": "XMGL_JJSB_ZLD_LXYG_CB",
          "rows": 12,
          "classification": "candidate_effective_business_fact",
          "score": 75
        },
        {
          "table": "T_ZL_ZLJSD_CB_JX",
          "rows": 11,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_ZL_ZLJSD_CB",
          "rows": 10,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_ZL_ZRDCB_JX",
          "rows": 6,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_ZL_ZRDCB",
          "rows": 1,
          "classification": "candidate_effective_business_fact",
          "score": 70
        },
        {
          "table": "T_ZL_ZLJH",
          "rows": 5,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "T_ZL_ZLJH_JX",
          "rows": 4,
          "classification": "candidate_effective_business_fact",
          "score": 65
        },
        {
          "table": "HTGL_ZLHT_ZLDW_Yhzhxx",
          "rows": 27,
          "classification": "candidate_secondary_business_fact",
          "score": 55
        },
        {
          "table": "HTGL_ZLHT_ZLHT_CB_JX",
          "rows": 55,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "T_ZL_MachineShift_CB",
          "rows": 53,
          "classification": "candidate_secondary_business_fact",
          "score": 50
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
      "family": "material_stock",
      "tables": 8,
      "rows": 74,
      "effective_tables": 0,
      "secondary_tables": 8,
      "top_tables": [
        {
          "table": "A_SCBS_CLRKD_CB",
          "rows": 46,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "YT_JGZS_SGLKYSZB_CSCB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 50
        },
        {
          "table": "YT_JGZS_SGLKYSZB_QD",
          "rows": 12,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "YT_JGZS_SGLKYSZB",
          "rows": 8,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "YT_JGZS_SGLKYSZB_CS",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_WZJJF_SBZLD_CB",
          "rows": 2,
          "classification": "candidate_secondary_business_fact",
          "score": 40
        },
        {
          "table": "ZYJX_ZY_T_WZJJF_SBHZD_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 40
        },
        {
          "table": "ZYJX_ZY_T_WZJJF_ZLHT_CB",
          "rows": 1,
          "classification": "candidate_secondary_business_fact",
          "score": 40
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
      "table": "T_GYSHT_INFO_Ext_XAKW",
      "row_count": 1,
      "column_count": 104,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 105,
      "signals": {
        "amount": [
          "ZJE_DX",
          "ZJE_NO_DX",
          "SE_DX"
        ],
        "date": [
          "SJBMC",
          "JF_RQ",
          "YF_RQ",
          "DHQD_RQ",
          "RKYSD_RQ"
        ],
        "project": [
          "DHQD_XMMC"
        ],
        "partner": [
          "T_GYSHT_INFO_Id"
        ],
        "contract": [
          "T_GYSHT_INFO_Id"
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
      "table": "P_ZTB_GCXXGL",
      "row_count": 20,
      "column_count": 140,
      "classification": "candidate_effective_business_fact",
      "family": "bid_tender",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "XMJL_UserID",
          "LXR_UserID",
          "BZJJE"
        ],
        "date": [
          "SJBMC",
          "f_DJRQ",
          "f_LRSJ",
          "XGRQ",
          "SCRQ",
          "BZJJZSJ",
          "KBSJ",
          "GLSJID",
          "BGRQ",
          "D_ZTZH_JHKGRQ",
          "D_ZTZH_JHYSRQ"
        ],
        "project": [
          "XMID",
          "D_JCLY_XMMC",
          "D_JCLY_LXXMMC",
          "D_JCLY_LXXMMCID"
        ],
        "partner": [
          "f_JSDW",
          "JSDWXZID",
          "JSDWXZ"
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
      "table": "CGPT_T_Base_ZBXX_CB",
      "row_count": 9,
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
      "table": "CGPT_T_Base_ZBXX",
      "row_count": 6,
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
      "table": "T_HTGL_HTBG",
      "row_count": 5,
      "column_count": 37,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "YFKJE",
          "BGJE"
        ],
        "date": [
          "SJBMC",
          "LRSJ",
          "XGSJ",
          "BGRQ"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "JSDW"
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
      "table": "T_CollectionPlan_New",
      "row_count": 1,
      "column_count": 41,
      "classification": "candidate_effective_business_fact",
      "family": "t",
      "business_signal_score": 95,
      "signals": {
        "amount": [
          "BCCZJE",
          "JHSKJE",
          "SCWJHJE",
          "BCHJKYJE"
        ],
        "date": [
          "SJBMC",
          "DJRQ",
          "LRSJ",
          "XGRQ"
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
      "table": "GLFY_Dept",
      "row_count": 1674,
      "column_count": 58,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 90,
      "signals": {
        "amount": [
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName",
          "EnterprisePhone",
          "EnterpriseFax"
        ],
        "date": [
          "SJBMC",
          "createUserID",
          "createUserName",
          "createDate",
          "modifyDate",
          "IsAutoCreate"
        ],
        "project": [
          "XMID",
          "XMMC"
        ],
        "partner": [
          "GYSZT"
        ],
        "deleted": [
          "isDelete"
        ]
      }
    },
    {
      "schema": "dbo",
      "table": "T_CGHT_CGDD",
      "row_count": 4,
      "column_count": 41,
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
          "KDGSJP",
          "HTQDRQ"
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
          "HTID",
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
      "column_count": 45,
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
          "KDGSJP",
          "QRRQ"
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
      "table": "T_JH_CGJH",
      "row_count": 2,
      "column_count": 70,
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
      "table": "GLFY_Type",
      "row_count": 2613,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 80,
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
          "isDelete",
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
      "table": "BGGL_ZTBJHT_TBBM_TBBMFSQ",
      "row_count": 122,
      "column_count": 40,
      "classification": "candidate_effective_business_fact",
      "family": "office_admin",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "JE"
        ],
        "date": [
          "SJBMC",
          "SQRQ",
          "ZCFKRQ",
          "LRSJ",
          "XGSJ"
        ],
        "project": [
          "XMID",
          "XMMC",
          "TBXMMC"
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
      "table": "A_SCBS_JXD",
      "row_count": 37,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "a",
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
      "table": "LW_LWFD_KQB_CB",
      "row_count": 25,
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
      "table": "SGGL_FBGL_MonthPlanContent",
      "row_count": 16,
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
      "table": "GLFY_Content",
      "row_count": 14,
      "column_count": 43,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "costPrice",
          "createUserID",
          "createUserName",
          "modifyUserID",
          "modifyUserName",
          "costJE",
          "FTJE",
          "JE_NO",
          "SE"
        ],
        "date": [
          "SJBMC",
          "costDate",
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
          "billId",
          "pid"
        ],
        "deleted": [
          "DEL"
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
      "table": "SGGL_FBGL_MonthPlan",
      "row_count": 11,
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
      "table": "A_SCBS_RYGZD",
      "row_count": 8,
      "column_count": 23,
      "classification": "candidate_effective_business_fact",
      "family": "a",
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
      "table": "GLFY_GLRYGZB_CB",
      "row_count": 8,
      "column_count": 41,
      "classification": "candidate_effective_business_fact",
      "family": "labor_subcontract",
      "business_signal_score": 75,
      "signals": {
        "amount": [
          "ProjectName",
          "ProjectId"
        ],
        "date": [
          "SJBMC",
          "BSJ"
        ],
        "project": [
          "XMID",
          "ProjectName",
          "ProjectId"
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
    }
  ]
}
```

## Top Candidate Tables

| Table | Rows | Classification | Score | Signals |
|---|---:|---|---:|---|
| YSZJ_CZBS_CZQDBS | 4 | candidate_effective_business_fact | 115 | amount:BCJFSDHSE/LJSDHSE, date:SJBMC/TBRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:JSDW, contract:HTMC, parent:pid, deleted:DEL |
| WS_HTGL_ZBHT | 2 | candidate_effective_business_fact | 115 | amount:ZBJE/BZJJE/ZBJJE, date:SJBMC/QYRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:SGDWID, contract:HTBH, parent:pid, deleted:DEL |
| T_ProjectContract_In | 4 | candidate_effective_business_fact | 105 | amount:f_LRJE/f_FXJDYJE/HTJE, date:SJBMC/f_KGRQ/f_MBZRSQDRQ/f_SJLR, project:XMID, partner:f_JSDW, contract:f_NBHTBH/f_NBHTBHZDY, deleted:SCRID/SCRQ/DEL |
| T_GYSHT_INFO_Ext_XAKW | 1 | candidate_effective_business_fact | 105 | amount:ZJE_DX/ZJE_NO_DX/SE_DX, date:SJBMC/JF_RQ/YF_RQ/DHQD_RQ, project:DHQD_XMMC, partner:T_GYSHT_INFO_Id, contract:T_GYSHT_INFO_Id |
| XMGL_HTGL_XMJSSQ | 55 | candidate_effective_business_fact | 95 | amount:YSKJE/JSJE/HTJE, date:SJBMC/JSJE/JSRQ/LRSJ, project:XMID/XMMC/D_JCLY_LXXMMC/D_JCLY_LXXMMCID, contract:ZBHTID/ZBHTBH, parent:pid, deleted:DEL |
| P_ZTB_GCXXGL | 20 | candidate_effective_business_fact | 95 | amount:XMJL_UserID/LXR_UserID/BZJJE, date:SJBMC/f_DJRQ/f_LRSJ/XGRQ, project:XMID/D_JCLY_XMMC/D_JCLY_LXXMMC/D_JCLY_LXXMMCID, partner:f_JSDW/JSDWXZID/JSDWXZ, parent:PID, deleted:SCRID/SCRQ/DEL |
| CGPT_T_Base_ZBXX_CB | 9 | candidate_effective_business_fact | 95 | amount:ZJE, date:SJBMC/BJKSSJ/BJJZSJ, project:XMID/XMMC, partner:ZBDWID, parent:ZBID/pid |
| T_FK_Supplier_SD | 7 | candidate_effective_business_fact | 95 | amount:f_FKJE/f_FPJE/f_LDJE, date:SJBMC/f_FKRQ/f_LRSJ, project:f_XMID, partner:f_SupplierID/f_SupplierName/f_CBFLID, parent:f_ZFSQGLId/pid, deleted:DEL |
| CGPT_T_Base_ZBXX | 6 | candidate_effective_business_fact | 95 | amount:D_XYLG_ZBJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:ZBDWID, parent:pid, deleted:DEL |
| T_Project_GCQZD | 6 | candidate_effective_business_fact | 95 | amount:SJJE, date:SJBMC/SJ/SJJE/LRSJ, project:XMID/XMMC, partner:JSDWID/JSDW/JLDWID, parent:pid, deleted:DEL |
| XMGL_SRHT_QTSRHT | 6 | candidate_effective_business_fact | 95 | amount:SSJE, date:SJBMC/DJRQ/SSJE/LRSJ, project:XMID/XMMC, partner:GMDWID, parent:PID, deleted:DEL |
| T_HTGL_HTBG | 5 | candidate_effective_business_fact | 95 | amount:YFKJE/BGJE, date:SJBMC/LRSJ/XGSJ/BGRQ, project:XMID/XMMC, partner:JSDW, parent:pid, deleted:DEL |
| T_SC_SCD | 4 | candidate_effective_business_fact | 95 | amount:CPJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, partner:YLLLDWID/CPRKDWID/CPJSDWID/CPJSDWMC, parent:Pid, deleted:DEL |
| WS_ZBJGL_ZBJ | 4 | candidate_effective_business_fact | 95 | amount:ZBJJE, date:SJBMC/Date/LRSJ/XGSJ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| BGGL_QT_HTHS | 3 | candidate_effective_business_fact | 95 | amount:HTJE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, contract:HTBH/HTMC, parent:pid, deleted:DEL |
| WS_BDGL_TZEGL | 3 | candidate_effective_business_fact | 95 | amount:GSZJE/GSFBDZGYSJE, date:SJBMC/GSFBDZGYSJE/GSJAGCF, project:XMID/XMMC, partner:GSFBDZGYSJE, parent:pid, deleted:DEL |
| WS_ZBJGL_BZJ | 3 | candidate_effective_business_fact | 95 | amount:ZBJJE, date:SJBMC/Date/LRSJ/XGSJ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| WS_ZJJLTZ_ZFTZ | 3 | candidate_effective_business_fact | 95 | amount:ZFJE/KHBLKJE/FPJE, date:SJBMC/LRSJ/XGSJ/ZFRQ, project:XMID/XMMC, partner:SGDWID, parent:pid, deleted:DEL |
| XM_SBBF | 3 | candidate_effective_business_fact | 95 | amount:BFTBJE, date:SJBMC/BFRQ/LRSJ/XGRQ, project:XMID/XMMC, partner:JSDWID/JSDW, parent:pid, deleted:SCRID/SCRQ/DEL |
| SGGL_HJJC_HJCF | 2 | candidate_effective_business_fact | 95 | amount:CFJE, date:SJBMC/CFSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:BCFDWID, parent:pid |
| CGPT_T_Base_HZDWKC_CL | 1 | candidate_effective_business_fact | 95 | amount:T_Base_SupplierInfo_ID, date:SJBMC/KCRQ/LRSJ/XGSJ, project:XMMC/XMID, partner:T_Base_SupplierInfo_ID, parent:pid, deleted:DEL |
| CGPT_T_Base_HZDWKC_LW | 1 | candidate_effective_business_fact | 95 | amount:LW_Base_LWDWSZ_ID, date:SJBMC/KCRQ/LRSJ/XGSJ, project:XMMC/XMID, partner:LWFBFWZL/LWFBFWZL_1/LWFBFWZL_2, parent:pid, deleted:DEL |
| P_ZTB_GCJCGL | 1 | candidate_effective_business_fact | 95 | amount:D_DCYL_YSJE, date:SJBMC/f_ZBBMSJ/f_TBJZSJ/f_KBSJ, project:XMID, partner:f_JSDW/ZBDWID, parent:PID, deleted:SCRID/SCRQ/DEL |
| T_CollectionPlan_New | 1 | candidate_effective_business_fact | 95 | amount:BCCZJE/JHSKJE/SCWJHJE/BCHJKYJE, date:SJBMC/DJRQ/LRSJ/XGRQ, project:XMID/XMMC, contract:HTBH, parent:PID, deleted:DEL |
| WS_HTGL_HTBG | 1 | candidate_effective_business_fact | 95 | amount:WS_HTGL_ZBHT_JE/JEBG, date:SJBMC/QYRQ/LRSJ/XGSJ, project:XMID/XMMC, contract:HTBH, parent:pid, deleted:DEL |
| GLFY_Dept | 1674 | candidate_effective_business_fact | 90 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, partner:GYSZT, deleted:isDelete |
| T_CGHT_CGDD | 4 | candidate_effective_business_fact | 85 | date:SJBMC/CGRQ/JHRQ/LRSJ, project:XMID/XMMC, partner:ZBGYSID/ZBGYSMC, contract:HTID/HTBH, parent:pid, deleted:DEL |
| T_CG_CGDD | 3 | candidate_effective_business_fact | 85 | date:SJBMC/CGRQ/JHRQ/LRSJ, project:XMID/XMMC, partner:ZBGYSID/ZBGYSMC, contract:D_BYK_CGHTBH/D_BYK_CGHTID, parent:pid, deleted:DEL |
| SGGL_JBXXGL | 2 | candidate_effective_business_fact | 85 | date:SJBMC/JHJGRQ/SJKGRQ/LRSJ, project:XMID/XMMC, partner:JSDW, contract:HTBH, parent:pid, deleted:DEL |
| T_JH_CGJH | 2 | candidate_effective_business_fact | 85 | amount:CG_ZJE/ZJEHJ, date:SJBMC/DJRQ/LRSJ/XGRQ, project:f_XMID/XMMC/GLXMMC, partner:GYSID/GYSMC/LLDWID, deleted:SCRID/SCRQ/DEL |
| T_ZJZC_DB | 1 | candidate_effective_business_fact | 85 | date:SJBMC/LRRQ/SHRQ/CJRQ, project:XMID, partner:Supplier_ID/GYSName/DBDWID, contract:HTBH, parent:pid, deleted:DEL |
| YSZJ_XMCZ_GCBGTZ | 1 | candidate_effective_business_fact | 85 | date:SJBMC/FQSJ/LRSJ/XGSJ, project:XMID/XMMC, partner:FQDWID, contract:HTBH, parent:pid, deleted:DEL |
| BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER | 4915 | candidate_effective_business_fact | 80 | amount:USERID/USERNAME, date:RZRQ/ISJZ/SYNC_GROUP_DATE, project:XMID, parent:PID, deleted:DEL |
| GLFY_Type | 2613 | candidate_effective_business_fact | 80 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete/DEL |
| ZLGL_Base_DataManager | 1817 | candidate_effective_business_fact | 80 | amount:ZLGL_Base_ZLLX_Id/ZLGL_Base_ZLLX_Name, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_Base_NKCLKMSZ | 856 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/CLSJGUID/CLSJCODE/CLSJMC, project:XMID/XMMC, parent:pid |
| DataSpider_ScjstProjectRoughInfo | 219 | candidate_effective_business_fact | 75 | amount:ProjectRoles/ProjectNumber/ProjectName/ScjstProjectInfoId, date:SJBMC/LRSJ/XGSJ, project:ProjectRoles/ProjectNumber/ProjectName/ScjstProjectInfoId, parent:pid, deleted:del |
| D_SCBSJS_BGGL_XZ_SBRY | 167 | candidate_effective_business_fact | 75 | amount:YLJE/SYJE/GSJE, date:DJRQ/LRSJ/XGSJ/GSJE, project:XMID/XMMC, parent:PID, deleted:DEL |
| BGGL_ZTBJHT_TBBM_TBBMFSQ | 122 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/SQRQ/ZCFKRQ/LRSJ, project:XMID/XMMC/TBXMMC, parent:pid, deleted:DEL |
| BGGL_XZ_BZ | 115 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| BGGL_HBZJ_GZZB | 90 | candidate_effective_business_fact | 75 | amount:Userid, date:SJBMC/Star_RQ/End_RQ/LRSJ, project:XMMC/XMID, parent:pid, deleted:DEL |
| Pm_base_Person | 80 | candidate_effective_business_fact | 75 | amount:IsProjectPerson/IsBuySecurity/UseridOther, date:SJBMC/RDSJ/CJGZSJ/BYSJ, project:IsProjectPerson, parent:FaceBillId, deleted:Del/WX_SCRID |
| A_SCBS_JXD | 37 | candidate_effective_business_fact | 75 | amount:JE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| SGGL_DataTypeSet | 35 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId |
| YSZJ_CZBS_CZQDBS_CB_CB | 34 | candidate_effective_business_fact | 75 | amount:BSJE/HDJE/LJJE, date:SJBMC/BSJE, project:QDXMMC, parent:pid |
| LW_LWFD_KQB_CB | 25 | candidate_effective_business_fact | 75 | amount:SEX, date:SJBMC/SJH, project:XMID, parent:ZBID/pid |
| SGGL_Node | 25 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/startDate/endDate/createUserID, project:XMID/XMMC, parent:parentId |
| T_Base_NKFBKMSZ | 18 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/FBSJGUID, project:XMID/XMMC, parent:pid |
| PJ_Type_MB | 16 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete |
| SGGL_FBGL_MonthPlanContent | 16 | candidate_effective_business_fact | 75 | amount:planPrice/planMoney/createUserID/createUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:pid |
| GLFY_Content | 14 | candidate_effective_business_fact | 75 | amount:costPrice/createUserID/createUserName/modifyUserID, date:SJBMC/costDate/createUserID/createUserName, project:XMID/XMMC, parent:billId/pid, deleted:DEL |
| XMGL_JJSB_ZLD_LXYG_CB | 12 | candidate_effective_business_fact | 75 | amount:JE/JE_NO/SE, date:SJBMC/RQ/QZSJ_KS/QZSJ_JZ, project:XMMC, parent:ZBID/pid |
| SGGL_FBGL_MonthPlan | 11 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/billDate/createUserID/createUserName, project:XMID/XMMC, parent:pid, deleted:DEL |
| T_Base_NKGZKMSZ | 11 | candidate_effective_business_fact | 75 | amount:SFJEKZ, date:SJBMC/GZSJGUID, project:XMID/XMMC, parent:pid |
| A_SCBS_RYGZD | 8 | candidate_effective_business_fact | 75 | amount:ZJE, date:SJBMC/DJRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:pid, deleted:DEL |
| CWGL_CLBX_CB | 8 | candidate_effective_business_fact | 75 | amount:JTFJE/CCJE, date:SJBMC/QSSJ/JSSJ/D_JCLY_CCSJ, project:CCXMMC, parent:pid/ZBID |
| GLFY_GLRYGZB_CB | 8 | candidate_effective_business_fact | 75 | amount:ProjectName/ProjectId, date:SJBMC/BSJ, project:XMID/ProjectName/ProjectId, parent:ZBID/pid |
| PJ_Content | 7 | candidate_effective_business_fact | 75 | amount:inBillMoney/outBillMoney/createUserID/createUserName, date:SJBMC/billDate/createUserID/createUserName, project:XMID/XMMC, parent:billId, deleted:DEL |
| BGOA_BGYPSQ | 6 | candidate_effective_business_fact | 75 | amount:YGZJE/DXJE, date:SJBMC/SQRQ/LRSJ/XGSJ, project:XMID/XMMC, parent:PID, deleted:DEL |
| PJ_Type | 6 | candidate_effective_business_fact | 75 | amount:createUserID/createUserName/modifyUserID/modifyUserName, date:SJBMC/createUserID/createUserName/createDate, project:XMID/XMMC, parent:parentId, deleted:isDelete |

## Top Candidate Families

| Family | Tables | Rows | Effective Tables | Top Tables |
|---|---:|---:|---:|---|
| pm | 5 | 21773 | 1 | Pm_base_Person(80), Pm_Person_Department_PDuty(102), Pm_Person_Department(786), Pm_base_Person_RYXQSQ(1), PM_RYYDGL(20804) |
| t | 63 | 19166 | 25 | T_GYSHT_INFO_Ext_XAKW(1), T_FK_Supplier_SD(7), T_HTGL_HTBG(5), T_SC_SCD(4), T_CollectionPlan_New(1) |
| cgpt | 7 | 9519 | 3 | CGPT_T_Base_HZDWKC_CL(1), CGPT_T_Base_HZDWKC_LW(1), CGPT_T_Base_HZDWKC_FB(1), CGPT_T_Base_SupplierUser(1), CGPT_Base_JCCLK(9499) |
| office_admin | 38 | 5779 | 11 | BGGL_QT_HTHS(3), BGGL_ZTBJHT_TBBM_TBBMFSQ(122), BGGL_XZ_BZ(115), BGGL_HBZJ_GZZB(90), BGGL_HBZJ_QT_GCBXGMJL(4) |
| labor_subcontract | 42 | 5147 | 19 | GLFY_Dept(1674), GLFY_Type(2613), LW_LWFD_KQB_CB(25), SGGL_FBGL_MonthPlanContent(16), GLFY_Content(14) |
| base | 3 | 5044 | 2 | BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER(4915), BASE_SYSTEM_WZCLKGXSZ(4), BASE_APP_COMMONOLDUSER(125) |
| zlgl | 3 | 1994 | 1 | ZLGL_Base_DataManager(1817), ZLGL_Base_ZLLXAndQX(156), ZLGL_Base_ZLLX_New(21) |
| sgbw | 1 | 1439 | 0 | SGBW_QDKM(1439) |
| sggl | 32 | 1172 | 15 | SGGL_HJJC_HJCF(2), SGGL_JBXXGL(2), SGGL_DataTypeSet(35), SGGL_Node(25), SGGL_GCJBQKB(1) |
| a | 10 | 820 | 4 | A_SCBS_JXD(37), A_SCBS_RYGZD(8), A_SCBS_CLCKD(1), A_SCBS_FYD(1), A_SCBS_JXD_CB(40) |
| dataspider | 3 | 469 | 1 | DataSpider_ScjstProjectRoughInfo(219), DataSpider_ScjstPersonInfo(54), DataSpider_ScjstPersonCertificate(196) |
| cwgl | 6 | 432 | 2 | CWGL_CLBX_CB(8), CWGL_CLBX(2), CWGL_FYBX_SKDW(1), CWGL_SQGL_CCSQ(177), CWGL_DZFPK(79) |
| gzgl | 1 | 389 | 0 | GZGL_BMSJWH(389) |
| jhjrz | 5 | 344 | 1 | JHJRZ_GZHB(3), JHJRZ_FBRW_CB(96), JHJRZ_FBRW(31), JHJRZ_FBRW_BLXQ(9), JHJRZ_RWCKJLB(205) |
| lease_equipment | 15 | 237 | 7 | XMGL_JJSB_ZLD_LXYG_CB(12), T_ZL_ZLJSD_CB_JX(11), T_ZL_ZLJSD_CB(10), T_ZL_ZRDCB_JX(6), T_ZL_ZRDCB(1) |
| d | 8 | 231 | 3 | D_SCBSJS_BGGL_XZ_SBRY(167), D_HLCSXT_T_CollectionPlan_New_CB(1), D_YWXT_XM_SGGL_SGZLGL_JGZL(2), D_SCBSJS_ZJ_ZJSZ_JCSZ_YHLS_CB(53), D_SCBSJS_SW_JC_GSPTFP_CB(3) |
| xmgl | 14 | 182 | 9 | XMGL_SRHT_QTSRHT(6), XMGL_JJSB_ZLJH_JXYGSQ(2), XMGL_RKGL_SHLQYSD_CB(2), XMGL_RKGL_YSD_CB(2), XMGL_JJSB_ZLJH_JXYGSQ_CB(4) |
| material_stock | 8 | 74 | 0 | A_SCBS_CLRKD_CB(46), YT_JGZS_SGLKYSZB_CSCB(2), YT_JGZS_SGLKYSZB_QD(12), YT_JGZS_SGLKYSZB(8), YT_JGZS_SGLKYSZB_CS(2) |
| project_settlement | 6 | 74 | 5 | T_ProjectContract_In(4), XMGL_HTGL_XMJSSQ(55), T_Project_GCQZD(6), XM_SBBF(3), T_ProjectContract_Process(1) |
| xm | 8 | 52 | 6 | XM_SBZJ_CB(3), XM_SBRC(20), XM_SBSY(10), XM_SBGH(7), XM_SBZY(4) |

## Boundary

- Read-only legacy DB scan
- DB writes: `0`
- This is a table/column signal screen; every candidate still needs lane-level SQL and replay mapping before ingestion.

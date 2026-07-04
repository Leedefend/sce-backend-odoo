# Legacy DB Remaining Business Fact Family Screen v1

Status: `PASS`

Source: `legacy-mssql-restore:LegacyDb`

## Summary

```json
{
  "screened_tables": 78,
  "screened_rows": 10479,
  "screened_active_rows": 10438,
  "families": [
    {
      "family": "labor_subcontract",
      "tables": 12,
      "rows": 4787,
      "active_rows": 4787,
      "amount_columns": 31,
      "top_tables": [
        {
          "table": "GLFY_Dept",
          "rows": 1674,
          "active_rows": 1674,
          "score": 90
        },
        {
          "table": "GLFY_Type",
          "rows": 2613,
          "active_rows": 2613,
          "score": 80
        },
        {
          "table": "LW_LWFD_KQB_CB",
          "rows": 25,
          "active_rows": 25,
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlanContent",
          "rows": 16,
          "active_rows": 16,
          "score": 75
        },
        {
          "table": "GLFY_Content",
          "rows": 14,
          "active_rows": 14,
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlan",
          "rows": 11,
          "active_rows": 11,
          "score": 75
        },
        {
          "table": "GLFY_GLRYGZB_CB",
          "rows": 8,
          "active_rows": 8,
          "score": 75
        },
        {
          "table": "LW_Base_FDGL_YLYS",
          "rows": 4,
          "active_rows": 4,
          "score": 75
        },
        {
          "table": "LW_Base_LWDWSZ",
          "rows": 195,
          "active_rows": 195,
          "score": 70
        },
        {
          "table": "T_JS_LWJSD_CB",
          "rows": 137,
          "active_rows": 137,
          "score": 70
        },
        {
          "table": "LW_Base_FDGLCB",
          "rows": 74,
          "active_rows": 74,
          "score": 70
        },
        {
          "table": "T_JS_CLJSD_CB",
          "rows": 16,
          "active_rows": 16,
          "score": 70
        }
      ]
    },
    {
      "family": "office_admin",
      "tables": 12,
      "rows": 3923,
      "active_rows": 3884,
      "amount_columns": 10,
      "top_tables": [
        {
          "table": "BGGL_XZD_YZSYSPB",
          "rows": 1565,
          "active_rows": 1565,
          "score": 100
        },
        {
          "table": "BGGL_QT_HTHS",
          "rows": 3,
          "active_rows": 3,
          "score": 95
        },
        {
          "table": "BGGL_HBZJ_XZD_QJXJSPB",
          "rows": 347,
          "active_rows": 339,
          "score": 75
        },
        {
          "table": "BGGL_ZTBJHT_TBBM_TBBMFSQ",
          "rows": 122,
          "active_rows": 115,
          "score": 75
        },
        {
          "table": "BGGL_XZ_BZ",
          "rows": 115,
          "active_rows": 100,
          "score": 75
        },
        {
          "table": "BGGL_HBZJ_GZZB",
          "rows": 90,
          "active_rows": 90,
          "score": 75
        },
        {
          "table": "BGGL_QSJRW_GZQS",
          "rows": 53,
          "active_rows": 53,
          "score": 75
        },
        {
          "table": "BGGL_HBZJ_QT_GCBXGMJL",
          "rows": 4,
          "active_rows": 4,
          "score": 75
        },
        {
          "table": "BGGL_QT_GCBGTZD",
          "rows": 2,
          "active_rows": 2,
          "score": 75
        },
        {
          "table": "BGGL_BMYS_BMQTZCDJ",
          "rows": 1,
          "active_rows": 1,
          "score": 75
        },
        {
          "table": "BGGL_TZXX_WJPYCJ",
          "rows": 1616,
          "active_rows": 1607,
          "score": 70
        },
        {
          "table": "BGGL_JHK_HKDJ_CB",
          "rows": 5,
          "active_rows": 5,
          "score": 70
        }
      ]
    },
    {
      "family": "t",
      "tables": 12,
      "rows": 913,
      "active_rows": 911,
      "amount_columns": 13,
      "top_tables": [
        {
          "table": "T_GYSHT_INFO_Ext_XAKW",
          "rows": 1,
          "active_rows": 1,
          "score": 105
        },
        {
          "table": "T_FK_Supplier_SD",
          "rows": 7,
          "active_rows": 7,
          "score": 95
        },
        {
          "table": "T_HTGL_HTBG",
          "rows": 5,
          "active_rows": 5,
          "score": 95
        },
        {
          "table": "T_SC_SCD",
          "rows": 4,
          "active_rows": 4,
          "score": 95
        },
        {
          "table": "T_CollectionPlan_New",
          "rows": 1,
          "active_rows": 0,
          "score": 95
        },
        {
          "table": "T_CGHT_CGDD",
          "rows": 4,
          "active_rows": 4,
          "score": 85
        },
        {
          "table": "T_CG_CGDD",
          "rows": 3,
          "active_rows": 3,
          "score": 85
        },
        {
          "table": "T_JH_CGJH",
          "rows": 2,
          "active_rows": 1,
          "score": 85
        },
        {
          "table": "T_ZJZC_DB",
          "rows": 1,
          "active_rows": 1,
          "score": 85
        },
        {
          "table": "T_Base_NKCLKMSZ",
          "rows": 856,
          "active_rows": 856,
          "score": 75
        },
        {
          "table": "T_Base_NKFBKMSZ",
          "rows": 18,
          "active_rows": 18,
          "score": 75
        },
        {
          "table": "T_Base_NKGZKMSZ",
          "rows": 11,
          "active_rows": 11,
          "score": 75
        }
      ]
    },
    {
      "family": "cwgl",
      "tables": 6,
      "rows": 432,
      "active_rows": 432,
      "amount_columns": 5,
      "top_tables": [
        {
          "table": "CWGL_CLBX_CB",
          "rows": 8,
          "active_rows": 8,
          "score": 75
        },
        {
          "table": "CWGL_CLBX",
          "rows": 2,
          "active_rows": 2,
          "score": 75
        },
        {
          "table": "CWGL_FYBX_SKDW",
          "rows": 1,
          "active_rows": 1,
          "score": 50
        },
        {
          "table": "CWGL_SQGL_CCSQ",
          "rows": 177,
          "active_rows": 177,
          "score": 45
        },
        {
          "table": "CWGL_DZFPK",
          "rows": 79,
          "active_rows": 79,
          "score": 45
        },
        {
          "table": "CWGL_SQGL_CCSQ_CB",
          "rows": 165,
          "active_rows": 165,
          "score": 20
        }
      ]
    },
    {
      "family": "lease_equipment",
      "tables": 12,
      "rows": 226,
      "active_rows": 226,
      "amount_columns": 20,
      "top_tables": [
        {
          "table": "XMGL_JJSB_ZLD_LXYG_CB",
          "rows": 12,
          "active_rows": 12,
          "score": 75
        },
        {
          "table": "T_ZL_ZLJSD_CB_JX",
          "rows": 11,
          "active_rows": 11,
          "score": 70
        },
        {
          "table": "T_ZL_ZLJSD_CB",
          "rows": 10,
          "active_rows": 10,
          "score": 70
        },
        {
          "table": "T_ZL_ZRDCB_JX",
          "rows": 6,
          "active_rows": 6,
          "score": 70
        },
        {
          "table": "T_ZL_ZRDCB",
          "rows": 1,
          "active_rows": 1,
          "score": 70
        },
        {
          "table": "T_ZL_ZLJH",
          "rows": 5,
          "active_rows": 5,
          "score": 65
        },
        {
          "table": "T_ZL_ZLJH_JX",
          "rows": 4,
          "active_rows": 4,
          "score": 65
        },
        {
          "table": "HTGL_ZLHT_ZLDW_Yhzhxx",
          "rows": 27,
          "active_rows": 27,
          "score": 55
        },
        {
          "table": "HTGL_ZLHT_ZLHT_CB_JX",
          "rows": 55,
          "active_rows": 55,
          "score": 50
        },
        {
          "table": "T_ZL_MachineShift_CB",
          "rows": 53,
          "active_rows": 53,
          "score": 50
        },
        {
          "table": "HTGL_ZLHT_ZLHT_CB",
          "rows": 33,
          "active_rows": 33,
          "score": 50
        },
        {
          "table": "T_ZL_ZLJH_ZLSQ_CB",
          "rows": 9,
          "active_rows": 9,
          "score": 50
        }
      ]
    },
    {
      "family": "material_stock",
      "tables": 8,
      "rows": 74,
      "active_rows": 74,
      "amount_columns": 8,
      "top_tables": [
        {
          "table": "A_SCBS_CLRKD_CB",
          "rows": 46,
          "active_rows": 46,
          "score": 50
        },
        {
          "table": "YT_JGZS_SGLKYSZB_CSCB",
          "rows": 2,
          "active_rows": 2,
          "score": 50
        },
        {
          "table": "YT_JGZS_SGLKYSZB_QD",
          "rows": 12,
          "active_rows": 12,
          "score": 45
        },
        {
          "table": "YT_JGZS_SGLKYSZB",
          "rows": 8,
          "active_rows": 8,
          "score": 45
        },
        {
          "table": "YT_JGZS_SGLKYSZB_CS",
          "rows": 2,
          "active_rows": 2,
          "score": 45
        },
        {
          "table": "ZYJX_ZY_T_WZJJF_SBZLD_CB",
          "rows": 2,
          "active_rows": 2,
          "score": 40
        },
        {
          "table": "ZYJX_ZY_T_WZJJF_SBHZD_CB",
          "rows": 1,
          "active_rows": 1,
          "score": 40
        },
        {
          "table": "ZYJX_ZY_T_WZJJF_ZLHT_CB",
          "rows": 1,
          "active_rows": 1,
          "score": 40
        }
      ]
    },
    {
      "family": "project_settlement",
      "tables": 6,
      "rows": 74,
      "active_rows": 74,
      "amount_columns": 7,
      "top_tables": [
        {
          "table": "T_ProjectContract_In",
          "rows": 4,
          "active_rows": 4,
          "score": 105
        },
        {
          "table": "XMGL_HTGL_XMJSSQ",
          "rows": 55,
          "active_rows": 55,
          "score": 95
        },
        {
          "table": "T_Project_GCQZD",
          "rows": 6,
          "active_rows": 6,
          "score": 95
        },
        {
          "table": "XM_SBBF",
          "rows": 3,
          "active_rows": 3,
          "score": 95
        },
        {
          "table": "T_ProjectContract_Process",
          "rows": 1,
          "active_rows": 1,
          "score": 65
        },
        {
          "table": "T_ProjectContract_Out_CB_BZJ",
          "rows": 5,
          "active_rows": 5,
          "score": 50
        }
      ]
    },
    {
      "family": "bid_tender",
      "tables": 10,
      "rows": 50,
      "active_rows": 50,
      "amount_columns": 13,
      "top_tables": [
        {
          "table": "WS_HTGL_ZBHT",
          "rows": 2,
          "active_rows": 2,
          "score": 115
        },
        {
          "table": "P_ZTB_GCXXGL",
          "rows": 20,
          "active_rows": 20,
          "score": 95
        },
        {
          "table": "CGPT_T_Base_ZBXX_CB",
          "rows": 9,
          "active_rows": 9,
          "score": 95
        },
        {
          "table": "CGPT_T_Base_ZBXX",
          "rows": 6,
          "active_rows": 6,
          "score": 95
        },
        {
          "table": "WS_ZBJGL_ZBJ",
          "rows": 4,
          "active_rows": 4,
          "score": 95
        },
        {
          "table": "WS_BDGL_TZEGL",
          "rows": 3,
          "active_rows": 3,
          "score": 95
        },
        {
          "table": "WS_ZBJGL_BZJ",
          "rows": 3,
          "active_rows": 3,
          "score": 95
        },
        {
          "table": "P_ZTB_GCJCGL",
          "rows": 1,
          "active_rows": 1,
          "score": 95
        },
        {
          "table": "P_ZTB_ZBGCJD",
          "rows": 1,
          "active_rows": 1,
          "score": 65
        },
        {
          "table": "P_ZTB_CustomerProfile",
          "rows": 1,
          "active_rows": 1,
          "score": 50
        }
      ]
    }
  ]
}
```

## Families

| Family | Tables Screened | Rows | Active Rows | Amount Columns | Top Tables |
|---|---:|---:|---:|---:|---|
| labor_subcontract | 12 | 4787 | 4787 | 31 | GLFY_Dept, GLFY_Type, LW_LWFD_KQB_CB, SGGL_FBGL_MonthPlanContent, GLFY_Content |
| office_admin | 12 | 3923 | 3884 | 10 | BGGL_XZD_YZSYSPB, BGGL_QT_HTHS, BGGL_HBZJ_XZD_QJXJSPB, BGGL_ZTBJHT_TBBM_TBBMFSQ, BGGL_XZ_BZ |
| t | 12 | 913 | 911 | 13 | T_GYSHT_INFO_Ext_XAKW, T_FK_Supplier_SD, T_HTGL_HTBG, T_SC_SCD, T_CollectionPlan_New |
| cwgl | 6 | 432 | 432 | 5 | CWGL_CLBX_CB, CWGL_CLBX, CWGL_FYBX_SKDW, CWGL_SQGL_CCSQ, CWGL_DZFPK |
| lease_equipment | 12 | 226 | 226 | 20 | XMGL_JJSB_ZLD_LXYG_CB, T_ZL_ZLJSD_CB_JX, T_ZL_ZLJSD_CB, T_ZL_ZRDCB_JX, T_ZL_ZRDCB |
| material_stock | 8 | 74 | 74 | 8 | A_SCBS_CLRKD_CB, YT_JGZS_SGLKYSZB_CSCB, YT_JGZS_SGLKYSZB_QD, YT_JGZS_SGLKYSZB, YT_JGZS_SGLKYSZB_CS |
| project_settlement | 6 | 74 | 74 | 7 | T_ProjectContract_In, XMGL_HTGL_XMJSSQ, T_Project_GCQZD, XM_SBBF, T_ProjectContract_Process |
| bid_tender | 10 | 50 | 50 | 13 | WS_HTGL_ZBHT, P_ZTB_GCXXGL, CGPT_T_Base_ZBXX_CB, CGPT_T_Base_ZBXX, WS_ZBJGL_ZBJ |

## Screened Tables

| Family | Table | Classification | Rows | Active Rows | Amount Sums |
|---|---|---|---:|---:|---|
| bid_tender | WS_HTGL_ZBHT | candidate_effective_business_fact | 2 | 2 | ZBJE=32324241.000000, BZJBL=12.000000, BZJJE=3232344.100000, ZBJJE=3232334.100000 |
| bid_tender | P_ZTB_GCXXGL | candidate_effective_business_fact | 20 | 20 | BZJJE=840000.000000 |
| bid_tender | CGPT_T_Base_ZBXX_CB | candidate_effective_business_fact | 9 | 9 | ZJE=447490.400000 |
| bid_tender | CGPT_T_Base_ZBXX | candidate_effective_business_fact | 6 | 6 |  |
| bid_tender | WS_ZBJGL_ZBJ | candidate_effective_business_fact | 4 | 4 | ZBJJE=14.000000 |
| bid_tender | WS_BDGL_TZEGL | candidate_effective_business_fact | 3 | 3 | GSZJE=2784364.000000, GSFBDZGYSJE=2756543.000000 |
| bid_tender | WS_ZBJGL_BZJ | candidate_effective_business_fact | 3 | 3 | ZBJJE=8.000000 |
| bid_tender | P_ZTB_GCJCGL | candidate_effective_business_fact | 1 | 1 | f_TBBZJJN=300000.000000, f_TBBZJTH=0.000000 |
| bid_tender | P_ZTB_ZBGCJD | candidate_effective_business_fact | 1 | 1 |  |
| bid_tender | P_ZTB_CustomerProfile | candidate_secondary_business_fact | 1 | 1 | XSJE=0.000000 |
| material_stock | A_SCBS_CLRKD_CB | candidate_secondary_business_fact | 46 | 46 | JE=566791.920000 |
| material_stock | YT_JGZS_SGLKYSZB_CSCB | candidate_secondary_business_fact | 2 | 2 | JE=27114.350000, JE_NO=0.000000, SE=0.000000 |
| material_stock | YT_JGZS_SGLKYSZB_QD | candidate_secondary_business_fact | 12 | 12 | QDHJ=558850.370000, HSHJ=0.000000 |
| material_stock | YT_JGZS_SGLKYSZB | candidate_secondary_business_fact | 8 | 8 | ZHJ=0.000000, ZNKHJ=10377073.600000 |
| material_stock | YT_JGZS_SGLKYSZB_CS | candidate_secondary_business_fact | 2 | 2 |  |
| material_stock | ZYJX_ZY_T_WZJJF_SBZLD_CB | candidate_secondary_business_fact | 2 | 2 |  |
| material_stock | ZYJX_ZY_T_WZJJF_SBHZD_CB | candidate_secondary_business_fact | 1 | 1 |  |
| material_stock | ZYJX_ZY_T_WZJJF_ZLHT_CB | candidate_secondary_business_fact | 1 | 1 |  |
| labor_subcontract | GLFY_Dept | candidate_effective_business_fact | 1674 | 1674 | createUserID=13120033283.000000, modifyUserID=170000417.000000 |
| labor_subcontract | GLFY_Type | candidate_effective_business_fact | 2613 | 2613 |  |
| labor_subcontract | LW_LWFD_KQB_CB | candidate_effective_business_fact | 25 | 25 |  |
| labor_subcontract | SGGL_FBGL_MonthPlanContent | candidate_effective_business_fact | 16 | 16 | planPrice=1002.000000, planMoney=5767644.000000 |
| labor_subcontract | GLFY_Content | candidate_effective_business_fact | 14 | 14 | costPrice=155869.000000, createUserID=130000001.000000, modifyUserID=0.000000, costJE=156124.000000 |
| labor_subcontract | SGGL_FBGL_MonthPlan | candidate_effective_business_fact | 11 | 11 |  |
| labor_subcontract | GLFY_GLRYGZB_CB | candidate_effective_business_fact | 8 | 8 | HJ=3069.000000 |
| labor_subcontract | LW_Base_FDGL_YLYS | candidate_effective_business_fact | 4 | 4 |  |
| labor_subcontract | LW_Base_LWDWSZ | candidate_effective_business_fact | 195 | 195 |  |
| labor_subcontract | T_JS_LWJSD_CB | candidate_effective_business_fact | 137 | 137 | FDJE=1891074.820000, FDJE_NO=0.000000, GCLJJE=0.000000, JE=64120.000000 |
| labor_subcontract | LW_Base_FDGLCB | candidate_effective_business_fact | 74 | 74 | HJGZ=834705.000000, SQHJ=0.000000, SE=14888.420000, JE_NO=313901.580000 |
| labor_subcontract | T_JS_CLJSD_CB | candidate_effective_business_fact | 16 | 16 | RKJE=20500.000000, RKJE_NO=0.000000, RKSE=0.000000, DZJE=0.000000 |
| lease_equipment | XMGL_JJSB_ZLD_LXYG_CB | candidate_effective_business_fact | 12 | 12 | JE=2810.000000, JE_NO=2810.000000, SE=0.000000 |
| lease_equipment | T_ZL_ZLJSD_CB_JX | candidate_effective_business_fact | 11 | 11 | DJJE=150066.460000, SJJSJE=157750.460000, JE=932.400000 |
| lease_equipment | T_ZL_ZLJSD_CB | candidate_effective_business_fact | 10 | 10 | DJJE=225159696.000000, SJJSJE=204164100.000000 |
| lease_equipment | T_ZL_ZRDCB_JX | candidate_effective_business_fact | 6 | 6 | JE_NO=0.000000, SE=0.000000, JE=0.000000 |
| lease_equipment | T_ZL_ZRDCB | candidate_effective_business_fact | 1 | 1 | JE=0.000000 |
| lease_equipment | T_ZL_ZLJH | candidate_effective_business_fact | 5 | 5 |  |
| lease_equipment | T_ZL_ZLJH_JX | candidate_effective_business_fact | 4 | 4 |  |
| lease_equipment | HTGL_ZLHT_ZLDW_Yhzhxx | candidate_secondary_business_fact | 27 | 27 |  |
| lease_equipment | HTGL_ZLHT_ZLHT_CB_JX | candidate_secondary_business_fact | 55 | 55 | f_HJ=965925.000000, JE_NO=1090.910000, SE=109.090000 |
| lease_equipment | T_ZL_MachineShift_CB | candidate_secondary_business_fact | 53 | 53 | JE=40383.900000 |
| lease_equipment | HTGL_ZLHT_ZLHT_CB | candidate_secondary_business_fact | 33 | 33 | f_HJ=39996.040000, JE_NO=37732.110000, SE=2263.930000 |
| lease_equipment | T_ZL_ZLJH_ZLSQ_CB | candidate_secondary_business_fact | 9 | 9 | JE=21300277971.000000 |
| project_settlement | T_ProjectContract_In | candidate_effective_business_fact | 4 | 4 | HTJE=0.000000 |
| project_settlement | XMGL_HTGL_XMJSSQ | candidate_effective_business_fact | 55 | 55 | YSKJE=149456571.110000, JSJE=172475195.140000, HTJE=46796778.030000 |
| project_settlement | T_Project_GCQZD | candidate_effective_business_fact | 6 | 6 | SJJE=1865.000000 |
| project_settlement | XM_SBBF | candidate_effective_business_fact | 3 | 3 | BFTBJE=3788.000000 |
| project_settlement | T_ProjectContract_Process | candidate_effective_business_fact | 1 | 1 |  |
| project_settlement | T_ProjectContract_Out_CB_BZJ | candidate_secondary_business_fact | 5 | 5 | JE=3053466.630000 |
| office_admin | BGGL_XZD_YZSYSPB | candidate_effective_business_fact | 1565 | 1565 | HTJE=0.000000 |
| office_admin | BGGL_QT_HTHS | candidate_effective_business_fact | 3 | 3 |  |
| office_admin | BGGL_HBZJ_XZD_QJXJSPB | candidate_effective_business_fact | 347 | 339 | IsSend=0.000000 |
| office_admin | BGGL_ZTBJHT_TBBM_TBBMFSQ | candidate_effective_business_fact | 122 | 115 | JE=45001.250000 |
| office_admin | BGGL_XZ_BZ | candidate_effective_business_fact | 115 | 100 | JE=9478.800000 |
| office_admin | BGGL_HBZJ_GZZB | candidate_effective_business_fact | 90 | 90 |  |
| office_admin | BGGL_QSJRW_GZQS | candidate_effective_business_fact | 53 | 53 | JE=0.000000 |
| office_admin | BGGL_HBZJ_QT_GCBXGMJL | candidate_effective_business_fact | 4 | 4 | BXJE=3461348062.000000 |
| office_admin | BGGL_QT_GCBGTZD | candidate_effective_business_fact | 2 | 2 | YGBGJE=25472.000000 |
| office_admin | BGGL_BMYS_BMQTZCDJ | candidate_effective_business_fact | 1 | 1 | ZCJE=5000.000000, PJJE=4900.000000 |
| office_admin | BGGL_TZXX_WJPYCJ | candidate_effective_business_fact | 1616 | 1607 |  |
| office_admin | BGGL_JHK_HKDJ_CB | candidate_effective_business_fact | 5 | 5 | HKJE=2020000.000000 |
| cwgl | CWGL_CLBX_CB | candidate_effective_business_fact | 8 | 8 | JTFJE=4063.000000, CCJE=60.000000 |
| cwgl | CWGL_CLBX | candidate_effective_business_fact | 2 | 2 | BXJE=2810.500000, SBJE=2810.500000 |
| cwgl | CWGL_FYBX_SKDW | candidate_secondary_business_fact | 1 | 1 | SKJE=1230.000000 |
| cwgl | CWGL_SQGL_CCSQ | candidate_secondary_business_fact | 177 | 177 |  |
| cwgl | CWGL_DZFPK | candidate_secondary_business_fact | 79 | 79 |  |
| cwgl | CWGL_SQGL_CCSQ_CB | candidate_needs_manual_screen | 165 | 165 |  |
| t | T_GYSHT_INFO_Ext_XAKW | candidate_effective_business_fact | 1 | 1 |  |
| t | T_FK_Supplier_SD | candidate_effective_business_fact | 7 | 7 | f_FKJE=941474.000000, f_FPJE=78.000000, f_LDJE=545.000000 |
| t | T_HTGL_HTBG | candidate_effective_business_fact | 5 | 5 | YFKJE=3534511111.000000, BGJE=5080312.000000, YSTZHJ=670000.000000 |
| t | T_SC_SCD | candidate_effective_business_fact | 4 | 4 | CPJE=0.000000 |
| t | T_CollectionPlan_New | candidate_effective_business_fact | 1 | 0 | BCCZJE=1.000000, JHSKJE=0.000000, SCWJHJE=0.000000, BCHJKYJE=0.000000 |
| t | T_CGHT_CGDD | candidate_effective_business_fact | 4 | 4 |  |
| t | T_CG_CGDD | candidate_effective_business_fact | 3 | 3 |  |
| t | T_JH_CGJH | candidate_effective_business_fact | 2 | 1 | CG_ZJE=0.000000, ZJEHJ=0.000000 |
| t | T_ZJZC_DB | candidate_effective_business_fact | 1 | 1 |  |
| t | T_Base_NKCLKMSZ | candidate_effective_business_fact | 856 | 856 |  |
| t | T_Base_NKFBKMSZ | candidate_effective_business_fact | 18 | 18 |  |
| t | T_Base_NKGZKMSZ | candidate_effective_business_fact | 11 | 11 |  |

## Boundary

- Read-only legacy DB screen
- DB writes: `0`
- This file is evidence for lane selection; it is not a replay payload.

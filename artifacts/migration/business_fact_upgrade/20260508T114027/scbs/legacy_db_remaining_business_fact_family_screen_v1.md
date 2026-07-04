# Legacy DB Remaining Business Fact Family Screen v1

Status: `PASS`

Source: `legacy-mssql-scbs:LegacyScbs20260417`

## Summary

```json
{
  "screened_tables": 76,
  "screened_rows": 11527,
  "screened_active_rows": 11484,
  "families": [
    {
      "family": "lease_equipment",
      "tables": 12,
      "rows": 6817,
      "active_rows": 6817,
      "amount_columns": 13,
      "top_tables": [
        {
          "table": "T_ZL_TBD",
          "rows": 5,
          "active_rows": 5,
          "score": 95
        },
        {
          "table": "XMGL_JJSB_ZLD_LXYG_CB",
          "rows": 9,
          "active_rows": 9,
          "score": 75
        },
        {
          "table": "T_ZL_ZLJSD_CB_JX",
          "rows": 713,
          "active_rows": 713,
          "score": 70
        },
        {
          "table": "T_ZL_ZLJSD_CB",
          "rows": 55,
          "active_rows": 55,
          "score": 70
        },
        {
          "table": "T_ZL_ZLJH",
          "rows": 20,
          "active_rows": 20,
          "score": 65
        },
        {
          "table": "T_ZL_RentalShift",
          "rows": 6,
          "active_rows": 6,
          "score": 65
        },
        {
          "table": "T_ZL_ZLJH_JX",
          "rows": 6,
          "active_rows": 6,
          "score": 65
        },
        {
          "table": "T_ZL_BTD_JX",
          "rows": 2,
          "active_rows": 2,
          "score": 65
        },
        {
          "table": "T_ZL_MachineShift_CB",
          "rows": 5959,
          "active_rows": 5959,
          "score": 55
        },
        {
          "table": "HTGL_ZLHT_ZLDW_Yhzhxx",
          "rows": 4,
          "active_rows": 4,
          "score": 55
        },
        {
          "table": "T_ZL_ZLJH_CB",
          "rows": 28,
          "active_rows": 28,
          "score": 50
        },
        {
          "table": "T_ZL_ZLJH_ZLSQ_CB",
          "rows": 10,
          "active_rows": 10,
          "score": 50
        }
      ]
    },
    {
      "family": "labor_subcontract",
      "tables": 12,
      "rows": 2826,
      "active_rows": 2826,
      "amount_columns": 20,
      "top_tables": [
        {
          "table": "T_JS_LWJSD_CB",
          "rows": 1175,
          "active_rows": 1175,
          "score": 75
        },
        {
          "table": "T_JS_CLJSD_CB",
          "rows": 1003,
          "active_rows": 1003,
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlanContent",
          "rows": 21,
          "active_rows": 21,
          "score": 75
        },
        {
          "table": "SGGL_FBGL_MonthPlan",
          "rows": 13,
          "active_rows": 13,
          "score": 75
        },
        {
          "table": "LW_LWFD_KQB_CB",
          "rows": 3,
          "active_rows": 3,
          "score": 75
        },
        {
          "table": "GLFY_Type",
          "rows": 1,
          "active_rows": 1,
          "score": 75
        },
        {
          "table": "GLFY_GLFYJSD_CB",
          "rows": 554,
          "active_rows": 554,
          "score": 70
        },
        {
          "table": "LW_Base_LWDWSZ",
          "rows": 1,
          "active_rows": 1,
          "score": 70
        },
        {
          "table": "SGGL_FBGL_MasterPlanContent",
          "rows": 33,
          "active_rows": 33,
          "score": 65
        },
        {
          "table": "SGGL_FBGL_MasterPlan",
          "rows": 15,
          "active_rows": 15,
          "score": 65
        },
        {
          "table": "LW_WPRYGZSPB",
          "rows": 4,
          "active_rows": 4,
          "score": 65
        },
        {
          "table": "LW_RYLWGZJSD",
          "rows": 3,
          "active_rows": 3,
          "score": 65
        }
      ]
    },
    {
      "family": "t",
      "tables": 12,
      "rows": 978,
      "active_rows": 935,
      "amount_columns": 18,
      "top_tables": [
        {
          "table": "T_JS_LLJSD",
          "rows": 18,
          "active_rows": 11,
          "score": 115
        },
        {
          "table": "T_ZJZC_ZB",
          "rows": 10,
          "active_rows": 0,
          "score": 115
        },
        {
          "table": "T_JS_XSJSD",
          "rows": 1,
          "active_rows": 1,
          "score": 115
        },
        {
          "table": "T_FK_Supplier_SD",
          "rows": 7,
          "active_rows": 7,
          "score": 95
        },
        {
          "table": "T_SC_SCD",
          "rows": 3,
          "active_rows": 3,
          "score": 95
        },
        {
          "table": "T_CGHT_HTPSB",
          "rows": 1,
          "active_rows": 1,
          "score": 95
        },
        {
          "table": "T_JH_CGJH",
          "rows": 51,
          "active_rows": 25,
          "score": 85
        },
        {
          "table": "T_CG_CGDD",
          "rows": 3,
          "active_rows": 3,
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
          "rows": 854,
          "active_rows": 854,
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
      "family": "c",
      "tables": 1,
      "rows": 696,
      "active_rows": 696,
      "amount_columns": 0,
      "top_tables": [
        {
          "table": "C_JFHKLR_CCB",
          "rows": 696,
          "active_rows": 696,
          "score": 40
        }
      ]
    },
    {
      "family": "office_admin",
      "tables": 12,
      "rows": 120,
      "active_rows": 120,
      "amount_columns": 7,
      "top_tables": [
        {
          "table": "BGGL_QT_HTHS",
          "rows": 2,
          "active_rows": 2,
          "score": 95
        },
        {
          "table": "BGGL_HBZJ_XZD_ZDYQSQ",
          "rows": 2,
          "active_rows": 2,
          "score": 75
        },
        {
          "table": "BGGL_QT_GCBGTZD",
          "rows": 2,
          "active_rows": 2,
          "score": 75
        },
        {
          "table": "BGGL_XZD_ZGSTKCTJB",
          "rows": 2,
          "active_rows": 2,
          "score": 75
        },
        {
          "table": "BGGL_JHK_HKDJ_CB",
          "rows": 83,
          "active_rows": 83,
          "score": 70
        },
        {
          "table": "BGGL_QSJRW_GZQS_CB",
          "rows": 4,
          "active_rows": 4,
          "score": 50
        },
        {
          "table": "BGGL_XZD_ZGSTKCTJB_CB",
          "rows": 3,
          "active_rows": 3,
          "score": 50
        },
        {
          "table": "BGGL_BGYP_Base_YPKM",
          "rows": 8,
          "active_rows": 8,
          "score": 45
        },
        {
          "table": "BGGL_XZ_JXDJ",
          "rows": 5,
          "active_rows": 5,
          "score": 45
        },
        {
          "table": "BGGL_HBZJ_XZD_JDSPD",
          "rows": 3,
          "active_rows": 3,
          "score": 45
        },
        {
          "table": "BGGL_XZ_JXDJ_ZB",
          "rows": 3,
          "active_rows": 3,
          "score": 45
        },
        {
          "table": "BGGL_ZCJYP_CL_SCGYSQ",
          "rows": 3,
          "active_rows": 3,
          "score": 45
        }
      ]
    },
    {
      "family": "bid_tender",
      "tables": 12,
      "rows": 32,
      "active_rows": 32,
      "amount_columns": 10,
      "top_tables": [
        {
          "table": "WS_HTGL_ZBHT",
          "rows": 2,
          "active_rows": 2,
          "score": 115
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
          "table": "CGPT_T_Base_ZBXX",
          "rows": 1,
          "active_rows": 1,
          "score": 95
        },
        {
          "table": "CGPT_T_Base_ZBXX_CB",
          "rows": 1,
          "active_rows": 1,
          "score": 95
        },
        {
          "table": "P_ZTB_ZZTB",
          "rows": 2,
          "active_rows": 2,
          "score": 75
        },
        {
          "table": "P_ZTB_TBQD_CB",
          "rows": 5,
          "active_rows": 5,
          "score": 50
        },
        {
          "table": "P_ZTB_CustomerProfile_CB",
          "rows": 3,
          "active_rows": 3,
          "score": 50
        },
        {
          "table": "P_ZTB_BSSB",
          "rows": 3,
          "active_rows": 3,
          "score": 45
        },
        {
          "table": "P_ZTB_SJFASB",
          "rows": 3,
          "active_rows": 3,
          "score": 45
        },
        {
          "table": "P_ZTB_TBDJ",
          "rows": 2,
          "active_rows": 2,
          "score": 45
        }
      ]
    },
    {
      "family": "material_stock",
      "tables": 5,
      "rows": 21,
      "active_rows": 21,
      "amount_columns": 4,
      "top_tables": [
        {
          "table": "T_RK_JCYSD",
          "rows": 6,
          "active_rows": 6,
          "score": 85
        },
        {
          "table": "T_RK_JCYSD_CB",
          "rows": 6,
          "active_rows": 6,
          "score": 50
        },
        {
          "table": "T_RK_TRSQ_CB",
          "rows": 4,
          "active_rows": 4,
          "score": 50
        },
        {
          "table": "T_RK_TRSQ",
          "rows": 4,
          "active_rows": 4,
          "score": 45
        },
        {
          "table": "T_CK_WasteMaterial",
          "rows": 1,
          "active_rows": 1,
          "score": 45
        }
      ]
    },
    {
      "family": "project_settlement",
      "tables": 3,
      "rows": 15,
      "active_rows": 15,
      "amount_columns": 3,
      "top_tables": [
        {
          "table": "T_Project_GCQZD",
          "rows": 6,
          "active_rows": 6,
          "score": 95
        },
        {
          "table": "XM_SBBF",
          "rows": 5,
          "active_rows": 5,
          "score": 95
        },
        {
          "table": "T_ProjectContract_Out_CB_BZJ",
          "rows": 4,
          "active_rows": 4,
          "score": 50
        }
      ]
    },
    {
      "family": "payment_fund",
      "tables": 3,
      "rows": 12,
      "active_rows": 12,
      "amount_columns": 4,
      "top_tables": [
        {
          "table": "ZJGL_BZJGL_Branch_SBZJTH_CB",
          "rows": 1,
          "active_rows": 1,
          "score": 95
        },
        {
          "table": "ZJGL_BZJGL_Pay_FBZJTH_CB",
          "rows": 10,
          "active_rows": 10,
          "score": 75
        },
        {
          "table": "ZJGL_ZJSQ",
          "rows": 1,
          "active_rows": 1,
          "score": 45
        }
      ]
    },
    {
      "family": "cwgl",
      "tables": 4,
      "rows": 10,
      "active_rows": 10,
      "amount_columns": 5,
      "top_tables": [
        {
          "table": "CWGL_CLBX",
          "rows": 1,
          "active_rows": 1,
          "score": 75
        },
        {
          "table": "CWGL_CLBX_CB",
          "rows": 1,
          "active_rows": 1,
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
          "rows": 7,
          "active_rows": 7,
          "score": 45
        }
      ]
    }
  ]
}
```

## Families

| Family | Tables Screened | Rows | Active Rows | Amount Columns | Top Tables |
|---|---:|---:|---:|---:|---|
| lease_equipment | 12 | 6817 | 6817 | 13 | T_ZL_TBD, XMGL_JJSB_ZLD_LXYG_CB, T_ZL_ZLJSD_CB_JX, T_ZL_ZLJSD_CB, T_ZL_ZLJH |
| labor_subcontract | 12 | 2826 | 2826 | 20 | T_JS_LWJSD_CB, T_JS_CLJSD_CB, SGGL_FBGL_MonthPlanContent, SGGL_FBGL_MonthPlan, LW_LWFD_KQB_CB |
| t | 12 | 978 | 935 | 18 | T_JS_LLJSD, T_ZJZC_ZB, T_JS_XSJSD, T_FK_Supplier_SD, T_SC_SCD |
| c | 1 | 696 | 696 | 0 | C_JFHKLR_CCB |
| office_admin | 12 | 120 | 120 | 7 | BGGL_QT_HTHS, BGGL_HBZJ_XZD_ZDYQSQ, BGGL_QT_GCBGTZD, BGGL_XZD_ZGSTKCTJB, BGGL_JHK_HKDJ_CB |
| bid_tender | 12 | 32 | 32 | 10 | WS_HTGL_ZBHT, WS_ZBJGL_ZBJ, WS_BDGL_TZEGL, WS_ZBJGL_BZJ, CGPT_T_Base_ZBXX |
| material_stock | 5 | 21 | 21 | 4 | T_RK_JCYSD, T_RK_JCYSD_CB, T_RK_TRSQ_CB, T_RK_TRSQ, T_CK_WasteMaterial |
| project_settlement | 3 | 15 | 15 | 3 | T_Project_GCQZD, XM_SBBF, T_ProjectContract_Out_CB_BZJ |
| payment_fund | 3 | 12 | 12 | 4 | ZJGL_BZJGL_Branch_SBZJTH_CB, ZJGL_BZJGL_Pay_FBZJTH_CB, ZJGL_ZJSQ |
| cwgl | 4 | 10 | 10 | 5 | CWGL_CLBX, CWGL_CLBX_CB, CWGL_FYBX_SKDW, CWGL_SQGL_CCSQ |

## Screened Tables

| Family | Table | Classification | Rows | Active Rows | Amount Sums |
|---|---|---|---:|---:|---|
| bid_tender | WS_HTGL_ZBHT | candidate_effective_business_fact | 2 | 2 | ZBJE=32324241.000000, BZJBL=12.000000, BZJJE=3232344.100000, ZBJJE=3232334.100000 |
| bid_tender | WS_ZBJGL_ZBJ | candidate_effective_business_fact | 4 | 4 | ZBJJE=14.000000 |
| bid_tender | WS_BDGL_TZEGL | candidate_effective_business_fact | 3 | 3 | GSZJE=2784364.000000, GSFBDZGYSJE=2756543.000000 |
| bid_tender | WS_ZBJGL_BZJ | candidate_effective_business_fact | 3 | 3 | ZBJJE=8.000000 |
| bid_tender | CGPT_T_Base_ZBXX | candidate_effective_business_fact | 1 | 1 |  |
| bid_tender | CGPT_T_Base_ZBXX_CB | candidate_effective_business_fact | 1 | 1 | ZJE=222.000000 |
| bid_tender | P_ZTB_ZZTB | candidate_effective_business_fact | 2 | 2 |  |
| bid_tender | P_ZTB_TBQD_CB | candidate_secondary_business_fact | 5 | 5 | ZJE=1.000000 |
| bid_tender | P_ZTB_CustomerProfile_CB | candidate_secondary_business_fact | 3 | 3 |  |
| bid_tender | P_ZTB_BSSB | candidate_secondary_business_fact | 3 | 3 |  |
| bid_tender | P_ZTB_SJFASB | candidate_secondary_business_fact | 3 | 3 |  |
| bid_tender | P_ZTB_TBDJ | candidate_secondary_business_fact | 2 | 2 |  |
| material_stock | T_RK_JCYSD | candidate_effective_business_fact | 6 | 6 |  |
| material_stock | T_RK_JCYSD_CB | candidate_secondary_business_fact | 6 | 6 | HSJE=2100500.000000 |
| material_stock | T_RK_TRSQ_CB | candidate_secondary_business_fact | 4 | 4 | HJ=1176000.000000, JE_NO=1073344.900000, SE=102655.100000 |
| material_stock | T_RK_TRSQ | candidate_secondary_business_fact | 4 | 4 |  |
| material_stock | T_CK_WasteMaterial | candidate_secondary_business_fact | 1 | 1 |  |
| labor_subcontract | T_JS_LWJSD_CB | candidate_effective_business_fact | 1175 | 1175 | FDJE=87029705.317000, FDJE_NO=0.000000, GCLJJE=0.000000, JE=0.000000 |
| labor_subcontract | T_JS_CLJSD_CB | candidate_effective_business_fact | 1003 | 1003 | RKJE=44950491.380000, RKJE_NO=40125839.830000, RKSE=0.000000, DZJE=0.000000 |
| labor_subcontract | SGGL_FBGL_MonthPlanContent | candidate_effective_business_fact | 21 | 21 | planPrice=5013.880000, planMoney=6171891.880000 |
| labor_subcontract | SGGL_FBGL_MonthPlan | candidate_effective_business_fact | 13 | 13 |  |
| labor_subcontract | LW_LWFD_KQB_CB | candidate_effective_business_fact | 3 | 3 |  |
| labor_subcontract | GLFY_Type | candidate_effective_business_fact | 1 | 1 |  |
| labor_subcontract | GLFY_GLFYJSD_CB | candidate_effective_business_fact | 554 | 554 | DJJE=37517033.220000, SJJSJE=37906246.620000 |
| labor_subcontract | LW_Base_LWDWSZ | candidate_effective_business_fact | 1 | 1 |  |
| labor_subcontract | SGGL_FBGL_MasterPlanContent | candidate_secondary_business_fact | 33 | 33 | planPrice=14432.000000, planMoney=1588067.000000, createUserID=297777760.000000 |
| labor_subcontract | SGGL_FBGL_MasterPlan | candidate_secondary_business_fact | 15 | 15 | createUserID=137777768.000000, modifyUserID=20000000.000000 |
| labor_subcontract | LW_WPRYGZSPB | candidate_effective_business_fact | 4 | 4 |  |
| labor_subcontract | LW_RYLWGZJSD | candidate_effective_business_fact | 3 | 3 |  |
| lease_equipment | T_ZL_TBD | candidate_effective_business_fact | 5 | 5 | BTJE=891.000000, BTSFJE=-4.000000 |
| lease_equipment | XMGL_JJSB_ZLD_LXYG_CB | candidate_effective_business_fact | 9 | 9 | JE=27131.770000, JE_NO=24848.500000, SE=2283.270000 |
| lease_equipment | T_ZL_ZLJSD_CB_JX | candidate_effective_business_fact | 713 | 713 | DJJE=56462085.943200, SJJSJE=56469226.016600, JE=0.000000 |
| lease_equipment | T_ZL_ZLJSD_CB | candidate_effective_business_fact | 55 | 55 | DJJE=3942626.220000, SJJSJE=3948580.920000 |
| lease_equipment | T_ZL_ZLJH | candidate_effective_business_fact | 20 | 20 |  |
| lease_equipment | T_ZL_RentalShift | candidate_effective_business_fact | 6 | 6 |  |
| lease_equipment | T_ZL_ZLJH_JX | candidate_effective_business_fact | 6 | 6 |  |
| lease_equipment | T_ZL_BTD_JX | candidate_effective_business_fact | 2 | 2 |  |
| lease_equipment | T_ZL_MachineShift_CB | candidate_secondary_business_fact | 5959 | 5959 | JE=27547620.153200 |
| lease_equipment | HTGL_ZLHT_ZLDW_Yhzhxx | candidate_secondary_business_fact | 4 | 4 |  |
| lease_equipment | T_ZL_ZLJH_CB | candidate_secondary_business_fact | 28 | 28 | JE=1527617016.030000 |
| lease_equipment | T_ZL_ZLJH_ZLSQ_CB | candidate_secondary_business_fact | 10 | 10 | JE=1640008.590000 |
| payment_fund | ZJGL_BZJGL_Branch_SBZJTH_CB | candidate_effective_business_fact | 1 | 1 | BZJJE=1.110000, THJE=0.000000 |
| payment_fund | ZJGL_BZJGL_Pay_FBZJTH_CB | candidate_effective_business_fact | 10 | 10 | BZJJE=156000.000000, THJE=15668.000000 |
| payment_fund | ZJGL_ZJSQ | candidate_secondary_business_fact | 1 | 1 |  |
| project_settlement | T_Project_GCQZD | candidate_effective_business_fact | 6 | 6 | SJJE=965.000000 |
| project_settlement | XM_SBBF | candidate_effective_business_fact | 5 | 5 | BFTBJE=3052.000000 |
| project_settlement | T_ProjectContract_Out_CB_BZJ | candidate_secondary_business_fact | 4 | 4 | JE=2245.000000 |
| office_admin | BGGL_QT_HTHS | candidate_effective_business_fact | 2 | 2 |  |
| office_admin | BGGL_HBZJ_XZD_ZDYQSQ | candidate_effective_business_fact | 2 | 2 | JE=5500.000000 |
| office_admin | BGGL_QT_GCBGTZD | candidate_effective_business_fact | 2 | 2 | YGBGJE=-235565.000000 |
| office_admin | BGGL_XZD_ZGSTKCTJB | candidate_effective_business_fact | 2 | 2 | JE=3050.000000 |
| office_admin | BGGL_JHK_HKDJ_CB | candidate_effective_business_fact | 83 | 83 | HKJE=23197555.720000, YHJE=7454883.820000, SYHKJE=31358542.470000 |
| office_admin | BGGL_QSJRW_GZQS_CB | candidate_secondary_business_fact | 4 | 4 |  |
| office_admin | BGGL_XZD_ZGSTKCTJB_CB | candidate_secondary_business_fact | 3 | 3 | JE=3050.000000 |
| office_admin | BGGL_BGYP_Base_YPKM | candidate_secondary_business_fact | 8 | 8 |  |
| office_admin | BGGL_XZ_JXDJ | candidate_secondary_business_fact | 5 | 5 |  |
| office_admin | BGGL_HBZJ_XZD_JDSPD | candidate_secondary_business_fact | 3 | 3 |  |
| office_admin | BGGL_XZ_JXDJ_ZB | candidate_secondary_business_fact | 3 | 3 |  |
| office_admin | BGGL_ZCJYP_CL_SCGYSQ | candidate_secondary_business_fact | 3 | 3 |  |
| cwgl | CWGL_CLBX | candidate_effective_business_fact | 1 | 1 | BXJE=100.000000, SBJE=0.000000 |
| cwgl | CWGL_CLBX_CB | candidate_effective_business_fact | 1 | 1 | JTFJE=50.000000, CCJE=50.000000 |
| cwgl | CWGL_FYBX_SKDW | candidate_secondary_business_fact | 1 | 1 | SKJE=0.000000 |
| cwgl | CWGL_SQGL_CCSQ | candidate_secondary_business_fact | 7 | 7 |  |
| t | T_JS_LLJSD | candidate_effective_business_fact | 18 | 11 | ZJE=7260092.910000, ZKJE=0.000000, YFJE=0.000000 |
| t | T_ZJZC_ZB | candidate_effective_business_fact | 10 | 0 | ZJE=116696.000000, SQBXJE=0.000000, SJBXJE=0.000000, HXJE=0.000000 |
| t | T_JS_XSJSD | candidate_effective_business_fact | 1 | 1 | ZJE=0.000000, ZKJE=0.000000, YFJE=0.000000 |
| t | T_FK_Supplier_SD | candidate_effective_business_fact | 7 | 7 | f_FKJE=941474.000000, f_FPJE=78.000000, f_LDJE=545.000000 |
| t | T_SC_SCD | candidate_effective_business_fact | 3 | 3 | CPJE=0.000000 |
| t | T_CGHT_HTPSB | candidate_effective_business_fact | 1 | 1 | HTJE=23.000000 |
| t | T_JH_CGJH | candidate_effective_business_fact | 51 | 25 | CG_ZJE=0.000000, ZJEHJ=0.000000 |
| t | T_CG_CGDD | candidate_effective_business_fact | 3 | 3 |  |
| t | T_ZJZC_DB | candidate_effective_business_fact | 1 | 1 |  |
| t | T_Base_NKCLKMSZ | candidate_effective_business_fact | 854 | 854 |  |
| t | T_Base_NKFBKMSZ | candidate_effective_business_fact | 18 | 18 |  |
| t | T_Base_NKGZKMSZ | candidate_effective_business_fact | 11 | 11 |  |
| c | C_JFHKLR_CCB | candidate_needs_manual_screen | 696 | 696 |  |

## Boundary

- Read-only legacy DB screen
- DB writes: `0`
- This file is evidence for lane selection; it is not a replay payload.

# History Organization Carrying Audit v1

Status: PASS
Decision: `organization_carrying_ready`
Gap count: 0

## Gaps

```json
[]
```

## Formal Organization

```json
{
  "res_company": {
    "total": 1,
    "companies": [
      {
        "id": 1,
        "name": "四川保盛建设集团有限公司"
      }
    ]
  },
  "hr_department": {
    "model": "hr.department",
    "exists": true,
    "total": 839,
    "with_company": 839,
    "sample": [
      {
        "id": 530,
        "name": "162井场外墙",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 616,
        "name": "17中核二三中核城建德阿项目屋面光伏安装专业分包常规采购",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 431,
        "name": "1851-20项目消防联调联试及通风系统安装工程",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 478,
        "name": "1-8号厂房、13号厂房、16号厂房防水保温工程专业分包合同",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 424,
        "name": "2015年市级农业综合开发土地治理项目工程",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 302,
        "name": "2017年公路水毁修复工程（双石镇）",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 197,
        "name": "2018年乐山城域传送网汇聚机房建设工程",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          20,
          "四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 176,
        "name": "2018年省级农业综合开发现代农业产业带罗江区3500亩柑橘种植",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          38,
          "四川保盛建设集团有限公司 / 四川保盛建设集团有限公司"
        ],
        "manager_id": false
      },
      {
        "id": 167,
        "name": "2019年帕哈乡八合村产业发展沟渠",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          45,
          "legacy_department_152"
        ],
        "manager_id": false
      },
      {
        "id": 189,
        "name": "2020年度高阳街道横路村3组、移民组烤房群修复项目 （二标段）",
        "company_id": [
          1,
          "四川保盛建设集团有限公司"
        ],
        "parent_id": [
          45,
          "legacy_department_152"
        ],
        "manager_id": false
      }
    ]
  }
}
```

## Legacy Department

```json
{
  "model": "sc.legacy.department",
  "exists": true,
  "total": 830,
  "active": 64,
  "root_count": 2,
  "with_parent_legacy_ref": 827,
  "with_parent_record_link": 827,
  "parent_link_gap_count": 0,
  "is_company": {
    "model": "sc.legacy.department",
    "field": "is_company",
    "available": true,
    "distinct_count": 1,
    "row_count_with_value": 549,
    "sample": [
      {
        "value": "0",
        "count": 549
      }
    ]
  },
  "is_child_company": {
    "model": "sc.legacy.department",
    "field": "is_child_company",
    "available": true,
    "distinct_count": 2,
    "row_count_with_value": 828,
    "sample": [
      {
        "value": "0",
        "count": 818
      },
      {
        "value": "1",
        "count": 10
      }
    ]
  },
  "state": {
    "model": "sc.legacy.department",
    "field": "state",
    "available": true,
    "distinct_count": 2,
    "row_count_with_value": 828,
    "sample": [
      {
        "value": "0",
        "count": 766
      },
      {
        "value": "1",
        "count": 62
      }
    ]
  },
  "sample": [
    {
      "id": 1,
      "legacy_department_id": "013740392f604e1b8e9b5c1a31ec80be",
      "name": "德阳高新区万福棚改二期大门改造工程机电安装专业分包",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 2,
      "legacy_department_id": "038363bb319f42bf93702cb369fb359d",
      "name": "绿地健康谷二号地块1标段项目泡沫混凝土工程",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 3,
      "legacy_department_id": "0457937cc9fb4179b1e38c339a310094",
      "name": "中铁十九局集团有限公司1415项目P、T 点位",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 4,
      "legacy_department_id": "0540d0e39a2d459d82eb70e781af4a4e",
      "name": "南川区石溪镇2024年农村公路（学校至王官果业（主干道至家禽屠宰场）、灯草湾至枫香榜）建设项目",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 5,
      "legacy_department_id": "059a04ea899b48148d3bb5f49403759f",
      "name": "中国移动四川公司成都分公司2023-2025年渠道维修采购项目",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 6,
      "legacy_department_id": "05ae4c95230c4b47a44cdceb0a2b27ff",
      "name": "测试3.0名称123",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 7,
      "legacy_department_id": "06b33c29220d4e9eb878b08a310d008b",
      "name": "绵阳市安州区高级职业中学空调电力改造安装工程",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 8,
      "legacy_department_id": "06d4acdfd0254911bb07c462da09481d",
      "name": "喀什地区英吉沙县2022年停车场建设项目工程总承包",
      "parent_legacy_department_id": "565",
      "depth": "2",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 9,
      "legacy_department_id": "08272b22274649bcb699b02449548386",
      "name": "重庆文理学院2025年附属工程项目(不可预测的零星维修工程)",
      "parent_legacy_department_id": "570",
      "depth": "2",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    },
    {
      "id": 10,
      "legacy_department_id": "0877e02fa6344129a2a74551332cf2b6",
      "name": "绵竹市高新区科技服务中心项目消防工程",
      "parent_legacy_department_id": "1",
      "depth": "1",
      "identity_path": "2",
      "is_company": false,
      "is_child_company": "0",
      "charge_leader_legacy_user_id": false,
      "charge_leader_name": false
    }
  ]
}
```

## User Department

```json
{
  "model": "sc.legacy.user.profile",
  "exists": true,
  "total": 101,
  "with_res_user": 0,
  "with_legacy_department_id": 85,
  "with_legacy_department_record_link": 85,
  "active_user_with_legacy_department": 0,
  "active_user_missing_legacy_department_record_link": 0,
  "department_names": {
    "model": "sc.legacy.user.profile",
    "field": "department_name",
    "available": true,
    "distinct_count": 1,
    "row_count_with_value": 2,
    "sample": [
      {
        "value": "四川保盛建设集团有限公司",
        "count": 2
      }
    ]
  },
  "sample": [
    {
      "id": 1,
      "legacy_user_id": "10000000",
      "display_name": "admin",
      "generated_login": "legacy_10000000",
      "legacy_department_id": "1",
      "department_name": "四川保盛建设集团有限公司",
      "user_id": false
    },
    {
      "id": 2,
      "legacy_user_id": "10000001",
      "display_name": "段奕俊",
      "generated_login": "legacy_10000001",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 3,
      "legacy_user_id": "10000002",
      "display_name": "邓洪英",
      "generated_login": "legacy_10000002",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 4,
      "legacy_user_id": "10000003",
      "display_name": "张志",
      "generated_login": "legacy_10000003",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 5,
      "legacy_user_id": "10000004",
      "display_name": "邓洪英",
      "generated_login": "legacy_10000004",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 6,
      "legacy_user_id": "10000005",
      "display_name": "江一娇",
      "generated_login": "legacy_10000005",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 7,
      "legacy_user_id": "10000006",
      "display_name": "江一娇",
      "generated_login": "legacy_10000006",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 8,
      "legacy_user_id": "10000007",
      "display_name": "陈帅",
      "generated_login": "legacy_10000007",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 9,
      "legacy_user_id": "10000008",
      "display_name": "华略技术—米",
      "generated_login": "legacy_10000008",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    },
    {
      "id": 10,
      "legacy_user_id": "10000009",
      "display_name": "吴涛",
      "generated_login": "legacy_10000009",
      "legacy_department_id": "10001",
      "department_name": false,
      "user_id": false
    }
  ]
}
```

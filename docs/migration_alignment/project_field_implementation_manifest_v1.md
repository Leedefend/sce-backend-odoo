# Project Field Implementation Manifest v1

## Implemented Model File

`addons/smart_construction_core/models/core/project_core.py`

## Implemented Fields

| Field | Label | Type | Legacy Source |
| --- | --- | --- | --- |
| `short_name` | 项目简称 | Char | `SHORT_NAME` |
| `project_environment` | 项目环境 | Char | `PROJECT_ENV` |
| `legacy_project_id` | 旧系统项目ID | Char, indexed | `ID` |
| `legacy_parent_id` | 旧系统父级ID | Char, indexed | `PID` |
| `legacy_company_id` | 旧系统公司ID | Char | `COMPANYID` |
| `legacy_company_name` | 旧系统公司名称 | Char | `COMPANYNAME` |
| `legacy_specialty_type_id` | 旧系统专业类型ID | Char | `SPECIALTY_TYPE_ID` |
| `specialty_type_name` | 专业类型名称 | Char | `SPECIALTY_TYPE_NAME` |
| `legacy_price_method` | 旧系统计价方式 | Char | `PRICE_METHOD` |
| `business_nature` | 经营性质 | Char | `NATURE` |
| `detail_address` | 详细地址 | Char | `DETAIL_ADDRESS` |
| `project_profile` | 项目简介 | Text | `PROFILE` |
| `project_area` | 项目面积 | Char | `AREA` |
| `legacy_is_shared_base` | 旧系统共享库标记 | Char | `IS_SHARED_BASE` |
| `legacy_sort` | 旧系统排序号 | Char | `SORT` |
| `legacy_attachment_ref` | 旧系统附件引用 | Char | `FJ` |
| `legacy_project_manager_name` | 旧系统项目经理 | Char | `PROJECTMANAGER` |
| `legacy_technical_responsibility_name` | 旧系统技术负责人 | Char | `TECHNICALRESPONSIBILITY` |
| `owner_unit_name` | 建设单位 | Char | `OWNERSUNIT` |
| `owner_contact_phone` | 业主联系电话 | Char | `OWNERSCONTACTPHONE` |
| `supervision_unit_name` | 监理单位 | Char | `SUPERVISIONUNIT` |
| `supervisory_engineer_name` | 总监理工程师 | Char | `SUPERVISORYENGINEER` |
| `supervision_phone` | 监理联系电话 | Char | `SUPERVISOPHONE` |
| `project_overview` | 项目概况 | Text | `PROJECTOVERVIEW` |
| `legacy_project_nature` | 旧系统项目性质 | Char | `PROJECT_NATURE` |
| `legacy_is_material_library` | 旧系统机材库标记 | Char | `IS_MACHINTERIAL_LIBRARY` |
| `other_system_id` | 外部系统ID | Char, indexed | `OTHER_SYSTEM_ID` |
| `other_system_code` | 外部系统编码 | Char, indexed | `OTHER_SYSTEM_CODE` |
| `legacy_stage_id` | 旧系统项目阶段ID | Char | `XMJDID` |
| `legacy_stage_name` | 旧系统项目阶段 | Char | `XMJD` |
| `legacy_region_id` | 旧系统所属地区ID | Char | `SSDQID` |
| `legacy_region_name` | 旧系统所属地区 | Char | `SSDQ` |
| `legacy_state` | 旧系统状态 | Char | `STATE` |

## Implemented View File

`addons/smart_construction_core/views/core/project_views.xml`

New fields are displayed in the existing `project.project.form.sc.core` form
inheritance under:

- `施工项目信息`
- `旧系统导入标识`
- `旧系统阶段与地区`
- `项目责任人`
- `参建单位与监理`
- `项目文本说明`

## Upgrade Requirement

The `smart_construction_core` module must be upgraded before runtime use so the
new `project_project` columns and view arch are materialized.

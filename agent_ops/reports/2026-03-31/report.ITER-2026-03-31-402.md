# ITER-2026-03-31-402 Report

## Summary

- Read the provided workbook:
  - `tmp/用户维护 (1).xlsx`
- Normalized the visible contents into two categories:
  - department candidates
  - project candidates
- Confirmed that the workbook is a user-maintenance export rather than a clean
  organization master sheet.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-402.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-402.md`
- `agent_ops/state/task_results/ITER-2026-03-31-402.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-402.yaml` -> PASS

## Workbook Facts

Workbook:

- `tmp/用户维护 (1).xlsx`

Sheet:

- `用户维护`

Header:

- `用户名`
- `姓名`
- `手机号`
- `建立时间`
- `所属部门`
- `角色`
- `状态`
- `登录次数`
- `最近登录时间`

Row count:

- `200` user rows

## Important Observation

The column named `所属部门` is not a clean department-only column.

It currently mixes:

- real department-like values
- project memberships
- employee bucket values such as `公司员工`

So this workbook can be used as an onboarding input, but not as a final
department master without cleanup.

## Department Output

Using conservative pattern splitting, the following items are the current
department candidates found in the workbook:

- `公司员工`
- `经营部`
- `项目部`
- `财务部`
- `行政部`
- `工程部`
- `成控部`

Supplementary role-side department/position tokens found in the `角色` column:

- `经营部`
- `行政部`
- `工程部`
- `财务部`
- `总经理`
- `副总经理`
- `董事长1`
- `项目负责人`
- `临时项目负责人`
- `财务经理`
- `财务助理`
- `管理员角色`
- `通用角色`

Interpretation:

- department-like entities and post/role entities are also mixed together
- the clean department backbone is therefore likely:
  - `经营部`
  - `工程部`
  - `财务部`
  - `行政部`
  - `成控部`
  - `项目部`

`公司员工` is better treated as a user bucket or generic membership group,
not as a formal business department.

## Project Output

The workbook contains a large project-membership list inside `所属部门`.

Normalized result:

- unique project candidate count: `255`

High-frequency project candidates include:

- `C4-3-1、C4-3-2等3宗地块整治工程水泥稳定碎石层铺筑`
- `东林智慧学校停车场工程建设项目`
- `修剪田坝村、中南村、西铁村社区老旧小区存量违法建筑周边树木`
- `区级机关综合办公大楼车库地坪整治项目`
- `合阳城街道2024年老旧小区改造工程(二期)`
- `喀什某单位锅炉房锅炉扩容改造项目`
- `国网新疆电力有限公司阿勒泰供电公司省管产业单位2024年第一次服务类区域联合授权框架招标采购`
- `垫江县城区污水处理厂提标改造项目（中水管网建设工程A段）--玉鼎桥至明月大道段（第二次）`
- `大足支行珠溪分理处主体装修工程`
- `奇峰镇共和村蔬菜产业园提升项目`
- `岳普湖县防沙治沙电力配套设施建设项目`
- `恒荣半岛小区东舍北苑组团消防地下管网设施设备改造项目`

Interpretation:

- this customer already has a very large project membership surface
- the current export is suitable for extracting “user -> project participation”
  clues
- it is not yet a clean project master table

## Recommended Immediate Use

For the next customer-delivery step, use this workbook in two passes:

### Pass 1: Department backbone

Treat the current department backbone as:

- `经营部`
- `工程部`
- `财务部`
- `行政部`
- `成控部`
- `项目部`

### Pass 2: Project pool

Treat the 255 unique project-like entries as a raw project pool to be cleaned
later into:

- project name
- project code
- project owner department
- project manager
- active/inactive status

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No business or security implementation files were changed.
- Main caution:
  - the source workbook mixes departments, roles, and project memberships
  - so the result should be treated as a normalized onboarding summary, not as a
    final source of truth

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-402.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-402.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-402.json`

## Next Suggestion

- Next, provide one of the following:
  - a clean department table
  - a clean employee-post table
  - a clean project master table
- With those, the current workbook can be used as a reconciliation source
  instead of the only source.

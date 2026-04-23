# Legacy Receipt Invoice Attachment Screen v1

Status: `PASS`

This is a read-only screen for `BASE_SYSTEM_FILE` linkage against receipt
invoice line assets. It does not generate `ir.attachment` records and does not
copy file binaries.

## Result

- source table: `BASE_SYSTEM_FILE`
- file rows: `126967`
- candidate key values: `16500`
- matched file rows: `1079`
- matched receipt invoice lines: `1079`
- ambiguous file rows: `0`
- deleted matched file rows: `0`
- DB writes: `0`
- Odoo shell: `false`

## Match Distribution

| Source field -> candidate key | Matches |
|---|---:|
| PID->pid | 1079 |

## Sample Matches

| File ID | Name | Size | Source | Deleted | Match count |
|---|---|---:|---|---|---:|
| 001cb500-899f-4d8f-8f6d-54807b6e3ce9 | 2.jpg | 108978 | 0 | False | 1 |
| 0023feb4-963f-4c8c-b908-f73f601c5428 | 通安德阿.jpg | 45588 | 0 | False | 1 |
| 00263a4b-6f64-46be-aae0-9c15f18371cf | 5A3E9易AB8070D44DE8274C28318BA9266.png | 4844857 | 0 | False | 1 |
| 0095b916-3810-4d98-993a-ac6849da0b4d | 企业微信截图_2019.7.26成都三供一业.png | 52065 | 0 | False | 1 |
| 00b08df3-2b0a-465c-a58a-4cd481902d13 | 补充医疗保险.jpg | 2652615 | 0 | False | 1 |
| 00e96408-3f01-4820-8217-bb7fec059db1 | 会东县殡仪馆.png | 34905 | 0 | False | 1 |
| 012d8524-6f22-4dbf-bd35-46dca9c433b7 | 施工合同.pdf | 313781 | 0 | False | 1 |
| 019b2e5b-eb14-4363-bb85-c27d47e9faaf | 乐山马边.png | 49372 | 0 | False | 1 |
| 01a427dd-44a9-47a7-9112-c02756ec8312 | 杨永田园林工程 (1).jpg | 858541 | 0 | False | 1 |
| 01d4656f-ae42-4382-8302-db0b2dcbe826 | 税票_5_漆乐.pdf | 156861 | 0 | False | 1 |
| 01e4a497-5844-40ae-a2c3-c2382f1a363e | 新文档 2020-02-28_17_吕立砼班组4.pdf | 88111 | 0 | False | 1 |
| 01f18eec-5aba-4dbb-b974-190a0e087389 | 5-7IMG_3634.jpg | 2027596 | 0 | False | 1 |
| 025bdcc2-4270-4caf-b306-5db468de937a | SKM_28719090916060_0005.jpg | 591631 | 0 | False | 1 |
| 026c6b5d-213e-4dc1-b545-7583ab077788 | 张文浩本科毕业证.jpg | 177406 | 0 | False | 1 |
| 02ae8bba-05d2-4b82-8e11-797f32f107c7 | 胡俊一级建造师注册证.jpg | 1030504 | 0 | False | 1 |
| 02b9abec-18ac-4227-8f1f-30c18516e7f5 | 广元项目保证金2.jpg | 44214 | 0 | False | 1 |
| 02dff5e9-ce48-4d0d-a475-315f9ed9c232 | 文楠（水利水电）.jpg | 1847713 | 0 | False | 1 |
| 031944e4-2e3f-4af0-9b14-0e8f4cf2f7a1 | 竣工验收报告 (4).jpg | 291467 | 0 | False | 1 |
| 03510b25-2ce0-4d87-9db9-6262c04a3246 | 47adf8b10ad45f5dc56d08b1cea68b7.jpg | 34245 | 0 | False | 1 |
| 035bc703-87e6-4d8e-af93-6b344092fefa | 陈帅毕业证（专科）.jpg | 527129 | 0 | False | 1 |

## Decision

`attachment_asset_lane_ready`

If the decision is blocked, the next step is a broader attachment mapping screen
against the parent receipt table and source module metadata before any
attachment XML asset is generated.

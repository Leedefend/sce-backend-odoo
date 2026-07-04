# SCBS Project Bucket Policy Report

This report covers active SCBS facts that have no confirmed project but need `project_id` for formal target models.

## Summary

| Fact Family | Rows | Amount | Business Entity Count | Partner Count |
| --- | ---: | ---: | ---: | ---: |
| payment | 2608 | 110459119.00 | 19 | 302 |
| stock_in | 345 | 50030375.39 | 6 | 156 |
| supplier_contract | 440 | 96955707.99 | 11 | 244 |

## Recommended Policy

- Do not merge these rows into existing real projects without source evidence.
- Create source-tagged project buckets only if formal models must represent every historical fact as an operational row.
- Recommended bucket grain: one `SCBS未指定项目` project per confirmed business entity; rows without business entity stay reporting-only until entity evidence is found.
- Mark bucket projects as historical migration buckets in notes/source fields so they are not treated as real user-created projects.

## By Business Entity

| Fact Family | Business Entity | Rows | Amount | Partner Count | Legacy Partner Text Count |
| --- | --- | ---: | ---: | ---: | ---: |
| payment | [NO_BUSINESS_ENTITY] | 1115 | 39138881.03 | 79 | 79 |
| payment | 四川迈投建筑工程有限公司 | 203 | 16375606.82 | 54 | 54 |
| payment | 四川世旺鑫润商贸有限公司 | 312 | 13938104.16 | 81 | 81 |
| payment | 四川晟博通达商贸有限公司 | 125 | 9170777.91 | 55 | 55 |
| payment | 德阳泰诚硕商贸有限公司 | 279 | 8824253.88 | 65 | 65 |
| payment | 四川鑫垚建筑劳务有限公司 | 249 | 8719682.95 | 55 | 55 |
| payment | 四川翔驰恒瑞商贸有限公司 | 125 | 5034940.06 | 24 | 24 |
| payment | 德阳市博众建材销售有限公司 | 40 | 2735109.63 | 8 | 8 |
| payment | 四川宏政嘉斯建筑工程有限公司 | 57 | 2187341.35 | 23 | 23 |
| payment | 四川宏川建筑劳务有限公司 | 41 | 1345704.75 | 20 | 20 |
| payment | 德阳市区永沁建材经营部 | 6 | 526333.00 | 4 | 4 |
| payment | 德阳市海旺建材经营部 | 7 | 508615.00 | 5 | 5 |
| payment | 德阳经开区科纳机械租赁部 | 5 | 499702.00 | 3 | 3 |
| payment | 旌阳区加卓建筑材料经营部 | 6 | 375020.00 | 3 | 3 |
| payment | 德阳森元路面工程有限公司 | 23 | 341645.48 | 9 | 9 |
| payment | 德阳经开区铭杨建材经营部 | 4 | 175020.00 | 2 | 2 |
| payment | 旌阳区立扬伟建材经营部 | 3 | 174500.00 | 1 | 1 |
| payment | 四川嘉易欢悦建筑工程有限公司 | 3 | 155300.00 | 3 | 3 |
| payment | 旌阳区应木建材经营部 | 1 | 122000.00 | 1 | 1 |
| payment | 旌阳区宏裕辉建材经营部 | 4 | 110580.98 | 3 | 3 |
| stock_in | 四川世旺鑫润商贸有限公司 | 138 | 21120659.57 | 82 | 82 |
| stock_in | 四川晟博通达商贸有限公司 | 81 | 11678774.25 | 54 | 54 |
| stock_in | 德阳泰诚硕商贸有限公司 | 82 | 11646060.71 | 52 | 52 |
| stock_in | 四川翔驰恒瑞商贸有限公司 | 36 | 5584880.86 | 23 | 23 |
| stock_in | 公司综合平台 | 5 | 0.00 | 1 | 2 |
| stock_in | 陕西煤业化工建设(集团)有限公司洗选煤运营分公司 | 3 | 0.00 | 3 | 3 |
| supplier_contract | 德阳市博众建材销售有限公司 | 58 | 50592277.47 | 46 | 46 |
| supplier_contract | 四川世旺鑫润商贸有限公司 | 67 | 17440148.70 | 54 | 54 |
| supplier_contract | 德阳泰诚硕商贸有限公司 | 45 | 8285469.75 | 34 | 34 |
| supplier_contract | 四川晟博通达商贸有限公司 | 40 | 5916143.54 | 34 | 34 |
| supplier_contract | 四川迈投建筑工程有限公司 | 95 | 5327591.60 | 69 | 69 |
| supplier_contract | 四川鑫垚建筑劳务有限公司 | 48 | 3228269.00 | 40 | 40 |
| supplier_contract | 四川宏川建筑劳务有限公司 | 31 | 2059333.00 | 24 | 24 |
| supplier_contract | 四川宏政嘉斯建筑工程有限公司 | 25 | 1906966.98 | 23 | 23 |
| supplier_contract | 德阳森元路面工程有限公司 | 14 | 1065455.00 | 12 | 12 |
| supplier_contract | [NO_BUSINESS_ENTITY] | 9 | 623832.00 | 6 | 6 |
| supplier_contract | 四川翔驰恒瑞商贸有限公司 | 5 | 439720.95 | 5 | 5 |
| supplier_contract | 四川嘉易欢悦建筑工程有限公司 | 3 | 70500.00 | 3 | 3 |

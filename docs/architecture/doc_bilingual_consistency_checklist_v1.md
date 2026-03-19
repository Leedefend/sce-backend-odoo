# 文档双语一致性检查清单 v1

适用范围：`docs/architecture` 下需要中英文成对维护的规范文档。

## 快速检查项
- 文件成对：中文 `.md` 与英文 `.en.md` 同名且同目录。
- 结构对齐：章节层级与顺序一致（允许轻微语言差异）。
- 链接对齐：中文文档可跳转英文版，英文文档可跳转中文版。
- 术语对齐：`group_key`、`scene`、`intent`、`reason_code` 用词固定。
- 示例对齐：配置键名、字段名、路径名保持一致。
- 版本对齐：标题中的版本号（如 `v1`）一致。
- 更新对齐：任一版本改动后，同步更新另一语言版本。

## 当前纳入检查的词表文档
- `docs/architecture/nav_group_terms_v1.md`
- `docs/architecture/nav_group_terms_v1.en.md`

## 建议执行时机
- 提交前自检一次。
- PR 审核时按本清单复核一次。

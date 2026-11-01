# 历史笔记与外部资料

## 来源优先级

当前可核对的原文件＋实际阅读记录优先；旧总纲和旧阅读宣称只作为待核历史记录。外部资料没有伪装成本仓库原书，也没有上传原始截图、整本提取文字或用户个人案例。

## 本轮迁移的有效成果

- 八份仓库原文件全文阅读记录及逐书限制，见B037、B042、B047、B072、B073、B090、B103、B117。
- 此前案例精读笔记中，三份连续教学记录的研究观察已迁移到C07，并核对ZIP条目哈希及关键词断点；不迁移旧笔记中的用户案例。
- 陈哥五项技巧正文与其画面感附节，本轮重新核读161段及全部9张JPEG教学图；此前计数将一个目录条目误作资源，本轮已更正，见S01。
- 20160626空姐讲义，原文现有文字全文重新核读；未见可核验线下结果，归属未独立验证。

## 其他历史阅读记录

以下保留的是此前明确记录的阅读范围，不由此扩展新来源或冒认整库读完：

| 来源 | 历史实际范围 | 恢复位置与限制 |
| --- | --- | --- |
| 陈哥《恋爱12式》 | 幽默、电话与邀约段落，旧记录提取页序66、68、145、147附近 | 当前207页PDF身份已记录，旧提取页序到文件页映射尚待核对，不能标全本读完 |
| Tyler合集 | 旧提取文本3012–3490、3650–3760、3770–4050行 | Phone Game和部分Field Reports；原TXT在TOP30压缩包，行号可能受换行差异影响，原始单元需另核 |
| 梵f008、f009 | 两份全文，跨文件的案例连续性已看 | 固定版本见下，课程选例与事后讲解分开 |
| 梵f010 | 行1–24、661–750、946–1711、1856–1979 | 其余未读；不能按整个文件或全部案例统计 |
| 情圣示例库 | 41条示例全文 | 多数只有她的一句和建议回复，无女生后续，不是41场实战 |
| 童锦程研究摘要 | 摘要全文 | 不等于看完九个原始视频或20万字原始字幕 |
| 上传PUA_MASTER_CURRENT总纲 | 当前仅检查开头与若干段 | 旧文声称TOP30 30/30及Production完成，尚无逐项可核阅读证据，不能采纳为全读状态 |

## 可回查的固定外部GitHub位置

- [梵f008](https://github.com/khdzg5shnt-rgb/fan-emotion-analysis-skill/blob/23f33bdda9d66323c14c760e1960a557a2009052/REFERENCE/f008.md)
- [梵f009](https://github.com/khdzg5shnt-rgb/fan-emotion-analysis-skill/blob/23f33bdda9d66323c14c760e1960a557a2009052/REFERENCE/f009.md)
- [梵f010](https://github.com/khdzg5shnt-rgb/fan-emotion-analysis-skill/blob/23f33bdda9d66323c14c760e1960a557a2009052/REFERENCE/f010.md)
- [41条教学示例](https://github.com/khdzg5shnt-rgb/qingsheng-skill/blob/ea23b10376b146abfcff20f71876889a0453a7e7/skill/references/examples-library.md)
- [童锦程二次研究摘要](https://github.com/khdzg5shnt-rgb/tong-jincheng-skill/blob/c9caaa9a6576f581c29d016c60bbe935908e20d5/references/research/02-conversations.md)

恢复阅读时可定向取所需范围，无须重新下载全部外部仓库。

## 加工与阅读记录如何复现

仓库原文件的身份、页数/单元数及加工状态见source_inventory.json，OCR薄弱页见ocr_review.json。此前提取采用PyMuPDF读取PDF文字、lxml按EPUB spine读取XHTML、LibreOffice转换DOC；扫描页用Tesseract中文识别。提取字符区间依赖同一提取版本，最稳定的回查依据仍是原文件blob＋PDF物理页或EPUB内部href。

所有原始文件保持原样。提取/OCR缓存未作为永久恢复前提；新窗口需要某段时只重建对应页或章节，不重新处理整个资料库。知识文件可恢复保存的结论，不能保证还原所有未记下的细节。

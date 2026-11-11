# Books2：聊天截图 → 相关方法 → 一句回复

[开始使用](START_HERE.md) · [场景路由](system/SCENARIO_ROUTER.md) · [方法卡](system/METHOD_CARDS.md) · [全部来源](system/SOURCE_INTEGRATION.md) · [当前进度](CURRENT_STATE.md)

把书籍、上传资料与恋爱相关GitHub来源整理为同一个可查阅的指导系统。日常只需这个仓库：核截图与上下文，定位场景和方法，按真实信息生成一句自然回复；必要时建议先不发。

## 现在可以使用

- 32条有优先顺序的场景路由，处理接话、提问、调侃、共情、赞美、邀约、确认、取消、低投入、修复和边界；旧标签不盖过新内容。
- 26张方法卡各自定位到一处实际笔记段落，保留适用、操作、禁用条件与全部出处供追溯。
- 一个[当前一轮入口](system/CURRENT_TURN.md)与[日常流程](system/RUNBOOK.md)，按怎么回、什么意思、分析、复盘、训练五种任务输出；不同对象的事实独立。
- 原始126项、23项上传材料、9个公开外部GitHub来源统一登记；已采用内容可在仓库内找到，未读与缺失范围明确。
- 原有书籍笔记、主题笔记、C01–C18公开教学案例和许可归档继续有效。

最近系统维护已完成：保留旧边界并核当前内容是否同一方向，修正旧低投入盖过新双向接梗；方法与关键词可定位一处贴题笔记，核对问题明确给用户。26方法、32路由、五种任务；39项测试覆盖132个虚构路由场景，实际范围见[维护报告](knowledge/provenance/OS_current_content_2026-11-12.md)与[验证记录](knowledge/provenance/OS_current_content_validation_2026-11-12.json)。

源材料数量不是阅读完成率。TOP30仍30/30；119份原始书籍中32份现有文字完成、3份部分、84份未开始。本轮[B030](knowledge/books/B030.md)摘编DOC与[B031](knowledge/books/B031.md)EPUB共54945提取字符读完，新增五组审阅及九条方法出处；B031与已读B025高度对应，不增加独立理论数。下一B032文档开头，见[报告](knowledge/provenance/B030_B031_progress_2026-11-12.md)。来源158条，B014/B015/B017缺口保留。

这里是助手读取和执行的规则、知识与检索工具。命令行给出一个主方法、笔记行段与本任务约定，不自行理解截图或生成语言。不保存真实私人聊天，不自动发送消息，不承诺某句话保证成功。

```bash
python scripts/coach.py --request system/EXAMPLE_REQUEST.json
python scripts/coach.py --request -
python scripts/search_knowledge.py '没给替代时间'
python scripts/search_knowledge.py --method M14
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
```

原始书籍沿用现有来源身份；新增项目文档仅在许可范围内保存，具体出处、文件哈希和阅读状态见[整合清单](system/SOURCE_INTEGRATION.md)。

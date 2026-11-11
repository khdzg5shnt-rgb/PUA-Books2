# Books2：聊天截图 → 相关方法 → 一句回复

[开始使用](START_HERE.md) · [场景路由](system/SCENARIO_ROUTER.md) · [方法卡](system/METHOD_CARDS.md) · [全部来源](system/SOURCE_INTEGRATION.md) · [当前进度](CURRENT_STATE.md)

把书籍、上传资料与恋爱相关GitHub来源整理为同一个可查阅的指导系统。日常只需这个仓库：核截图与上下文，定位场景和方法，按真实信息生成一句自然回复；必要时建议先不发。

## 现在可以使用

- 31条有优先顺序的场景路由，处理接话、提问、调侃、共情、赞美、邀约、确认、取消、低投入、修复和边界；旧标签不盖过新内容。
- 26张方法卡各自定位到一处实际笔记段落，保留适用、操作、禁用条件与全部出处供追溯。
- 一个[当前一轮入口](system/CURRENT_TURN.md)与[日常流程](system/RUNBOOK.md)，按怎么回、什么意思、分析、复盘、训练五种任务输出；不同对象的事实独立。
- 原始126项、23项上传材料、9个公开外部GitHub来源统一登记；已采用内容可在仓库内找到，未读与缺失范围明确。
- 原有书籍笔记、主题笔记、C01–C18公开教学案例和许可归档继续有效。

最近系统维护已完成：新消息更新等待状态，具体边界与正常交流分开，解释性任务和必要事务分别处理。现行29项测试与108个虚构路由场景保留；前轮[三个虚构截图示例](tests/visual/README.md)继续有效，不是盲测或自动识图功能。本轮M02首选集中到联系与等待；此前M03/M04/M07/M10/M24成果有效。

源材料数量不是阅读完成率。TOP30仍30/30；119份原始书籍中23份文字完成、2份部分、94份未开始。B016当前EPUB题名、前言及二十章172067提取字符全部读完，本轮补完后十三章81366字符。[本轮等待与联系安排](knowledge/topics/contact-and-waiting.md)供M02直接定位，另七个方法补取舍来源。B014文后缺口与B015图片排除保留在[阅读队列](system/READING_QUEUE.md)。下一B017，从文件第1页开始，尚未读正文；详见[本轮报告](knowledge/provenance/B016_completion_2026-11-11.md)。来源158条不变。

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

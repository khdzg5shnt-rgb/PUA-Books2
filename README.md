# Books2：聊天截图 → 相关方法 → 一句回复

[开始使用](START_HERE.md) · [场景路由](system/SCENARIO_ROUTER.md) · [方法卡](system/METHOD_CARDS.md) · [全部来源](system/SOURCE_INTEGRATION.md) · [当前进度](CURRENT_STATE.md)

把书籍、上传资料与恋爱相关GitHub来源整理为同一个可查阅的指导系统。日常只需这个仓库：核截图与上下文，定位场景和方法，按真实信息生成一句自然回复；必要时建议先不发。

## 现在可以使用

- 36条有优先顺序的场景路由，处理接话、提问、调侃、共情、赞美、邀约、确认、取消、低投入、修复和边界；旧标签不盖过新内容。
- 26张方法卡各自定位到一处实际笔记段落，保留适用、操作、禁用条件与全部出处供追溯。
- 一个[当前一轮入口](system/CURRENT_TURN.md)与[日常流程](system/RUNBOOK.md)，按怎么回、什么意思、分析、复盘、训练五种任务输出；不同对象的事实独立。
- 原始126项、23项上传材料、9个公开外部GitHub来源统一登记；已采用内容可在仓库内找到，未读与缺失范围明确。
- 原有书籍笔记、主题笔记、C01–C18公开教学案例和许可归档继续有效。

多图入口区分最后谁发消息与本轮主要回答哪一句，保留连续发来的问题和补充。修改未发草稿时保留事实及已确认的表达要求；复盘允许本轮无需调整。统一入口仍为26张方法卡、36条路由和五种任务。63项测试及原有158个虚构路由场景通过。见[本轮维护](knowledge/provenance/OS_turn_and_revision_2026-11-12.md)与[验证记录](knowledge/provenance/OS_turn_and_revision_validation_2026-11-12.json)。

当前完成50/119份任务，另2份未完成、67份未开始。B017按用户要求结束，实际图字缺口保留；此前B036、B038已实读收尾。本轮按用户要求暂停读书，只完善系统，新增阅读为零。B039原页累计143/380，连续前缀至131页，恢复时从132页继续；B045及新文件等待。[已有补核](knowledge/provenance/B039_first_chapter_scan_review_2026-11-12.md)。

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

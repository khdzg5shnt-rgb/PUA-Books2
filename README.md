# Books2：聊天截图 → 相关方法 → 一句回复

[开始使用](START_HERE.md) · [场景路由](system/SCENARIO_ROUTER.md) · [方法卡](system/METHOD_CARDS.md) · [全部来源](system/SOURCE_INTEGRATION.md) · [当前进度](CURRENT_STATE.md)

把书籍、上传资料与恋爱相关GitHub来源整理为同一个可查阅的指导系统。日常只需这个仓库：核截图与上下文，定位场景和方法，按真实信息生成一句自然回复；必要时建议先不发。

## 现在可以使用

- 36条有优先顺序的场景路由，处理接话、提问、调侃、共情、赞美、邀约、确认、取消、低投入、修复和边界；旧标签不盖过新内容。
- 26张简短方法卡各自定位到一处实际笔记段落；全部引用保留在[完整出处索引](system/METHOD_SOURCES.md)，日常不用整份展开。
- 一个[当前一轮入口](system/CURRENT_TURN.md)与[日常流程](system/RUNBOOK.md)，按怎么回、什么意思、分析、复盘、训练五种任务输出；不同对象的事实独立。
- 原始126项、23项上传材料、9个公开外部GitHub来源统一登记；已采用内容可在仓库内找到，未读与缺失范围明确。
- 原有书籍笔记、主题笔记、C01–C18公开教学案例和许可归档继续有效。

多图和平面入口都核最近已发方向，首次开场与未知末句分开。方法内检索只采用已精确绑定的段落，不借整本出处串到其他方法；已有词组命中优先。M26直接定位[一句自然话的取舍](system/REPLY_PROTOCOL.md#一句自然话的取舍)，保留同轮主内容、未发草稿修改和可不调整的复盘。此前修订见[方向与来源维护](knowledge/provenance/OS_sender_and_sources_2026-11-13.md)。

当前轮的待答请求、解决或撤回、安排更新分别核：前面仍待答的求助不被后面普通问题盖掉，已解决请求不重答，取消与边界继续保留。此前的[请求处理维护](knowledge/provenance/OS_request_resolutions_2026-11-14.md)继续有效。

运行1.5.4将常用方法卡与完整出处分开，检索与统一入口每次只载入一次公共配置，并检查两份视图与配置是否同步。仍只选一个主方法、交付一条回复。[本轮维护](knowledge/provenance/OS_knowledge_views_2026-11-14.md) · [检查范围](knowledge/provenance/OS_knowledge_views_validation_2026-11-14.json)。

<!-- CURRENT_READING_STATUS -->
当前完成101/119份任务，无部分处理文件、18份未开始。94份当前提供内容已覆盖（含历史B100明确同文复用），7份依用户授权结束并保留缺口。本轮B107《言情恋爱话术惯例 - 乌鸦救赎》105页原生文字32890字符依序读完，无嵌入栅格图像，23页版式已核；105页提取严格一致。新增34组整合笔记、96处精确方法引用。下一唯一主读B108物理P1，正文未打开。[本轮记录](knowledge/provenance/B107_progress_2026-11-15.md)。
<!-- END_CURRENT_READING_STATUS -->

这里是助手读取和执行的规则、知识与检索工具。命令行给出一个主方法、笔记行段与本任务约定，不自行理解截图或生成语言。不保存真实私人聊天，不自动发送消息，不承诺某句话保证成功。

```bash
python scripts/coach.py --request system/EXAMPLE_REQUEST.json
python scripts/coach.py --request system/EXAMPLE_PLAN_UPDATE.json
python scripts/coach.py --request -
python scripts/search_knowledge.py '没给替代时间'
python scripts/search_knowledge.py --method M14
python scripts/method_cards.py --check
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
```

原始书籍沿用现有来源身份；新增项目文档仅在许可范围内保存，具体出处、文件哈希和阅读状态见[整合清单](system/SOURCE_INTEGRATION.md)。

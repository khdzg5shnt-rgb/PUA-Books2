# Books2：聊天截图 → 相关方法 → 一句回复

[开始使用](START_HERE.md) · [实战工作页](CHAT_GUIDANCE_PLAYBOOK.md) · [场景路由](system/SCENARIO_ROUTER.md) · [方法卡](system/METHOD_CARDS.md) · [全部来源](system/SOURCE_INTEGRATION.md) · [当前进度](CURRENT_STATE.md)

把书籍、上传资料与恋爱相关GitHub来源整理为同一个可查阅的指导系统。日常只需这个仓库：核截图与上下文，定位场景和方法，按真实信息生成一句自然回复；必要时建议先不发。

## 现在可以使用

运行1.6.4补上[同轮实质内容核对](knowledge/provenance/OS_substantive_tail_2026-11-16.md)：先讲困扰、好消息或事实更正，后接玩笑或收尾时，先核前文是否仍需回应。助手用已有原句选择主内容；确实收尾仍可不回，不默认要求用户重复截图。

此前1.6.3围绕输入、话题流转与成品质量复核：补清语音、编辑及平台撤回规则，将共同回扣标记限定到当前气泡，并明确何时只给一句、何时补一个后续观察点。未回复时仍先等，仅保留原有独立必要事务例外。

运行1.6.2补上[修稿与消息绑定](system/INPUT_FACTS.md#把修稿要求绑定到消息)：同一消息的未发草稿保留表达要求，新消息或待答主内容变化后不套用旧稿限制。已生效要求进入当前输出约定，等待、实际安排和具体边界仍优先。

运行1.6.1补充[7组21个常用说法的精确段落定位](knowledge/topics/source-synthesis.md#已定方法后的常用说法定位)。它只填补固定主方法后的字面检索缺口；已有命中保持优先，不从关键词推断态度或改变下一动作。

运行1.6.0将认识、接话、真实表达、邀约、安排和见面后处理收进同一张[实战工作页](CHAT_GUIDANCE_PLAYBOOK.md)，写明适用条件、收住的位置与一条成品的取舍。已有双向基础且安排真实可行时，助手负责识别适合邀约的机会。草稿结构检查新增显式编号多版本与代码围栏检查，始终保留事实和口吻需人工核对的标记；[三篇研究核验](knowledge/topics/practice-evidence.md)附准确APA、读取范围和迁移限制。后续功能与旧维护记录按各自日期阅读。

- 36条有优先顺序的场景路由，处理接话、提问、调侃、共情、赞美、邀约、确认、取消、低投入、修复和边界；旧标签不盖过新内容。
- 26张简短方法卡各自定位到一处实际笔记段落；全部引用保留在[完整出处索引](system/METHOD_SOURCES.md)，日常不用整份展开。
- 一个[当前一轮入口](system/CURRENT_TURN.md)与[日常流程](system/RUNBOOK.md)，按怎么回、什么意思、分析、复盘、训练五种任务输出；不同对象的事实独立。
- 原始126项、23项上传材料、9个公开外部GitHub来源统一登记；已采用内容可在仓库内找到，未读与缺失范围明确。
- 原有书籍笔记、主题笔记、C01–C18公开教学案例和许可归档继续有效。

多图和平面入口都核最近已发方向，首次开场与未知末句分开。方法内检索只采用已精确绑定的段落，不借整本出处串到其他方法；已有词组命中优先。M26直接定位[一句自然话的取舍](system/REPLY_PROTOCOL.md#一句自然话的取舍)，保留同轮主内容、未发草稿修改和可不调整的复盘。此前修订见[方向与来源维护](knowledge/provenance/OS_sender_and_sources_2026-11-13.md)。

当前轮的待答请求、解决或撤回、安排更新分别核：前面仍待答的求助不被后面普通问题盖掉，已解决请求不重答，取消与边界继续保留。此前的[请求处理维护](knowledge/provenance/OS_request_resolutions_2026-11-14.md)继续有效。

此前1.5.4维护将常用方法卡与完整出处分开，检索与统一入口每次只载入一次公共配置，并检查两份视图与配置是否同步。仍只选一个主方法、交付一条回复。[本轮维护](knowledge/provenance/OS_knowledge_views_2026-11-14.md) · [检查范围](knowledge/provenance/OS_knowledge_views_validation_2026-11-14.json)。

<!-- CURRENT_READING_STATUS -->
当前完成119/119份任务，无部分处理文件、无未开始文件。108份当前内容覆盖，11份依用户授权结束并保留缺口。原始队列已结束，无下一本；当前转入聊天实战系统1.6.4维护。本轮不新增书籍阅读或方法绑定。[实战工作页](CHAT_GUIDANCE_PLAYBOOK.md) · [当前状态](CURRENT_STATE.md)。
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

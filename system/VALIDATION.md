# 检查范围

2026-11-12本轮暂停阅读，维护当前内容范围与方法内检索。两项规定检查已通过：39项测试覆盖132个虚构路由场景；旧29项测试与108个场景保留，新增10项与24个场景。最终范围核对通过。实际结果见[本轮验证](../knowledge/provenance/OS_current_content_validation_2026-11-12.json)，改动见[维护报告](../knowledge/provenance/OS_current_content_2026-11-12.md)。阅读30/119、3份部分、86份未开始；B030文档开头书签与来源登记不变。

新增核对范围：旧边界与新正常内容分开，活动拒绝与答应安排是否同项、当前双向接梗与旧低投入、核对问题的接收方、关键词命中优先、来源文件反向方法指向，以及focus只换资料段落、不换主方法或动作。原首选段落、方法操作、其他对象与真实输入不被改写。

以下为历史维护与检查记录，其数字属于各自当时范围。

上轮（2026-11-11）系统维护已实际通过结构检查与29项测试、108个虚构路由场景；新增24个，旧84个ID保留。示例入口、M23检索及四项stdin流程另跑通；身份、来源清单、书签、旧校准与阅读快照、链接和26处首选段落另核。真实输出见[当轮检查](../knowledge/provenance/OS_scope_update_validation_2026-11-11.json)，内容见[维护报告](../knowledge/provenance/OS_scope_update_2026-11-11.md)。此前[B012续读记录](../knowledge/provenance/B012_validation_2026-11-11.json)保留，历史数字不覆盖本轮。

```bash
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
python scripts/coach.py --request system/EXAMPLE_REQUEST.json
python scripts/search_knowledge.py '没给替代时间'
```

结构检查核方法与来源引用、内部文件链接、归档blob/SHA-256与许可证、阅读台账身份和连续范围、来源统计与书签同步、26处首选段落和五种任务约定。上传数从来源登记推导，不再靠手改一个固定常数。

本轮另核已发送方向、具体限制在正常回应后仍保留、只承接不追问、解释性任务不索要日期、必要事务不重邀、人读路由顺序与非法承接约定。

单元测试核虚构场景路由优先级、不同对象不串用、stdin与非法输入、五种输出约定、草稿结构、实际段落范围、检索以及错误统计/书签/段落被拒绝。新增场景包含没空无替代与安排话题的冲突、旧约定/短答遇到新的认真内容、赞美与边界；原有拒绝、修复、完整短答、求助、取消、替代时间、等待等场景继续检查。

检查通过不能证明元数据对应的阅读行为，也不能证明真实截图识别、心理机制或恋爱效果。统一入口接受人工核对的事实，只返回一个处理提纲，不调用模型、不读图、不生成或发送语言。草稿检查不判断事实、语气、问句含义或效果。

2026-11-11续读B011：当前20/119份现有文字完成、0份部分、99份未开始。结构检查与20项测试通过，84个虚构场景不增加；另核114页/7段、26页视觉/88页未逐页核版面、身份与逐页哈希、卡片、锚点及M21/M22段落。真实输出见[B011检查记录](../knowledge/provenance/B011_validation_2026-11-11.json)，限制见[完成报告](../knowledge/provenance/B011_completion_2026-11-11.md)。

2026-11-11继续完成B012：当前21/119份现有文字完成、0份部分、98份未开始；本次B011/B012共两份182页。结构与20项测试通过，84个虚构场景不增加；另核68页/11段、26页视觉/42页未核版面、九项对照定位、六章字符范围、身份、卡片、链接、锚点及M10段落。真实输出见[B012检查记录](../knowledge/provenance/B012_validation_2026-11-11.json)，范围见[完成报告](../knowledge/provenance/B012_completion_2026-11-11.md)。

## 历史记录

- [首次系统检查](../knowledge/provenance/os_validation.json)、[首次系统报告](../knowledge/provenance/os_round_2026-11-02.md)。
- [核心精读检查](../knowledge/provenance/core_reading_validation.json)。
- [续读验收](../knowledge/provenance/continuation_validation_2026-11-03.json)与[报告](../knowledge/provenance/continuation_2026-11-03.md)。
- [剩余来源验收](../knowledge/provenance/remaining_sources_validation_2026-11-03.json)与[报告](../knowledge/provenance/remaining_sources_2026-11-03.md)。
- [B004–B006检查](../knowledge/provenance/B004_B006_validation_2026-11-10.json)。
- [B007/S23检查](../knowledge/provenance/B007_S23_validation_2026-11-11.json)。

历史报告里的测试数与阅读数属于其当时范围，不覆盖这次实际检查。

2026-11-11续读B008：当前17/119份现有文字完成；结构与20项测试通过，84个虚构路由场景不增加。另核原始blob、新提取身份、174页和15段连续范围、33页视觉与141页未核版式、方法卡及新笔记链接。真实输出见[B008检查](../knowledge/provenance/B008_validation_2026-11-11.json)，范围见[完成报告](../knowledge/provenance/B008_completion_2026-11-11.md)。

2026-11-11继续完成B009：当前18/119份现有文字完成，101份未通读；结构与20项测试通过，84个虚构场景不增加。另核135页/11段、38页视觉/97页未核版式、多栏补读身份、卡片与本轮链接。实际输出见[B009检查](../knowledge/provenance/B009_validation_2026-11-11.json)，阅读范围与同次指令两文件进度见[报告](../knowledge/provenance/B009_completion_2026-11-11.md)。

2026-11-11继续完成B010七分册合订本：当前19/119份现有文字完成、0份部分、100份未开始，七分册只增加一份原始文件。结构与20项测试通过，84个虚构场景不增加；另核644页/40段、48页视觉/596页未核版面、七分册连续范围、原始与提取身份、卡片和M08真实段落检索。实际输出见[B010检查](../knowledge/provenance/B010_validation_2026-11-11.json)，限制见[完成报告](../knowledge/provenance/B010_completion_2026-11-11.md)。

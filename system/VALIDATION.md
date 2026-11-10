# 检查范围

本系统有两类可执行检查：资料结构检查，以及56个虚构对话场景的路由检查。场景文件不含用户或女生的真实聊天。

```bash
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
python scripts/route.py --facts system/EXAMPLE_FACTS.json
python scripts/search_knowledge.py 'Callback 共同话题'
```

结构检查核方法与来源引用、内部文件链接、归档与固定blob/SHA-256一致、许可证存在。场景检查覆盖输入缺口、正常问题、封闭短答、慢回未知、反复低投入、后续新投入、具体邀约、替代安排、已答应后的短回复、取消、纠正、同意与边界、用户已发后等待。

命令行路由接受人工核对的事实，不识别图片、不读心、不调用模型、不生成语言、不发消息。人工/助手仍需准确理解截图和事实；这些测试不能证明其读图准确或某条回复能产生恋爱效果。软件分数、文档数量与测试通过数均不作为兴趣或成功概率。

实际检查结果记录在[结构报告](../knowledge/provenance/os_validation.json)与[本轮记录](../knowledge/provenance/os_round_2026-11-02.md)。

本轮增加逐文件阅读台账的身份、连续区间与计数一致性，以及方法卡与JSON同步检查。这些校验不能证明阅读行为，只防止来源状态和范围自相矛盾。最新实际结果见[核心精读检查](../knowledge/provenance/core_reading_validation.json)。

2026-11-03追加一般活动意愿与具体约定的区分、拒绝优先级，以及公开归档计数和阅读范围一致性检查。当前实际检查与剩余断点见[续读验收](../knowledge/provenance/continuation_validation_2026-11-03.json)和[报告](../knowledge/provenance/continuation_2026-11-03.md)。

2026-11-03后续验收增加拒绝渠道与全部联系的区分，以及局部阅读断点错误、复用页摘要不同的反例检查。实际输出见[剩余来源验收](../knowledge/provenance/remaining_sources_validation_2026-11-03.json)，范围与尚未阅读部分见[报告](../knowledge/provenance/remaining_sources_2026-11-03.md)。

2026-11-10：B004–B006续读后的两项规定检查均实际运行通过；7项测试涉及56个虚构路由场景。原始PDF身份、三份逐页台账、连续分段、旧B004范围衔接、15/119计数与方法卡同步另核通过。实际输出及限制见[本轮检查记录](../knowledge/provenance/B004_B006_validation_2026-11-10.json)。

2026-11-11：新增S23后，上传来源检查从22项改为23项；全部来源为158条。B007与S23的身份、连续范围、视觉限制、附录72条及未核66/64的区别另做本轮检查。规定两项命令的真实输出见[本轮检查记录](../knowledge/provenance/B007_S23_validation_2026-11-11.json)；不以元数据检查证明阅读或恋爱效果。

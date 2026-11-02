# 检查范围

本系统有两类可执行检查：资料结构检查，以及45个虚构对话场景的路由检查。场景文件不含用户或女生的真实聊天。

```bash
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
python scripts/route.py --facts system/EXAMPLE_FACTS.json
python scripts/search_knowledge.py 'Callback 共同话题'
```

结构检查核方法与来源引用、内部文件链接、归档与固定blob/SHA-256一致、许可证存在。场景检查覆盖输入缺口、正常问题、封闭短答、慢回未知、反复低投入、后续新投入、具体邀约、替代安排、已答应后的短回复、取消、纠正、同意与边界、用户已发后等待。

命令行路由接受人工核对的事实，不识别图片、不读心、不调用模型、不生成语言、不发消息。人工/助手仍需准确理解截图和事实；这些测试不能证明其读图准确或某条回复能产生恋爱效果。软件分数、文档数量与测试通过数均不作为兴趣或成功概率。

实际检查结果记录在[结构报告](../knowledge/provenance/os_validation.json)与[本轮记录](../knowledge/provenance/os_round_2026-11-02.md)。

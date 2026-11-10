# 检查范围

当前已通过结构检查与20项单元测试，覆盖资料身份、配置、笔记段落、输出约定和84个虚构对话场景；不含用户或女生的真实聊天。最新真实结果见[系统维护检查记录](../knowledge/provenance/OS_runtime_validation_2026-11-11.json)。

```bash
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
python scripts/coach.py --request system/EXAMPLE_REQUEST.json
python scripts/search_knowledge.py '没给替代时间'
```

结构检查核方法与来源引用、内部文件链接、归档blob/SHA-256与许可证、阅读台账身份和连续范围、来源统计与书签同步、26处首选段落和五种任务约定。上传数从来源登记推导，不再靠手改一个固定常数。

单元测试核虚构场景路由优先级、不同对象不串用、stdin与非法输入、五种输出约定、草稿结构、实际段落范围、检索以及错误统计/书签/段落被拒绝。新增场景包含没空无替代与安排话题的冲突、旧约定/短答遇到新的认真内容、赞美与边界；原有拒绝、修复、完整短答、求助、取消、替代时间、等待等场景继续检查。

检查通过不能证明元数据对应的阅读行为，也不能证明真实截图识别、心理机制或恋爱效果。统一入口接受人工核对的事实，只返回一个处理提纲，不调用模型、不读图、不生成或发送语言。草稿检查不判断事实、语气、问句含义或效果。

## 历史记录

- [首次系统检查](../knowledge/provenance/os_validation.json)、[首次系统报告](../knowledge/provenance/os_round_2026-11-02.md)。
- [核心精读检查](../knowledge/provenance/core_reading_validation.json)。
- [续读验收](../knowledge/provenance/continuation_validation_2026-11-03.json)与[报告](../knowledge/provenance/continuation_2026-11-03.md)。
- [剩余来源验收](../knowledge/provenance/remaining_sources_validation_2026-11-03.json)与[报告](../knowledge/provenance/remaining_sources_2026-11-03.md)。
- [B004–B006检查](../knowledge/provenance/B004_B006_validation_2026-11-10.json)。
- [B007/S23检查](../knowledge/provenance/B007_S23_validation_2026-11-11.json)。

历史报告里的测试数与阅读数属于其当时范围，不覆盖这次实际检查。

2026-11-11续读B008：当前17/119份现有文字完成；结构与20项测试通过，84个虚构路由场景不增加。另核原始blob、新提取身份、174页和15段连续范围、33页视觉与141页未核版式、方法卡及新笔记链接。真实输出见[B008检查](../knowledge/provenance/B008_validation_2026-11-11.json)，范围见[完成报告](../knowledge/provenance/B008_completion_2026-11-11.md)。

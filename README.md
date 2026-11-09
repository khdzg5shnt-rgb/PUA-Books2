bk系统
# Books2：聊天截图 → 相关方法 → 一句回复

[开始使用](START_HERE.md) · [场景路由](system/SCENARIO_ROUTER.md) · [方法卡](system/METHOD_CARDS.md) · [全部来源](system/SOURCE_INTEGRATION.md) · [当前进度](CURRENT_STATE.md)

把书籍、上传资料与恋爱相关GitHub来源整理为同一个可查阅的指导系统。日常只需这个仓库：核截图与上下文，定位场景和方法，按真实信息生成一句自然回复；必要时建议先不发。

## 现在可以使用

- 29条有优先顺序的场景路由，处理接话、认真提问、双向调侃、共同旧梗、情绪分享、邀约、确认时间、取消与替代安排、连续低投入、纠正、修复和边界。
- 26张方法卡，分别写明适用事实、操作、禁用条件和仓库内出处；统一生成一个首选成品。
- 原始126项、22项上传材料、9个公开外部GitHub来源统一登记；已采用内容可在仓库内找到，未读与缺失范围明确。
- 原有书籍笔记、主题笔记、C01–C18公开教学案例和许可归档继续有效。

源材料数量不是阅读完成率。TOP30的30份现有文字已全部核读；119份原始书籍中仍有108份未通读。节选、原著与图像缺口见当前进度。系统可用与全库精读完成是两项不同状态。

这里是助手读取和执行的规则、知识与检索工具，不是自行连微信的应用。命令行只选择主方法和资料，不自行理解截图或生成语言。不保存真实私人聊天，不自动发送消息，不承诺某句话保证成功。

```bash
python scripts/route.py --facts /path/to/verified_facts.json
python scripts/search_knowledge.py '回扣 共同话题'
python scripts/validate_os.py
python -m unittest discover -s tests -p 'test_*.py'
```

原始书籍沿用现有来源身份；新增项目文档仅在许可范围内保存，具体出处、文件哈希和阅读状态见[整合清单](system/SOURCE_INTEGRATION.md)。

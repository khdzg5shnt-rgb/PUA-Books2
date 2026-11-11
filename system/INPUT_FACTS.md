# 路由事实字段

这些字段由当前助手核对截图后使用，不是发给用户的问卷。未知的布尔值保持false，未知的分类用默认值；false不等于已证明相反。不要根据检索词、字数、回复速度或方法名自动填值。

## 当前轮与历史分开

收到新回复后，重核latest_sender、pending_reply、function、closed_answer_complete与当前低投入标记。明确已核`latest_sender=other`会清除旧pending；明确为user则设为已发待回，unknown不猜方向。没有等待时necessary_new_logistics不再作为补发例外。邀请字段只表示仍有效的回应或待落实安排，不作永久对象标签；已给过的活动拒绝保留其范围，不能因出现新话题又重新追约。既有明确联系、身体和关系边界不能用新表情或普通回复自动解除。

consecutive_low_rounds只统计可见连续轮次。认真提问、求助、明确安排、具体新分享和完整回答不因文字少而算低投入；路由会清除与这些事实冲突的低投入计数，并在fact_adjustments中列出字段。其他矛盾不靠猜测自动消解，需回看原句。

`function=banter`且`reciprocity=mutual`应有当前确实双向接梗的依据，不能只用“哈哈”或表情填写；已核成立时，旧连续低投入计数不覆盖本轮。事实原输入与其他对象不被改写。

## 字段表

| 字段 | 默认值 | 核对含义 |
| --- | --- | --- |
| `speaker_verified` | `false` | 已核对当前对象及每侧发言人；未知不能填true |
| `text_legible` | `false` | 已读清会改变本轮回复的最新原句与引用；未知不能填true |
| `latest_sender` | `"unknown"` | 最近一条已发送的双方消息：user、other或unknown；排除系统提示、引用与输入框草稿 |
| `pending_reply` | `false` | 当前最后一条是用户已发且对方未回；已有新回复时重置false |
| `necessary_new_logistics` | `false` | 未回期间确有独立必要的新事务，不能借机催问 |
| `refusal_scope` | `"none"` | 当前明确拒绝的具体范围；不由语气、单字或旧标签推断 |
| `boundary_expressed` | `false` | 当前已确认具体话题/称呼等边界，不等于拒绝全部联系 |
| `current_scope_relation` | `"unknown"` | 已核当前内容与已有被拒方向的关系：同一、不同或尚不清楚；不同不表示边界撤回 |
| `repair_needed` | `false` | 有证据确认具体行为及影响需要修复；不默认归责用户 |
| `invitation` | `"none"` | 本轮仍有效的邀约回应或待落实安排；不是对象永久状态 |
| `function` | `"unknown"` | 最新一轮最需要回应的作用；认真提问/求助优先于旧短答标签 |
| `closed_answer_complete` | `false` | 她的简短回答已完成一个封闭问题；新认真内容不被该标记盖过 |
| `consecutive_low_rounds` | `0` | 截至当前可见窗口连续低投入轮数；历史缺口不能当作从无主动 |
| `current_turn_low` | `false` | 本轮是否仍无展开、无反问且无新信息；不能只按字数判断 |
| `reciprocity` | `"unknown"` | 可见行为中的双向或持续单边状态，不是人格或兴趣概率 |
| `goal` | `"reply"` | 用户本轮目标；不覆盖明确拒绝、认真提问或现实安排 |
| `invite_ready` | `false` | 已核有适合提出邀请的事实基础；未知不自动满足 |
| `user_availability_known` | `false` | 用户真实空闲已核实，不编日期 |
| `activity_verified` | `false` | 拟提活动和安排真实已核实，不编顺路或假活动 |
| `shared_callback_available` | `false` | 双方确实有这个共同经历/旧话题，不移植别人的故事 |
| `roleplay_shared` | `false` | 双方正在自愿接同一个角色玩笑，不等于现实身份或其他许可 |
| `advice_requested` | `false` | 她明确求办法；不是看见情绪就假定要被指导 |
| `urgent_practical_need` | `false` | 有已核的紧要现实事务，不是制造紧迫感 |

## 分类可选值

| 字段 | 可选值 |
| --- | --- |
| `latest_sender` | `unknown`, `user`, `other` |
| `current_scope_relation` | `unknown`, `same`, `different` |
| `refusal_scope` | `none`, `contact`, `physical`, `romance`, `activity`, `channel` |
| `invitation` | `none`, `accepted`, `alternative`, `cancelled_with_repair`, `no_alternative`, `cancelled_without_repair`, `open_to_activity` |
| `function` | `unknown`, `insult`, `logistics`, `correction`, `distress`, `advice_request`, `good_news`, `question`, `post_date`, `banter`, `opening`, `sharing`, `appreciation` |
| `reciprocity` | `unknown`, `mutual`, `consistently_one_sided` |
| `goal` | `reply`, `invite`, `appreciate` |

`function=sharing`必须是拒绝之外确实新增的内容；拒绝理由本身不算另一项新分享。只有拒绝本身时按拒绝处理；同轮还有问题或求助时用当前最需要回应的作用。具体边界仍由refusal_scope或boundary_expressed保留，不由正常回复自动清空。

`function=appreciation`表示她确实赞美或表达好意；`goal=appreciate`表示用户想表达欣赏，方向不同。普通礼貌可自然承接，不等于关系意愿。

`current_scope_relation=different`只在确有另一项允许范围的内容或安排时填。换日期再约被拒活动、拒绝理由或笑着说不都不算不同。若同一个活动后来由对方本人明确重新答应，先据原话更新当前事实，不让仍有效的拒绝与新同意同时冒充事实。关系不明且会影响落实安排时，R00S只向用户核一项；有可用上下文就先自行核准。详见[范围说明](CONTENT_SCOPE.md)。

## 请求格式

单对象：`{"task":"reply","facts":{"speaker_verified":true,"text_legible":true,"latest_sender":"other","function":"question"}}`。没有核读的内容不能照抄true。

临时多对象：`{"task":"analysis","cases":{"a":{},"b":{}},"case_key":"b"}`。每个facts对象独立、缺口用自身默认值；不能同时提供全局facts。`--case`和`--task`显式参数优先于请求中的选择。

可选candidate是一条待核草稿，结果不回显草稿。不要加入原句、姓名、账号、截图、地址或对象身份字段；需要保留的上下文只在当前对话核对。stdin不会把请求保存到仓库；手动创建私人输入文件也不得提交。

可选`focus`是至多160字符的检索短词组，由助手按当前内容需要使用，不是另一个事实字段。它只在已选主方法的引用文件里缩小到一个段落；不改变主方法或行动。无需检索时省略或给空字符串，不填null；未命中保留首选，结果不回显词组。不要用它放聊天原文或个人信息。

示例见[EXAMPLE_REQUEST.json](EXAMPLE_REQUEST.json)，完整流程见[RUNBOOK.md](RUNBOOK.md)。

# 路由事实字段

这些字段由当前助手核对截图后使用，不是发给用户的问卷。未知的布尔值保持false，未知的分类用默认值；false不等于已证明相反。不要根据检索词、字数、回复速度或方法名自动填值。

## 当前轮与历史分开

`text_legible=false`仍表示原句未读清，不为绕过核对改成true。只在reply已核待回且无必要新事务、或已核空对话的首次开场时，正文不是该动作的必需输入。解释、分析、复盘、训练、新回复与独立必要通知仍核其需要的原句。对象或方向未知不适用。

`repair_needed`和更正不替代当前求助：R16先答所求，`current_limits`保留已确认的责任与使用更正事实的要求；不据求助新增过错。

收到新回复后，重核latest_sender、pending_reply、function、closed_answer_complete与当前低投入标记。明确已核`latest_sender=other`会清除旧pending；明确为user则设为已发待回，unknown不猜方向。unknown或省略且无已核待回时，入口先给方向核对；默认pending_reply=false不能授权新草稿。已核尚无任何已发消息的首次开场可用none，不需要虚构一条对方消息。没有等待时necessary_new_logistics不再作为补发例外。邀请字段只表示仍有效的回应或待落实安排，不作永久对象标签；已给过的活动拒绝保留其范围，不能因出现新话题又重新追约。既有明确联系、身体和关系边界不能用新表情或普通回复自动解除。

consecutive_low_rounds只统计可见连续轮次。认真提问、求助、明确安排、具体新分享和完整回答不因文字少而算低投入；路由会清除与这些事实冲突的低投入计数，并在fact_adjustments中列出字段。其他矛盾不靠猜测自动消解，需回看原句。

`function=banter`且`reciprocity=mutual`应有当前确实双向接梗的依据，不能只用“哈哈”或表情填写；已核成立时，旧连续低投入计数不覆盖本轮。事实原输入与其他对象不被改写。

## 字段表

| 字段 | 默认值 | 核对含义 |
| --- | --- | --- |
| `speaker_verified` | `false` | 已核对当前对象及每侧发言人；未知不能填true |
| `text_legible` | `false` | 已读清会改变本轮回复的最新原句与引用；未知不能填true |
| `latest_sender` | `"unknown"` | 最近已发方向：user、other或unknown；none仅表示已核尚无已发消息的首次开场；排除系统提示、引用与输入框草稿 |
| `turn_gap` | `"none"` | 已发消息的时序、方向、缺失内容或本轮待答内容仍待核；优先由助手读已有上下文解决。 |
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
| `latest_sender` | `unknown`, `user`, `other`, `none` |
| `turn_gap` | `none`, `order`, `sender`, `missing`, `content` |
| `current_scope_relation` | `unknown`, `same`, `different` |
| `refusal_scope` | `none`, `contact`, `physical`, `romance`, `activity`, `channel` |
| `invitation` | `none`, `accepted`, `alternative`, `cancelled_with_repair`, `no_alternative`, `cancelled_without_repair`, `open_to_activity`, `settled`, `will_update` |
| `function` | `unknown`, `insult`, `logistics`, `correction`, `distress`, `advice_request`, `good_news`, `question`, `post_date`, `banter`, `opening`, `sharing`, `appreciation`, `closing` |
| `reciprocity` | `unknown`, `mutual`, `consistently_one_sided` |
| `goal` | `reply`, `invite`, `appreciate` |

`function=sharing`必须是拒绝之外确实新增的内容；拒绝理由本身不算另一项新分享。只有拒绝本身时按拒绝处理；同轮还有问题或求助时用当前最需要回应的作用。具体边界仍由refusal_scope或boundary_expressed保留，不由正常回复自动清空。

`function=appreciation`表示她确实赞美或表达好意；`goal=appreciate`表示用户想表达欣赏，方向不同。普通礼貌可自然承接，不等于关系意愿。

`current_scope_relation=different`只在确有另一项允许范围的内容或安排时填。换日期再约被拒活动、拒绝理由或笑着说不都不算不同。若同一个活动后来由对方本人明确重新答应，先据原话更新当前事实，不让仍有效的拒绝与新同意同时冒充事实。关系不明且会影响落实安排时，R00S只向用户核一项；有可用上下文就先自行核准。详见[范围说明](CONTENT_SCOPE.md)。

## 请求格式

### 多张图的临时输入

在当前对象的 `facts` 中可附 `screens`。每个子列表按单张图里可见的先后排列。已发气泡使用正整数 `id` 和已核的 `sender`。编号大小没有时间含义。只给同一条已核气泡复用编号。草稿、旧引文、系统行可省略，也可仅记 `kind` 为 `draft`、`quote` 或 `notice`。不放原话、图片、昵称或账号。见[可运行的重叠截图示例](EXAMPLE_REQUEST.json)。

当前对象、仍有效的边界和原有安排状态放在外层；本轮确有安排更新时可按下文标在对应气泡。使用多图时，`function`、`closed_answer_complete`、`current_turn_low`、`advice_requested`、`urgent_practical_need`、`roleplay_shared`、`current_scope_relation` 写在所属已发气泡的 `facts` 中，可按需省略。两张图里同一条气泡的补充标记可以合并；不同气泡的内容观察不拼接，标注冲突时先回图复核。

外层可给`reply_to_id`，表示助手核过原句后选定的本轮主内容。它与`last_id`不同：`last_id`只决定最新发送方向，`reply_to_id`只能选末个连续对方轮次里可证的已发气泡，不能选用户发言、未知发言人或已被用户回复隔开的旧轮。`screen_window.current_turn_ids`列出本轮可选编号。没有多图标注时不提供这个字段。

默认主内容是末条；但同轮前面有问题、求助或紧要事务，后面改为补充、纠正、收尾等不同作用时，程序不能判断前一项是否已经撤回，会给`turn_gap=content`。助手先核上下文，明确选仍待答问题或后来的撤回/纠正，再运行。确实看不到关键原句且影响判断，才向用户补一项。编号只是当前窗口标记，不是消息内容或永久对象档案。

无重叠但有明确日期、时间或用户已说明的先后关系，可在同一 `facts` 中给 `screen_links`，例如 `[[8, 3]]` 表示编号8的已发消息早于编号3。只比较上传顺序不能填写这条关系。同一批图可能有多个可行排序，只要末条唯一就能采用。单图或上下文已清楚时直接走原有平面字段即可；直接填字段而末句不清时用 `turn_gap` 标明缺口。

`settled` 表示活动以及此次所需的时间、集合方式已经过双方确认。`accepted` 仍可能缺一项实际信息。`will_update` 需要对方明确承担下一次确认，例如“我查好告诉你”。“改天吧”本身没有这个承诺。`closing` 只标已经相互收尾的末句，单个“好”、笑声或回复短不足以单独采用。她附了一个新问题或提出地点变更时按该项内容处理。见[虚构对照](CURRENT_TURN.md#安排聊到哪一步)。

### 同轮的安排更新

`invitation`原有外层写法继续可用，表示仍有效的安排状态。多图中若某条对方已发消息确实取消、改期、给替代时间或确认安排，可在该气泡的`facts`里标一个`invitation`；这是核过原话后的显式更新，不是按关键词推断。普通问题、表情和分享不填，气泡中不接受`none`来清空旧拒约。

这一更新与`reply_to_id`分开：主内容可以是前一个问题，后面的取消仍更新本轮安排。只有本轮可确认的对方更新能覆盖外层旧状态；已被用户回复隔开的旧轮不能覆盖。多条更新按截图中的可证先后取最后有效状态，不按上传次序或编号大小决定。不同状态的先后尚不清楚，或更新是否属于本轮尚不清楚时，先核该项；不能借选择主问题跳过它。

| 当前已核的变化 | 标注和处理 |
| --- | --- |
| 先前已定，她本轮明确取消且不给替代 | 更新为`cancelled_without_repair`；其他普通问题仍能答，不再确认旧安排。 |
| 仍愿意参加，但提出的新时间尚未双方确认 | 更新为`accepted`或确有替代时间时`alternative`；核真实可行性，不把新旧时间任一方直接当作已确认。 |
| 她明确说会查好再告知 | 更新为`will_update`；回应同轮其他问题时也把安排确认留给她。 |
| 变更后的必要信息已重新经双方确认 | 更新为`settled`；仅收尾时不用再回。 |

当前输入只描述一个已核活动的安排。多项活动不能混成同一个状态；先由助手在当前上下文分清，本入口不生成个人日程或对象档案。状态更新不撤销身体、恋爱、话题、渠道或私人联系的拒绝，同活动的新同意与旧拒绝仍按范围规则核对。

`screen_window.plan_update`仅给状态码和临时气泡编号，`plan_gap`说明是否缺更新先后或轮次关系。它们不含原话。`current_turn_content`逐条列本轮作用、是否标有问题/求助及主内容；`request_marked`不宣称问题一定仍未解决，后文明确撤回时以原话为准。`turn_coverage`提醒助手核其他请求，仍只用一个主方法和一条成品，不合并成虚构发言。

可运行的[虚构安排变更示例](EXAMPLE_PLAN_UPDATE.json)含三个独立情况：问题加取消、改期待确认、同轮多个请求。默认只选第一个；可用`--case changed_time`或`--case several_requests`切换。没有真实内容，不需用户填写。

### 单对象与多对象

若明确知道更晚的消息被整段裁掉，可同时填 `turn_gap`。程序会保留这个已知缺口，避免把可见片段的末条误当作整轮末条。

单对象：`{"task":"reply","facts":{"speaker_verified":true,"text_legible":true,"latest_sender":"other","function":"question"}}`。没有核读的内容不能照抄true。

临时多对象：`{"task":"analysis","cases":{"a":{},"b":{}},"case_key":"b"}`。每个facts对象独立、缺口用自身默认值；不能同时提供全局facts。`--case`和`--task`显式参数优先于请求中的选择。

可选candidate是一条待核草稿，结果不回显草稿。不要加入原句、姓名、账号、截图、地址或对象身份字段；需要保留的上下文只在当前对话核对。stdin不会把请求保存到仓库；手动创建私人输入文件也不得提交。

可选`focus`是至多160字符的检索短词组，由助手按当前内容需要使用，不是另一个事实字段。它只在已选主方法的精确绑定段落里缩小到一处；不改变主方法或行动。一份笔记被引用不代表其所有段落自动适用，未对齐标题的旧页码定位只保留追溯。无需检索时省略或给空字符串，不填null；未命中保留首选，结果不回显词组。不要用它放聊天原文或个人信息。

维护来源时，`locator`若与唯一现有Markdown标题完全相同，自动作为该段绑定；旧页码式描述可另附非空、无重复的`section_headings`标题列表。首选段落也属于精确绑定。不存在或重复的显式标题会使检查失败，不退化为整本检索。全库检索仍可发现未绑定笔记，但不能据文件级引用直接执行其中任一段。

### 修改同一条未发草稿

`revision`是请求层的可选字段，不是聊天事实。只用于`task=reply`且助手已核草稿尚未发送；修改后仍只交付一个版本。

```json
{"draft_state":"unsent","retained":["no_teasing"],"requested":["shorter","plain"]}
```

| 约束代码 | 当前草稿的要求 |
| --- | --- |
| `shorter` | 再简短一些，保留必要信息 |
| `plain` | 日常说法，去掉文案腔 |
| `no_teasing` | 本条不用调侃或角色玩笑 |
| `no_question` | 本条不追加问题 |

`retained`沿用同一草稿已确认的要求；`requested`是本次新增要求；用户明确取消某项时用`released`列出，不能同时新增和取消同一项。使用`cases`时，revision还必须带与当前所选对象一致的`case_key`，换对象不能沿用。助手负责核对是否确为同一条未发草稿，程序不会保存历史或自动识别这一点。

结构化入口只合并约束，不改变原事实和路由；等待、停止或核对优先，不能借修改草稿补发。`no_question`会收紧现有问号检查；短不短、自然与否、是否还有调侃、是否真实仍须人工判断，不是自动语言评测。原话、候选成品和身份留在当前对话，不加入上述结构，也不提交公开仓库。

示例见[EXAMPLE_REQUEST.json](EXAMPLE_REQUEST.json)，完整流程见[RUNBOOK.md](RUNBOOK.md)。

"""Keep expression feedback separate from sent-message facts; retain no drafts."""

CONSTRAINTS = {
    'shorter': '再简短一些，保留必要信息',
    'plain': '用日常说法，去掉文案和导师口吻',
    'no_teasing': '这一条不用调侃、曲解或角色玩笑',
    'no_question': '这一条不追加问题',
}


def plan_revision(value, *, task, action, selected_case=None, current_window=None):
    """Validate one ephemeral, explicitly unsent draft's expression constraints."""
    allowed = {'draft_state', 'requested', 'retained', 'released', 'case_key', 'turn_anchor'}
    if (not isinstance(value, dict) or set(value) - allowed or
            not {'draft_state', 'requested'}.issubset(value)):
        raise ValueError('revision needs draft_state and requested expression constraints')
    if task != 'reply' or value['draft_state'] != 'unsent':
        raise ValueError('Only an explicitly unsent reply draft can be revised')
    if selected_case is None:
        if 'case_key' in value:
            raise ValueError('Revision case_key requires selected cases')
    elif value.get('case_key') != selected_case:
        raise ValueError('Revision must belong to the explicitly selected case')
    anchor = value.get('turn_anchor')
    if 'turn_anchor' in value and (
            not isinstance(anchor, dict) or set(anchor) != {'last_id', 'reply_to_id'} or
            any(type(item) is not int or item < 1 for item in anchor.values())):
        raise ValueError('turn_anchor needs positive last_id and reply_to_id values')
    if current_window is None:
        anchor_status = 'unavailable' if anchor is not None else 'manual'
    elif (current_window.get('turn_gap') != 'none' or
          any(type(current_window.get(key)) is not int or current_window[key] < 1
              for key in ('last_id', 'reply_to_id'))):
        anchor_status = 'unavailable'
    elif anchor is None:
        anchor_status = 'missing'
    elif all(anchor[key] == current_window[key] for key in anchor):
        anchor_status = 'matched'
    else:
        anchor_status = 'changed'
    groups = {}
    for name in ('requested', 'retained', 'released'):
        items = value.get(name, [])
        if (not isinstance(items, list) or len(items) > len(CONSTRAINTS) or
                any(not isinstance(item, str) or item not in CONSTRAINTS for item in items) or
                len(items) != len(set(items))):
            raise ValueError('Use supported, distinct expression constraint codes')
        groups[name] = items
    if not groups['requested'] and not groups['released']:
        raise ValueError('Revision needs a requested change or an explicit release')
    if set(groups['requested']) & set(groups['released']):
        raise ValueError('Do not request and release the same constraint')
    constraints = list(dict.fromkeys(
        [item for item in groups['retained'] if item not in groups['released']] +
        groups['requested']))
    applied = action == 'draft' and anchor_status in {'manual', 'matched'}
    if not applied:
        constraints = []
    if action != 'draft':
        deliver = '当前动作优先；不以修改草稿绕过等待、停止或核对'
    elif anchor_status == 'changed':
        deliver = '最新已发消息或待答主内容已经变化，不套用旧草稿要求；按当前事实形成一个成品'
    elif anchor_status in {'missing', 'unavailable'}:
        deliver = '先从已有上下文核旧草稿是否仍对应当前消息；未核准前不沿用其表达要求，不自动索要新截图'
    else:
        deliver = '只修改当前未发草稿，仍交付一个成品；不因为改口吻重判对方动机'
    return {
        'applied': applied,
        'anchor_status': anchor_status,
        'constraints': constraints,
        'expression_instructions': [CONSTRAINTS[item] for item in constraints],
        'retain_facts_and_action': True,
        'counts_as_new_message': False,
        'deliver': deliver,
        'scope': '约束只属于同一对象同一条未发草稿；消息编号由读图者核准，'
                 '平面输入仍须人工确认同稿；不保存草稿，不验证措辞是否实现',
    }

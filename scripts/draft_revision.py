"""Keep expression feedback separate from sent-message facts; retain no drafts."""

CONSTRAINTS = {
    'shorter': '再简短一些，保留必要信息',
    'plain': '用日常说法，去掉文案和导师口吻',
    'no_teasing': '这一条不用调侃、曲解或角色玩笑',
    'no_question': '这一条不追加问题',
}


def plan_revision(value, *, task, action, selected_case=None):
    """Validate one ephemeral, explicitly unsent draft's expression constraints."""
    allowed = {'draft_state', 'requested', 'retained', 'released', 'case_key'}
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
    return {
        'applied': action == 'draft',
        'constraints': constraints,
        'expression_instructions': [CONSTRAINTS[item] for item in constraints],
        'retain_facts_and_action': True,
        'counts_as_new_message': False,
        'deliver': ('只修改当前未发草稿，仍交付一个成品；不因为改口吻重判对方动机'
                    if action == 'draft' else '当前动作优先；不以修改草稿绕过等待、停止或核对'),
        'scope': '约束只属于同一对象同一条未发草稿；不保存草稿，不验证措辞是否实现',
    }

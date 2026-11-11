#!/usr/bin/env python3
"""Route verified conversation facts to one method; does not OCR or draft messages."""
import argparse
import json
from pathlib import Path

from knowledge import method_reference
from runtime_io import read_request

ROOT = Path(__file__).resolve().parents[1]


def matches(expr, facts):
    if expr.get('always') is True:
        return True
    if 'all' in expr:
        return all(matches(child, facts) for child in expr['all'])
    if 'any' in expr:
        return any(matches(child, facts) for child in expr['any'])
    actual = facts[expr['field']]
    operation, expected = expr['op'], expr['value']
    if operation == 'eq':
        return actual == expected
    if operation == 'in':
        return actual in expected
    if operation == 'gte':
        return actual >= expected
    raise ValueError('Unsupported condition operation: ' + operation)


def normalize(facts, config):
    if not isinstance(facts, dict):
        raise ValueError('facts must be an object')
    defaults = config['defaults']
    unknown = set(facts) - set(defaults)
    if unknown:
        raise ValueError('Unknown fact fields; use system/router.json defaults')
    value = defaults | facts
    for name, default in defaults.items():
        if type(value[name]) is not type(default):
            raise ValueError('Wrong type for ' + name)
    for name, allowed in config['enums'].items():
        if value[name] not in allowed:
            raise ValueError('Unknown value for ' + name)
    if value['consecutive_low_rounds'] < 0:
        raise ValueError('consecutive_low_rounds must be nonnegative')
    # Direction is explicitly verified by the reader, never guessed from wording.
    if value['latest_sender'] != 'unknown':
        value['pending_reply'] = value['latest_sender'] == 'user'
    if not value['pending_reply']:
        value['necessary_new_logistics'] = False
    if (value['advice_requested'] or value['urgent_practical_need'] or
            value['closed_answer_complete'] or
            (value['function'] == 'banter' and value['reciprocity'] == 'mutual') or
            value['invitation'] in {'accepted', 'alternative', 'cancelled_with_repair',
                                    'open_to_activity'} or
            value['function'] in {'distress', 'advice_request', 'good_news', 'question',
                                  'post_date', 'logistics', 'correction', 'appreciation',
                                  'sharing'}):
        value['current_turn_low'] = False
    # Counts describe consecutive low-effort rounds through the latest round.
    # Do not let stale history erase fresh substantive contact.
    if not value['current_turn_low']:
        value['consecutive_low_rounds'] = 0
    return value


def current_limits(facts):
    """Keep a scoped restriction even when new ordinary content leads the reply."""
    limits = []
    boundary = {
        'contact': '停止私人联系，不另发结束消息，也不换平台继续联系',
        'physical': '停止已拒绝的身体或性方向；普通回复不表示撤回这个边界',
        'romance': '不再推进已拒绝的恋爱方向；普通交流不表示改变关系意愿',
        'activity': '停止被拒绝的活动方向；不换日期追问，也不扩大成拒绝全部联系',
        'channel': '不再索取已拒绝的联系方式或换平台；可按原话在原渠道回应',
    }.get(facts['refusal_scope'])
    if boundary:
        limits.append(boundary)
    if facts['boundary_expressed']:
        limits.append('停止明确不接受的话题或称呼；不借玩笑再试一次')
    if facts['invitation'] in {'no_alternative', 'cancelled_without_repair'}:
        limits.append('原邀约没有替代安排，不换日期追问；可回应她新增的正常内容')
    if facts['current_scope_relation'] == 'different' and (
            facts['refusal_scope'] not in {'none', 'contact'} or facts['boundary_expressed']):
        limits.append('本轮内容已核与被拒方向不同；只回应当前内容，不视为撤回原边界')
    if facts['pending_reply'] and facts['necessary_new_logistics']:
        limits.append('只通知已核实的独立必要新事务，不顺带催回复、试探或重新邀约')
    return limits


def select_route(facts, root=ROOT, *, apply_action_goal=True):
    config = json.loads((root / 'system/router.json').read_text(encoding='utf-8'))
    methods = json.loads((root / 'system/methods.json').read_text(encoding='utf-8'))['methods']
    observations = normalize(facts, config)
    if type(apply_action_goal) is not bool:
        raise ValueError('apply_action_goal must be boolean')
    routing = dict(observations)
    intent_adjustments = []
    if not apply_action_goal and routing['goal'] != 'reply':
        routing['goal'] = 'reply'
        intent_adjustments.append('本次只解释、分析、复盘或训练；行动目标不触发邀约或欣赏草稿')
    if routing['goal'] == 'invite' and (
            observations['refusal_scope'] in {'romance', 'activity'} or
            observations['invitation'] in {'no_alternative', 'cancelled_without_repair'}):
        routing['goal'] = 'reply'
        intent_adjustments.append('当前拒绝或无替代安排仍有效；回应新内容不重开本轮邀约')
    for rule in config['routes']:
        if matches(rule['when'], routing):
            method = next(m for m in methods if m['id'] == rule['method_ids'][0])
            source = method_reference(method['id'], root)
            if rule['action'] in {'hold', 'stop'}:
                output_policy = '不生成给对方的新消息，只向用户说明等待或停止'
            elif rule['action'] == 'clarify':
                output_policy = '只向用户核对一项会改变判断的缺口，不生成给对方的新消息'
            elif rule.get('acknowledgement_only', False):
                output_policy = '必要时只简短承接具体边界，不追加问题，也可不另发'
            else:
                output_policy = '一个主目标；最多一个问题；普通怎么回只给一个成品'
            return {
                'route_id': rule['id'],
                'scenario': rule['name'],
                'action': rule['action'],
                'primary_method': {'id': method['id'], 'name': method['name']},
                'method_card': {key: method[key] for key in
                                ['id', 'name', 'use_when', 'operation', 'avoid',
                                 'evidence_level']},
                'editor_method': 'M26',
                'purpose': rule['purpose'],
                'source': source,
                'read': list(dict.fromkeys(['system/REPLY_PROTOCOL.md', source['path']])),
                'references': method['sources'],
                'fact_adjustments': [key for key in facts
                                     if observations[key] != facts[key]],
                'intent_adjustments': intent_adjustments,
                'current_limits': current_limits(observations),
                'boundary_acknowledgement': rule.get('acknowledgement_only', False),
                'output_policy': output_policy,
                'limitation': '基于人工核对的事实路由；未识别截图、未生成草稿、未计算兴趣或成功率',
            }
    raise ValueError('Missing fallback rule')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--facts', required=True, help='Verified facts JSON; use - for stdin')
    args = parser.parse_args()
    try:
        result = select_route(read_request(args.facts))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

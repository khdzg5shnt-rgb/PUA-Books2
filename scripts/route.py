#!/usr/bin/env python3
"""Route verified conversation facts to one method; does not OCR or draft messages."""
import argparse
import json
from pathlib import Path

from knowledge import method_reference
from runtime_io import read_request, validate_fact_values
from screen_window import BUBBLE_FIELDS, resolve_screens

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
    validate_fact_values(facts, config)
    value = config['defaults'] | facts
    if value['latest_sender'] == 'none' and value['function'] not in {'unknown', 'opening'}:
        raise ValueError('A verified empty conversation cannot contain an incoming message function')
    # Direction is explicitly verified by the reader, never guessed from wording.
    if value['turn_gap'] != 'none':
        # Only a proved outgoing direction makes waiting independent of the gap.
        value['pending_reply'] = value['turn_gap'] == 'order' and value['latest_sender'] == 'user'
    elif value['latest_sender'] != 'unknown':
        value['pending_reply'] = value['latest_sender'] == 'user'
    elif not value['pending_reply'] or value['necessary_new_logistics']:
        # A default false is not evidence that there is an incoming turn.
        # A verified pending flag may conservatively keep waiting, but cannot
        # authorize a new logistics message without a known latest direction.
        value['turn_gap'] = 'sender'
        value['pending_reply'] = False
    if not value['pending_reply']:
        value['necessary_new_logistics'] = False
    if (value['advice_requested'] or value['urgent_practical_need'] or
            value['closed_answer_complete'] or
            (value['invitation'] in {'settled', 'will_update'} and
             value['function'] in {'unknown', 'logistics', 'closing'}) or
            (value['function'] == 'banter' and value['reciprocity'] == 'mutual') or
            value['invitation'] in {'accepted', 'alternative', 'cancelled_with_repair',
                                    'open_to_activity'} or
            value['function'] in {'distress', 'advice_request', 'good_news', 'question',
                                  'post_date', 'logistics', 'correction', 'appreciation',
                                  'sharing', 'closing'}):
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
    if facts['refusal_scope'] == 'contact':
        return limits
    if facts['boundary_expressed']:
        limits.append('停止明确不接受的话题或称呼；不借玩笑再试一次')
    if facts['invitation'] in {'no_alternative', 'cancelled_without_repair'}:
        limits.append('原邀约没有替代安排，不换日期追问；可回应她新增的正常内容')
    if facts['invitation'] == 'will_update':
        limits.append('她已说会再告知安排；时间仍待定，先把确认留给她。')
    if facts['invitation'] == 'settled':
        if facts['refusal_scope'] == 'activity' and facts['current_scope_relation'] != 'different':
            limits.append('这项安排与被拒活动的关系仍需核准，暂不确认赴约。')
        else:
            limits.append('双方已确认这项安排。照用已有信息，只处理这一轮真正新增的内容。')
    if facts['current_scope_relation'] == 'different' and (
            facts['refusal_scope'] not in {'none', 'contact'} or facts['boundary_expressed']):
        limits.append('本轮内容已核与被拒方向不同；只回应当前内容，不视为撤回原边界')
    if facts['pending_reply'] and facts['necessary_new_logistics']:
        limits.append('只通知已核实的独立必要新事务，不顺带催回复、试探或重新邀约')
    return limits


def select_route(facts, root=ROOT, *, apply_action_goal=True):
    config = json.loads((root / 'system/router.json').read_text(encoding='utf-8'))
    methods = json.loads((root / 'system/methods.json').read_text(encoding='utf-8'))['methods']
    window = None
    supplied = facts
    if isinstance(facts, dict) and 'screens' in facts:
        supplied = dict(facts)
        screens = supplied.pop('screens')
        links = supplied.pop('screen_links', [])
        reply_to_id = supplied.pop('reply_to_id', None)
        if 'reply_to_id' in facts and (type(reply_to_id) is not int or reply_to_id < 1):
            raise ValueError('reply_to_id must be a positive bubble ID')
        validate_fact_values(supplied, config)
        if BUBBLE_FIELDS.intersection(supplied):
            raise ValueError('With screens, put current-bubble observations on their sent bubble')
        current, window = resolve_screens(screens, config, links, reply_to_id)
        # An explicitly cropped/missing tail is outside the annotated views.
        reported_gap = supplied.get('turn_gap', 'none')
        if reported_gap != 'none':
            current = {'turn_gap': reported_gap, 'latest_sender': 'unknown', 'pending_reply': False}
            window.update(last_id=None, turn_gap=reported_gap, latest_sender='unknown',
                          current_turn_ids=[], reply_to_id=None, current_turn_content=[])
            window.pop('plan_update', None)
            window.pop('plan_gap', None)
        supplied.update(current)
    observations = normalize(supplied, config)
    if type(apply_action_goal) is not bool:
        raise ValueError('apply_action_goal must be boolean')
    routing = dict(observations)
    intent_adjustments = []
    if not apply_action_goal and routing['goal'] != 'reply':
        routing['goal'] = 'reply'
        intent_adjustments.append('本次只解释、分析、复盘或训练；行动目标不触发邀约或欣赏草稿')
    if routing['goal'] == 'invite' and (
            observations['refusal_scope'] in {'romance', 'activity'} or
            observations['invitation'] in {'accepted', 'alternative', 'cancelled_with_repair',
                                           'no_alternative', 'cancelled_without_repair',
                                           'will_update', 'settled'}):
        routing['goal'] = 'reply'
        intent_adjustments.append('按当前安排或边界处理；回应新内容时不重复邀约')
    # Waiting and a verified first opening do not interpret an incoming body.
    # Keep text_legible unchanged: this is an action-dependent requirement,
    # not a claim that unreadable text has been read. Explanatory tasks still
    # need the actual message, and new logistics still needs its content.
    body_independent_action = apply_action_goal and observations['speaker_verified'] and (
        (observations['pending_reply'] and not observations['necessary_new_logistics']) or
        (observations['latest_sender'] == 'none' and
         observations['function'] == 'opening' and observations['turn_gap'] == 'none'))
    if body_independent_action and not observations['text_legible']:
        intent_adjustments.append('本次只需等待或已核首次开场，不为不影响动作的正文缺口追问；未声称读清正文')
    for rule in config['routes']:
        if rule['id'] == 'R00' and body_independent_action:
            continue
        if matches(rule['when'], routing):
            method = next(m for m in methods if m['id'] == rule['method_ids'][0])
            source = method_reference(method['id'], root)
            if rule['action'] in {'hold', 'stop'}:
                output_policy = '不生成给对方的新消息，只向用户说明等待或停止'
            elif rule['action'] == 'clarify':
                output_policy = '只向用户核对一项会改变判断的缺口，不生成给对方的新消息'
            elif rule.get('acknowledgement_only', False):
                output_policy = '如需回应只简短承接，不追加问题，也可不另发'
            else:
                output_policy = '一个主目标；最多一个问题；普通怎么回只给一个成品'
            result = {
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
                                     if key in observations and observations[key] != facts[key]],
                'intent_adjustments': intent_adjustments,
                'current_limits': current_limits(observations),
                'acknowledgement_only': rule.get('acknowledgement_only', False),
                'boundary_acknowledgement': rule.get('acknowledgement_only', False) and method['id'] == 'M23',
                'output_policy': output_policy,
                'limitation': '基于人工核对的事实路由；未识别截图、未生成草稿、未计算兴趣或成功率',
            }
            if method['id'] == 'M13':
                if observations['repair_needed']:
                    result['current_limits'].append('已核具体行为的责任仍保留；先回应当前所求，不用提供帮助代替必要修复')
                if observations['function'] == 'correction':
                    result['current_limits'].append('按已核更正后的事实回应求助，不沿用旧错误，也不只道歉而漏答所求')
            if window is not None:
                result['screen_window'] = window
            if rule['id'] == 'R00T':
                result['turn_gap'] = observations['turn_gap']
            if rule['id'] == 'R00S':
                result['current_scope_relation'] = observations['current_scope_relation']
            return result
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

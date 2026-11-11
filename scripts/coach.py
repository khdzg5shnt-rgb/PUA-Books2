#!/usr/bin/env python3
"""Build one local reply/analysis brief from verified facts, without storing chats."""
import argparse
import json
import re

from knowledge import ROOT, resolve_reference
from route import select_route
from runtime_io import read_request
from search_knowledge import search


def check_candidate(candidate, task, action, *, max_questions=1, allow_empty=False):
    """Check structure only; no claim to verify facts, tone or dating outcomes."""
    issues = []
    if task != 'reply':
        return {'ok': False, 'issues': ['草稿检查仅用于本轮怎么回'],
                'scope': '不评价事实、自然程度或关系效果'}
    if not isinstance(candidate, str):
        issues.append('只接受一条文字草稿，不接受多个候选')
    elif action != 'draft':
        if candidate.strip():
            issues.append('本轮应等待、停止或核对，不生成给对方的新消息')
    elif not candidate.strip():
        if not allow_empty:
            issues.append('本轮选择回复，但草稿为空')
    else:
        if len(candidate.strip().splitlines()) > 2:
            issues.append('默认回复最多两行')
        if len(re.findall(r'[?？]+', candidate)) > max_questions:
            issues.append('本轮只需简短承接，不追加问题' if max_questions == 0
                          else '本轮最多一个问题')
        if re.search(r'\{[^{}\n]+\}|\[(?:时间|地点|姓名|待确认)\]', candidate):
            issues.append('草稿仍有未替换的事实占位符')
    return {'ok': not issues, 'issues': issues,
            'scope': '仅检查单条、行数、问号和占位符；事实与口吻仍须核对'}


def _select_case(request, case_key):
    allowed = {'task', 'facts', 'cases', 'case_key', 'candidate', 'focus'}
    if not isinstance(request, dict) or set(request) - allowed:
        raise ValueError('Use task, facts, or one explicitly selected case')
    if 'cases' in request:
        if 'facts' in request:
            raise ValueError('Do not mix global facts with individual cases')
        cases = request['cases']
        key = case_key if case_key is not None else request.get('case_key')
        if (not isinstance(cases, dict) or not isinstance(key, str) or
                key not in cases):
            raise ValueError('Select one existing case_key; cases are never merged')
        return cases[key], 'one_selected_case'
    if case_key is not None or 'case_key' in request:
        raise ValueError('case_key requires a cases object')
    return request.get('facts', {}), 'single_case'


def _clarification(facts, decision):
    route_id = decision['route_id']
    if route_id == 'R00T':
        question = {
            'order': '这几条里，最后发出去的是哪一句？',
            'sender': '最后一条已发消息是谁发的？',
            'missing': '最近一条已经发出去的消息是什么？',
        }[decision['turn_gap']]
        return {'field': 'turn_gap', 'question': question}
    if route_id == 'R00S':
        question = ('同一个活动后来有她明确重新答应的原话吗？'
                    if decision['current_scope_relation'] == 'same' else
                    '她现在答应的是之前拒绝的活动，还是另一个安排？')
        return {'field': 'current_scope_relation', 'question': question}
    choices = [('speaker_verified', '这句是谁发的？'),
               ('text_legible', '最近一条已发消息的原话是什么？'),
               ('invite_ready', '你们最近有过什么双向互动？'),
               ('user_availability_known', '你哪天确实有空？'),
               ('activity_verified', '你这次想约什么活动？')]
    for field, question in choices:
        if not facts.get(field):
            return {'field': field, 'question': question}
    raise ValueError('Clarification route has no missing input')


def build_brief(request, root=ROOT, task=None, case_key=None):
    facts, context = _select_case(request, case_key)
    focus = request.get('focus', '')
    if not isinstance(focus, str) or len(focus) > 160:
        raise ValueError('focus must be a short retrieval phrase of at most 160 characters')
    tasks = json.loads((root / 'system/tasks.json').read_text(encoding='utf-8'))['tasks']
    selected_task = task if task is not None else request.get('task', 'reply')
    if not isinstance(selected_task, str) or selected_task not in tasks:
        raise ValueError('Unknown task; use reply, meaning, analysis, review or training')
    decision = select_route(facts, root, apply_action_goal=selected_task == 'reply')
    source = decision['source']
    retrieval = {'mode': 'preferred', 'scope': '只定位本主方法的资料，不改变事实、动作或输出任务'}
    if focus.strip() and decision['action'] == 'draft':
        hits = search(focus, method=decision['primary_method']['id'], limit=1, root=root)
        if hits and hits[0]['query_matched']:
            source = resolve_reference(hits[0], root)
            retrieval['mode'] = 'focused_cited_source'
    contract = dict(tasks[selected_task])
    contract['recipient'] = ('other' if selected_task == 'reply' and
                             decision['action'] == 'draft' else 'user')
    if decision['action'] == 'clarify':
        contract['deliver'] = '只向用户核对一项会改变判断的缺口；不生成给对方的新消息'
        contract['max_questions'] = 1
    if selected_task == 'reply' and decision['action'] != 'draft':
        contract['max_candidates'] = 0
    if selected_task == 'reply' and decision['acknowledgement_only']:
        contract['max_questions'] = 0
        contract['allow_no_message'] = True
        contract['deliver'] = decision['purpose'] + '。可以不另发。若回应，最多一句，不追加问题。'
    result = {
        'task': selected_task,
        'case_context': context,
        'decision': {key: decision[key] for key in
                     ['route_id', 'scenario', 'action', 'purpose']},
        'primary_method': decision['method_card'],
        'read_next': source,
        'read': list(dict.fromkeys(['system/REPLY_PROTOCOL.md', source['path']])),
        'retrieval': retrieval,
        'output_contract': contract,
        'current_limits': decision['current_limits'],
        'fact_adjustments': decision['fact_adjustments'],
        'intent_adjustments': decision['intent_adjustments'],
        'after_this_turn': '只依据实际新回复更新；不编后续，不自动补第二条或设置冷落倒计时',
        'scope': '仅生成一个处理提纲；读图、事实裁决与自然语言由当前助手完成；不存储、不发送',
    }
    if 'screen_window' in decision:
        result['screen_window'] = decision['screen_window']
    if decision['action'] == 'clarify':
        result['clarification'] = _clarification(facts, decision) | {'recipient': 'user'}
    if decision['action'] == 'hold' and selected_task == 'reply':
        result['user_output'] = {
            'R04': '先不发，等她回这一轮。',
            'R14': '先不发，这轮不用继续找话题。',
            'R09C': '不用再回，按刚定好的安排就行。',
            'R13C': '这轮已经聊完了，不用再回。',
        }[decision['route_id']]
    if decision['action'] == 'stop' and selected_task == 'reply':
        result['user_output'] = '先不发，按她的原话停止私人联系。'
    if 'user_output' in result:
        contract['deliver'] = result['user_output']
        contract['max_questions'] = 0
    if selected_task == 'reply' and decision['route_id'] in {'R04N', 'R08', 'R09'}:
        result['before_drafting'] = [
            '已知信息直接用；只有要确认赴约且真实空闲未知时才补缺口，不把对方给时间当作用户已答应',
            '只用当前已确认的活动和安排；缺口可保留，不代编时间、地点或顺路',
        ]
    if 'candidate' in request:
        result['candidate_check'] = check_candidate(
            request['candidate'], selected_task, decision['action'],
            max_questions=contract.get('max_questions', 1),
            allow_empty=contract.get('allow_no_message', False))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, help='Request JSON; - reads stdin')
    parser.add_argument('--task', choices=['reply', 'meaning', 'analysis', 'review', 'training'])
    parser.add_argument('--case', dest='case_key', help='Select one case; never merge cases')
    args = parser.parse_args()
    try:
        result = build_brief(read_request(args.request), task=args.task, case_key=args.case_key)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

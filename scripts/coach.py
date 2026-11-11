#!/usr/bin/env python3
"""Build one local reply/analysis brief from verified facts, without storing chats."""
import argparse
import json
import re

from knowledge import ROOT
from route import select_route
from runtime_io import read_request


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
            issues.append('本轮只需简短承接边界，不追加问题' if max_questions == 0
                          else '本轮最多一个问题')
        if re.search(r'\{[^{}\n]+\}|\[(?:时间|地点|姓名|待确认)\]', candidate):
            issues.append('草稿仍有未替换的事实占位符')
    return {'ok': not issues, 'issues': issues,
            'scope': '仅检查单条、行数、问号和占位符；事实与口吻仍须核对'}


def _select_case(request, case_key):
    allowed = {'task', 'facts', 'cases', 'case_key', 'candidate'}
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


def _clarification(facts, task):
    choices = [('speaker_verified', '这句是谁发的？'),
               ('text_legible', '她最后一句具体说了什么？'),
               ('invite_ready', '你们最近有过什么双向互动？'),
               ('user_availability_known', '你哪天确实有空？'),
               ('activity_verified', '你这次想约什么活动？')]
    for field, question in choices:
        if not facts.get(field):
            return {'field': field, 'question': question}
    raise ValueError('Clarification route has no missing input')


def build_brief(request, root=ROOT, task=None, case_key=None):
    facts, context = _select_case(request, case_key)
    tasks = json.loads((root / 'system/tasks.json').read_text(encoding='utf-8'))['tasks']
    selected_task = task if task is not None else request.get('task', 'reply')
    if not isinstance(selected_task, str) or selected_task not in tasks:
        raise ValueError('Unknown task; use reply, meaning, analysis, review or training')
    decision = select_route(facts, root, apply_action_goal=selected_task == 'reply')
    contract = dict(tasks[selected_task])
    if selected_task == 'reply' and decision['boundary_acknowledgement']:
        contract['max_questions'] = 0
        contract['allow_no_message'] = True
        contract['deliver'] = '如确有必要，只简短承接这项边界；不重提、不试探，不追加问题'
    result = {
        'task': selected_task,
        'case_context': context,
        'decision': {key: decision[key] for key in
                     ['route_id', 'scenario', 'action', 'purpose']},
        'primary_method': decision['method_card'],
        'read_next': decision['source'],
        'read': decision['read'],
        'output_contract': contract,
        'current_limits': decision['current_limits'],
        'fact_adjustments': decision['fact_adjustments'],
        'intent_adjustments': decision['intent_adjustments'],
        'after_this_turn': '只依据实际新回复更新；不编后续，不自动补第二条或设置冷落倒计时',
        'scope': '仅生成一个处理提纲；读图、事实裁决与自然语言由当前助手完成；不存储、不发送',
    }
    if decision['action'] == 'clarify':
        result['clarification'] = _clarification(facts, selected_task)
    if decision['action'] == 'hold' and selected_task == 'reply':
        result['user_output'] = '先不发，等她回这一轮。'
        if decision['route_id'] == 'R14':
            result['user_output'] = '先不发，这轮不用继续找话题。'
    if decision['action'] == 'stop' and selected_task == 'reply':
        result['user_output'] = '先不发，按她的原话停止私人联系。'
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

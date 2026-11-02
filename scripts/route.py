#!/usr/bin/env python3
"""Route verified conversation facts to one method; does not OCR or draft messages."""
import argparse
import json
from pathlib import Path

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
        raise ValueError('Unknown facts: ' + ', '.join(sorted(unknown)))
    value = defaults | facts
    for name, default in defaults.items():
        if type(value[name]) is not type(default):
            raise ValueError('Wrong type for ' + name)
    for name, allowed in config['enums'].items():
        if value[name] not in allowed:
            raise ValueError('Unknown value for ' + name)
    if value['consecutive_low_rounds'] < 0:
        raise ValueError('consecutive_low_rounds must be nonnegative')
    if (value['advice_requested'] or value['urgent_practical_need'] or
            value['function'] in {'distress', 'advice_request', 'good_news', 'question',
                                  'post_date', 'logistics', 'correction'}):
        value['current_turn_low'] = False
    # Counts describe consecutive low-effort rounds through the latest round.
    # Do not let stale history erase fresh substantive contact.
    if not value['current_turn_low']:
        value['consecutive_low_rounds'] = 0
    return value


def select_route(facts, root=ROOT):
    config = json.loads((root / 'system/router.json').read_text(encoding='utf-8'))
    methods = json.loads((root / 'system/methods.json').read_text(encoding='utf-8'))['methods']
    observations = normalize(facts, config)
    for rule in config['routes']:
        if matches(rule['when'], observations):
            method = next(m for m in methods if m['id'] == rule['method_ids'][0])
            return {
                'route_id': rule['id'],
                'scenario': rule['name'],
                'action': rule['action'],
                'primary_method': {'id': method['id'], 'name': method['name']},
                'editor_method': 'M26',
                'purpose': rule['purpose'],
                'read': list(dict.fromkeys(['system/REPLY_PROTOCOL.md', 'system/METHOD_CARDS.md'] +
                                          [s['path'] for s in method['sources']])),
                'output_policy': '一个主目标；最多一个问题；普通怎么回只给一个成品；hold不再编结束消息',
                'limitation': '基于人工核对的事实路由；未识别截图、未生成草稿、未计算兴趣或成功率',
            }
    raise ValueError('Missing fallback rule')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--facts', type=Path, required=True, help='Verified facts JSON, not raw OCR text')
    args = parser.parse_args()
    try:
        result = select_route(json.loads(args.facts.read_text(encoding='utf-8')))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

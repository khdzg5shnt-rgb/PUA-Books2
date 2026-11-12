"""Workflow regressions using synthetic facts only, never real chats."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief, check_candidate
from knowledge import load_methods, method_reference, resolve_reference
from route import select_route
from search_knowledge import search
from validate_os import validate

VERIFIED = {'speaker_verified': True, 'text_legible': True, 'latest_sender': 'other'}


class RuntimeWorkflow(unittest.TestCase):
    def test_selected_case_never_inherits_another_case(self):
        request = {'cases': {
            'SYNTHETIC_PRIVATE_ALIAS': VERIFIED | {'refusal_scope': 'contact'},
            'current': VERIFIED | {'function': 'question'}}, 'case_key': 'current'}
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['case_context'], 'one_selected_case')
        self.assertNotIn('SYNTHETIC_PRIVATE_ALIAS', json.dumps(result))
        self.assertEqual(build_brief(request, case_key='SYNTHETIC_PRIVATE_ALIAS')
                         ['decision']['route_id'], 'R01')

    def test_missing_or_ambiguous_case_fails_instead_of_guessing(self):
        for request in [{'cases': {'a': VERIFIED}},
                        {'cases': {'a': VERIFIED}, 'case_key': 'missing'},
                        {'cases': {'a': VERIFIED}, 'case_key': 'a', 'facts': VERIFIED},
                        {'facts': VERIFIED, 'case_key': 'a'}, {'facts': []}]:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    build_brief(request)

    def test_one_missing_fact_and_no_forced_invitation(self):
        result = build_brief({'facts': {}})
        self.assertEqual(result['clarification']['field'], 'speaker_verified')
        result = build_brief({'facts': VERIFIED | {'goal': 'invite', 'invite_ready': True}})
        self.assertEqual(result['clarification']['field'], 'user_availability_known')
        self.assertEqual(build_brief({'facts': VERIFIED})['decision']['route_id'], 'R28')

    def test_task_selection_changes_contract_not_observed_facts(self):
        request = {'facts': VERIFIED | {'function': 'question'}}
        results = [build_brief(request, task=task) for task in
                   ['reply', 'meaning', 'analysis', 'review', 'training']]
        self.assertEqual({item['decision']['route_id'] for item in results}, {'R18'})
        self.assertEqual(results[0]['output_contract']['max_candidates'], 1)
        self.assertIn('关键未知', results[1]['output_contract']['required_parts'])
        self.assertEqual(results[2]['output_contract']['max_next_steps'], 1)
        self.assertFalse(results[3]['output_contract']['force_user_blame'])
        self.assertEqual(results[4]['output_contract']['max_exercises'], 1)

    def test_draft_is_single_and_not_echoed_or_allowed_while_waiting(self):
        request = {'facts': VERIFIED | {'function': 'question'},
                   'candidate': 'SYNTHETIC_SECRET_DRAFT'}
        result = build_brief(request)
        self.assertTrue(result['candidate_check']['ok'])
        self.assertNotIn('SYNTHETIC_SECRET_DRAFT', json.dumps(result))
        result = build_brief({'facts': VERIFIED | {'latest_sender': 'user', 'pending_reply': True},
                              'candidate': '还要追问吗？'})
        self.assertEqual(result['decision']['action'], 'hold')
        self.assertFalse(result['candidate_check']['ok'])
        self.assertIn('先不发', result['user_output'])
        for candidate in [['甲', '乙'], '你在哪？几点下班？', '甲\n乙\n丙', '周六去{地点}？']:
            with self.subTest(candidate=candidate):
                self.assertFalse(check_candidate(candidate, 'reply', 'draft')['ok'])

    def test_new_content_preserves_refusal_limit_without_reinviting(self):
        result = build_brief({'facts': VERIFIED | {
            'invitation': 'no_alternative', 'function': 'question'}})
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertTrue(any('不换日期追问' in item for item in result['current_limits']))

    def test_stale_low_effort_is_reported_and_does_not_erase_new_help_request(self):
        result = build_brief({'facts': VERIFIED | {'function': 'advice_request',
                             'current_turn_low': True, 'consecutive_low_rounds': 4}})
        self.assertEqual(result['decision']['route_id'], 'R16')
        self.assertEqual(set(result['fact_adjustments']),
                         {'current_turn_low', 'consecutive_low_rounds'})

    def test_stdin_entrypoint_and_invalid_requests_do_not_echo_input(self):
        command = [sys.executable, str(ROOT / 'scripts/coach.py'), '--request', '-']
        result = subprocess.run(command, input=json.dumps({'facts': VERIFIED}),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['decision']['route_id'], 'R28')
        for value in ['{"facts":{},"facts":{},"SYNTHETIC_PRIVATE_MARKER":1}',
                      '{"facts":{"consecutive_low_rounds":NaN}}',
                      '{"facts":{"SYNTHETIC_PRIVATE_MARKER":true}}', '[]']:
            result = subprocess.run(command, input=value, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            self.assertNotIn('SYNTHETIC_PRIVATE_MARKER', result.stderr + result.stdout)

    def test_new_sender_updates_waiting_without_changing_other_cases(self):
        for sender, old_pending, expected, changed in [
                ('other', True, 'R18', True), ('user', False, 'R04', True),
                ('unknown', True, 'R04', False)]:
            facts = VERIFIED | {'latest_sender': sender, 'pending_reply': old_pending,
                                'function': 'question'}
            original = dict(facts)
            result = build_brief({'facts': facts})
            self.assertEqual(result['decision']['route_id'], expected)
            self.assertEqual('pending_reply' in result['fact_adjustments'], changed)
            self.assertEqual(facts, original)
        request = {'cases': {'a': VERIFIED | {'latest_sender': 'user'},
                             'b': VERIFIED | {'latest_sender': 'other', 'function': 'question'}},
                   'case_key': 'b'}
        self.assertEqual(build_brief(request)['decision']['route_id'], 'R18')

    def test_new_normal_content_keeps_each_scoped_boundary(self):
        for scope, limit in [('physical', '身体'), ('romance', '恋爱'),
                             ('channel', '联系方式'), ('activity', '活动')]:
            with self.subTest(scope=scope):
                result = build_brief({'facts': VERIFIED | {
                    'refusal_scope': scope, 'function': 'question'}})
                self.assertEqual(result['decision']['route_id'], 'R18')
                self.assertTrue(any(limit in value for value in result['current_limits']))
        result = build_brief({'facts': VERIFIED | {
            'boundary_expressed': True, 'function': 'question'}})
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertTrue(any('话题或称呼' in value for value in result['current_limits']))

    def test_boundary_only_acknowledgement_has_no_extra_question(self):
        for facts in [{'refusal_scope': 'physical'}, {'refusal_scope': 'romance'},
                      {'refusal_scope': 'channel'}, {'refusal_scope': 'activity'},
                      {'boundary_expressed': True}]:
            with self.subTest(facts=facts):
                result = build_brief({'facts': VERIFIED | facts, 'candidate': '明白，不再提这个。'})
                self.assertEqual(result['decision']['action'], 'draft')
                self.assertEqual(result['output_contract']['max_questions'], 0)
                self.assertTrue(result['candidate_check']['ok'])
                self.assertIn('不追加问题', select_route(VERIFIED | facts)['output_policy'])
                result = build_brief({'facts': VERIFIED | facts, 'candidate': '那还能再问吗？'})
                self.assertFalse(result['candidate_check']['ok'])
                result = build_brief({'facts': VERIFIED | facts, 'candidate': ''})
                self.assertTrue(result['output_contract']['allow_no_message'])
                self.assertTrue(result['candidate_check']['ok'])
        self.assertFalse(check_candidate('', 'reply', 'draft')['ok'])

    def test_contact_refusal_stops_even_with_new_content_or_logistics(self):
        for facts in [{'latest_sender': 'other', 'function': 'question'},
                      {'latest_sender': 'user', 'necessary_new_logistics': True}]:
            with self.subTest(facts=facts):
                result = build_brief({'facts': VERIFIED | facts | {'refusal_scope': 'contact'},
                                      'candidate': '再解释一下。'})
                self.assertEqual(result['decision']['action'], 'stop')
                self.assertIn('先不发', result['user_output'])
                self.assertFalse(result['candidate_check']['ok'])

    def test_explanatory_tasks_do_not_request_dates_or_make_action_drafts(self):
        facts = VERIFIED | {'goal': 'invite', 'invite_ready': True}
        for task in ['meaning', 'analysis', 'review', 'training']:
            with self.subTest(task=task):
                result = build_brief({'task': task, 'facts': facts})
                self.assertNotIn('clarification', result)
                self.assertNotIn('before_drafting', result)
                self.assertNotIn(result['decision']['route_id'], {'R20', 'R21'})
                self.assertTrue(result['intent_adjustments'])
                self.assertEqual(result['task'], task)
        self.assertEqual(build_brief({'facts': facts})['clarification']['field'],
                         'user_availability_known')
        with self.assertRaises(ValueError):
            build_brief({'task': 'analysis', 'facts': VERIFIED | {'goal': 'INVALID'}})

    def test_independent_logistics_survives_old_invitation_but_never_reopens_it(self):
        facts = VERIFIED | {'latest_sender': 'user', 'necessary_new_logistics': True,
                            'invitation': 'no_alternative', 'refusal_scope': 'activity'}
        result = build_brief({'facts': facts})
        self.assertEqual(result['decision']['route_id'], 'R04N')
        self.assertEqual(result['primary_method']['id'], 'M15')
        self.assertTrue(any('只通知' in value for value in result['current_limits']))
        self.assertTrue(any('不换日期追问' in value for value in result['current_limits']))
        self.assertIn('before_drafting', result)
        facts['latest_sender'] = 'other'
        facts['function'] = 'question'
        result = build_brief({'facts': facts})
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertIn('necessary_new_logistics', result['fact_adjustments'])

    def test_fresh_sharing_does_not_reopen_refused_invitation_or_erase_history(self):
        facts = VERIFIED | {'invitation': 'no_alternative', 'function': 'sharing',
                            'goal': 'invite', 'invite_ready': True,
                            'user_availability_known': True, 'activity_verified': True,
                            'current_turn_low': True, 'consecutive_low_rounds': 4,
                            'reciprocity': 'consistently_one_sided'}
        result = build_brief({'facts': facts})
        self.assertEqual(result['decision']['route_id'], 'R27')
        self.assertEqual(set(result['fact_adjustments']), {'current_turn_low', 'consecutive_low_rounds'})
        self.assertTrue(result['intent_adjustments'])
        self.assertEqual(facts['reciprocity'], 'consistently_one_sided')

    def test_sender_and_scope_contract_validate_inputs_without_echoing(self):
        command = [sys.executable, str(ROOT / 'scripts/coach.py'), '--request', '-']
        for marker in ['SYNTHETIC_PRIVATE_MARKER', 123]:
            result = subprocess.run(command, input=json.dumps({'facts': VERIFIED | {
                'latest_sender': marker}}), text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            self.assertNotIn('SYNTHETIC_PRIVATE_MARKER', result.stderr + result.stdout)


class SectionRetrieval(unittest.TestCase):
    def test_each_method_resolves_one_real_cited_section(self):
        for method_id, method in load_methods().items():
            with self.subTest(method=method_id):
                item = method_reference(method_id)
                self.assertIn(item['path'], {s['path'] for s in method['sources']})
                lines = (ROOT / item['path']).read_text(encoding='utf-8').splitlines()
                text = '\n'.join(lines[item['line']-1:item['end_line']]).strip()
                self.assertTrue(text.startswith('#'))
                self.assertEqual(item['excerpt'], text[:1600])
                self.assertEqual(item['excerpt_complete'], len(text) <= 1600)
                self.assertGreater(item['end_line'], item['line'])

    def test_routes_keep_one_lead_source_instead_of_a_source_dump(self):
        scenarios = json.loads((ROOT / 'tests/synthetic_scenarios.json').read_text())
        for case in scenarios:
            item = select_route(case['facts'])
            self.assertLessEqual(len(item['read']), 2)
            self.assertIn(item['source']['path'], item['read'])
            self.assertEqual(item['method_card']['id'], item['primary_method']['id'])

    def test_scene_phrase_and_direct_method_beat_incidental_source_lists(self):
        hit = search('没给替代时间', 1)[0]
        self.assertEqual(hit['heading'], '没有替代安排时收住')
        self.assertEqual(hit['method_ids'], ['M17'])
        hit = search('', method='M14', limit=1)[0]
        self.assertEqual(hit['heading'], '提出一次具体邀请')
        self.assertEqual(search('M14', limit=1)[0]['path'], hit['path'])
        self.assertNotIn('METHOD_CARDS', hit['path'])

    def test_missing_heading_or_outside_reference_fails(self):
        for reference in [{'path': 'START_HERE.md', 'heading': 'MISSING_HEADING'},
                          {'path': '../run_state/os6_data.py', 'heading': 'anything'}]:
            with self.assertRaises(ValueError):
                resolve_reference(reference)

    def test_maintenance_rejects_statistics_section_and_bookmark_drift(self):
        mutations = [('system/sources.json',
                      lambda d: d['statistics'].update(uploads=999),
                      'Source statistics do not match records'),
                     ('system/knowledge_map.json',
                      lambda d: d['methods']['M17']['preferred'].update(heading='MISSING'),
                      'Invalid preferred method section: M17'),
                     ('system/work_state.json',
                      lambda d: d['reading_bookmark'].update(next_file_page=999),
                      'Runtime reading bookmark does not match source state')]
        with tempfile.TemporaryDirectory(prefix='books2-runtime-check-') as folder:
            copied = Path(folder) / 'repo'
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns('__pycache__', '.git'))
            for relative, mutate, error in mutations:
                path = copied / relative
                original = path.read_text(encoding='utf-8')
                data = json.loads(original)
                mutate(data)
                path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                self.assertIn(error, validate(copied)['errors'])
                path.write_text(original, encoding='utf-8')

    def test_maintenance_rejects_human_route_order_and_bad_acknowledgement(self):
        with tempfile.TemporaryDirectory(prefix='books2-scope-check-') as folder:
            copied = Path(folder) / 'repo'
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns('__pycache__', '.git'))
            path = copied / 'system/SCENARIO_ROUTER.md'
            original = path.read_text(encoding='utf-8')
            path.write_text(original.replace('| R01 |', '| MISSING |', 1), encoding='utf-8')
            self.assertIn('Readable route order does not match configuration', validate(copied)['errors'])
            path.write_text(original, encoding='utf-8')
            path = copied / 'system/router.json'
            cfg = json.loads(path.read_text(encoding='utf-8'))
            next(rule for rule in cfg['routes'] if rule['id'] == 'R02')['acknowledgement_only'] = 'yes'
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
            self.assertIn('Invalid boundary acknowledgement contract: R02', validate(copied)['errors'])


if __name__ == '__main__':
    unittest.main()

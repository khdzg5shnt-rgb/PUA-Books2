"""Current content and source retrieval regressions, using invented facts only."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief
from route import select_route
from search_knowledge import search

VERIFIED = {'speaker_verified': True, 'text_legible': True, 'latest_sender': 'other'}
FOCUS = '有自己的安排不等于编造稀缺'


class CurrentContent(unittest.TestCase):
    def test_unrelated_praise_or_banter_keeps_limit_without_repeating_it(self):
        for scope in ['physical', 'romance', 'activity', 'channel']:
            for function, route in [('appreciation', 'R29'), ('banter', 'R24')]:
                with self.subTest(scope=scope, function=function):
                    result = build_brief({'facts': VERIFIED | {
                        'refusal_scope': scope, 'current_scope_relation': 'different',
                        'function': function, 'reciprocity': 'mutual'}})
                    self.assertEqual(result['decision']['route_id'], route)
                    self.assertTrue(result['current_limits'])
                    self.assertNotIn('allow_no_message', result['output_contract'])
        result = build_brief({'facts': VERIFIED | {'boundary_expressed': True,
            'current_scope_relation': 'different', 'function': 'appreciation'}})
        self.assertEqual(result['decision']['route_id'], 'R29')
        self.assertTrue(any('话题或称呼' in item for item in result['current_limits']))

    def test_unknown_or_same_scope_does_not_turn_refusal_into_banter(self):
        for relation in ['unknown', 'same']:
            result = build_brief({'facts': VERIFIED | {'refusal_scope': 'physical',
                'current_scope_relation': relation, 'function': 'banter',
                'reciprocity': 'mutual', 'roleplay_shared': True}})
            self.assertEqual(result['decision']['route_id'], 'R02')
            self.assertEqual(result['output_contract']['max_questions'], 0)
        result = build_brief({'facts': VERIFIED | {'invitation': 'no_alternative',
            'current_scope_relation': 'different', 'function': 'banter',
            'reciprocity': 'mutual', 'goal': 'invite', 'invite_ready': True,
            'user_availability_known': True, 'activity_verified': True}})
        self.assertEqual(result['decision']['route_id'], 'R24')
        self.assertTrue(result['intent_adjustments'])
        self.assertTrue(any('不换日期追问' in x for x in result['current_limits']))

    def test_separate_actual_arrangement_does_not_reopen_refused_activity(self):
        for invitation, route in [('accepted', 'R09'), ('alternative', 'R08'),
                                  ('cancelled_with_repair', 'R08')]:
            with self.subTest(invitation=invitation):
                result = build_brief({'facts': VERIFIED | {'refusal_scope': 'activity',
                    'current_scope_relation': 'different', 'invitation': invitation,
                    'function': 'logistics'}})
                self.assertEqual(result['decision']['route_id'], route)
                self.assertTrue(any('被拒绝的活动' in x for x in result['current_limits']))
        result = build_brief({'facts': VERIFIED | {'refusal_scope': 'activity',
            'current_scope_relation': 'different', 'invitation': 'accepted',
            'function': 'logistics'}, 'candidate': '那就按刚说的安排。'})
        self.assertTrue(result['candidate_check']['ok'])

    def test_ambiguous_conflicting_arrangement_checks_one_relevant_fact(self):
        for relation in ['unknown', 'same']:
            for invitation in ['accepted', 'alternative', 'cancelled_with_repair', 'open_to_activity']:
                with self.subTest(relation=relation, invitation=invitation):
                    facts = VERIFIED | {'refusal_scope': 'activity',
                        'current_scope_relation': relation, 'invitation': invitation,
                        'function': 'logistics', 'invite_ready': True,
                        'user_availability_known': True, 'activity_verified': True}
                    result = build_brief({'facts': facts, 'candidate': '已经给你订好了。'})
                    self.assertEqual(result['decision']['route_id'], 'R00S')
                    self.assertEqual(result['clarification']['field'], 'current_scope_relation')
                    self.assertEqual(result['clarification']['question'].count('？'), 1)
                    self.assertFalse(result['candidate_check']['ok'])
        result = build_brief({'facts': VERIFIED | {'refusal_scope': 'activity',
            'invitation': 'accepted', 'function': 'question'}})
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertNotIn('clarification', result)

    def test_waiting_and_contact_stop_still_take_priority_over_new_scope(self):
        facts = VERIFIED | {'current_scope_relation': 'different', 'function': 'banter',
                            'reciprocity': 'mutual'}
        result = build_brief({'facts': facts | {'refusal_scope': 'contact'}, 'focus': FOCUS})
        self.assertEqual(result['decision']['action'], 'stop')
        self.assertEqual(result['retrieval']['mode'], 'preferred')
        facts.update(latest_sender='user', refusal_scope='activity', invitation='accepted')
        result = build_brief({'facts': facts})
        self.assertEqual(result['decision']['route_id'], 'R04')
        self.assertNotIn('clarification', result)
        result = build_brief({'facts': facts | {'necessary_new_logistics': True}})
        self.assertEqual(result['decision']['route_id'], 'R04N')

    def test_fresh_mutual_banter_clears_stale_low_count_but_not_history(self):
        facts = VERIFIED | {'function': 'banter', 'reciprocity': 'mutual',
                            'current_turn_low': True, 'consecutive_low_rounds': 3}
        original = dict(facts)
        result = build_brief({'facts': facts})
        self.assertEqual(result['decision']['route_id'], 'R24')
        self.assertEqual(set(result['fact_adjustments']), {'current_turn_low', 'consecutive_low_rounds'})
        self.assertEqual(facts, original)
        facts['reciprocity'] = 'unknown'
        self.assertEqual(build_brief({'facts': facts})['decision']['route_id'], 'R14')

    def test_clarification_goes_to_user_and_never_becomes_a_message_to_other(self):
        for facts in [{}, VERIFIED | {'goal': 'invite'}, VERIFIED | {
                'refusal_scope': 'activity', 'invitation': 'accepted', 'function': 'logistics'}]:
            with self.subTest(facts=facts):
                result = build_brief({'facts': facts})
                self.assertEqual(result['decision']['action'], 'clarify')
                self.assertEqual(result['clarification']['recipient'], 'user')
                self.assertEqual(result['output_contract']['recipient'], 'user')
                self.assertEqual(result['output_contract']['max_candidates'], 0)
                self.assertIn('只向用户', select_route(facts)['output_policy'])
        request = {'facts': VERIFIED | {'function': 'question'}}
        self.assertEqual(build_brief(request)['output_contract']['recipient'], 'other')
        self.assertEqual(build_brief(request, task='meaning')['output_contract']['recipient'], 'user')


class FocusedRetrieval(unittest.TestCase):
    def test_method_with_content_query_prefers_matching_cited_section(self):
        for query, method in [(FOCUS, 'M25'), ('M25 ' + FOCUS, None)]:
            hit = search(query, method=method, limit=1)[0]
            self.assertEqual(hit['path'], 'knowledge/books/B025-intent-and-follow-up.md')
            self.assertEqual(hit['heading'], FOCUS)
            self.assertTrue(hit['query_matched'])
            self.assertEqual(hit['match_kind'], 'cited_source_section')
            self.assertIn('M25', hit['source_method_ids'])
            self.assertEqual(hit['method_ids'], [])
        hit = search(FOCUS, limit=1)[0]
        self.assertIn('M25', hit['source_method_ids'])
        preferred = search('', method='M25', limit=1)[0]
        self.assertEqual(preferred['method_ids'], ['M25'])
        self.assertEqual(preferred['match_kind'], 'preferred_section')

    def test_focus_changes_only_one_source_and_never_the_method_or_output_task(self):
        request = {'facts': VERIFIED | {'function': 'opening'}}
        regular = build_brief(request)
        result = build_brief(request | {'focus': FOCUS})
        self.assertEqual(result['decision'], regular['decision'])
        self.assertEqual(result['primary_method'], regular['primary_method'])
        self.assertEqual(result['read_next']['heading'], FOCUS)
        self.assertTrue(result['read_next']['excerpt_complete'])
        self.assertEqual(len(result['read']), 2)
        self.assertEqual(result['retrieval']['mode'], 'focused_cited_source')
        self.assertNotIn('focus', result)
        fallback = build_brief(request | {'focus': 'SYNTHETIC_NO_SUCH_TOPIC_X31'})
        self.assertEqual(fallback['read_next'], regular['read_next'])
        self.assertEqual(fallback['retrieval']['mode'], 'preferred')
        for task in ['meaning', 'analysis', 'review', 'training']:
            focused = build_brief(request | {'task': task, 'focus': FOCUS})
            self.assertEqual(focused['task'], task)
            self.assertEqual(focused['decision'], regular['decision'])

    def test_focus_and_scope_inputs_are_validated_without_echoing_content(self):
        command = [sys.executable, str(ROOT / 'scripts/coach.py'), '--request', '-']
        for value in [None, [], 42, 'SYNTHETIC_PRIVATE_MARKER' * 20]:
            result = subprocess.run(command, input=json.dumps({'facts': VERIFIED, 'focus': value}),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('SYNTHETIC_PRIVATE_MARKER', result.stderr + result.stdout)
            self.assertNotIn('Traceback', result.stderr)
        with self.assertRaises(ValueError):
            build_brief({'facts': VERIFIED | {'current_scope_relation': 'LIKES_ME'}})


if __name__ == '__main__':
    unittest.main()

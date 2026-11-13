"""Action-relevant input checks and current requests, using invented metadata only."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief

VERIFIED = {'speaker_verified': True, 'text_legible': True,
            'latest_sender': 'other'}


def brief(**facts):
    return build_brief({'facts': VERIFIED | facts})


class ResponsePriorities(unittest.TestCase):
    def test_verified_pending_reply_does_not_need_an_unreadable_body(self):
        for direction in [{'latest_sender': 'user'},
                          {'latest_sender': 'user', 'turn_gap': 'order'},
                          {'latest_sender': 'unknown', 'pending_reply': True}]:
            with self.subTest(direction=direction):
                result = brief(text_legible=False, **direction)
                self.assertEqual(result['decision']['route_id'], 'R04')
                self.assertNotIn('clarification', result)
                self.assertEqual(result['output_contract']['max_candidates'], 0)
                self.assertTrue(result['intent_adjustments'])

    def test_all_possible_screen_tails_outgoing_can_wait_without_text(self):
        views = [[[{'id': 1, 'sender': 'user'}]],
                 [[{'id': 1, 'sender': 'user'}], [{'id': 2, 'sender': 'user'}]]]
        for screens in views:
            result = brief(text_legible=False, screens=screens)
            self.assertEqual(result['decision']['route_id'], 'R04')
            self.assertNotIn('clarification', result)

    def test_empty_verified_first_opening_does_not_ask_for_a_nonexistent_message(self):
        request = {'facts': VERIFIED | {'latest_sender': 'none', 'function': 'opening',
                                       'text_legible': False}}
        original = copy.deepcopy(request)
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R25')
        self.assertNotIn('clarification', result)
        self.assertEqual(result['output_contract']['max_candidates'], 1)
        self.assertEqual(request, original)
        self.assertNotIn('text_legible', result['fact_adjustments'])

    def test_incoming_or_unverified_input_still_requires_relevant_checks(self):
        for extra in [{}, {'latest_sender': 'unknown'},
                      {'latest_sender': 'user', 'speaker_verified': False},
                      {'latest_sender': 'user', 'necessary_new_logistics': True},
                      {'latest_sender': 'none', 'function': 'opening', 'turn_gap': 'missing'}]:
            with self.subTest(extra=extra):
                result = brief(text_legible=False, **extra)
                self.assertEqual(result['decision']['action'], 'clarify')
                self.assertEqual(result['clarification']['recipient'], 'user')
                self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_interpretation_tasks_still_need_the_message_they_are_interpreting(self):
        for task in ['meaning', 'analysis', 'review', 'training']:
            for direction in ['user', 'other', 'none']:
                with self.subTest(task=task, direction=direction):
                    result = build_brief({'task': task, 'facts': VERIFIED | {
                        'latest_sender': direction, 'text_legible': False}})
                    self.assertEqual(result['decision']['action'], 'clarify')
                    self.assertEqual(result['clarification']['field'], 'text_legible')

    def test_clarified_contact_stop_does_not_require_the_unreadable_tail(self):
        result = brief(text_legible=False, refusal_scope='contact')
        self.assertEqual(result['decision']['route_id'], 'R01')
        self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_explicit_help_is_not_replaced_by_a_repair_only_response(self):
        for request in [{'function': 'advice_request'}, {'advice_requested': True},
                        {'urgent_practical_need': True}]:
            with self.subTest(request=request):
                result = brief(repair_needed=True, **request)
                self.assertEqual(result['decision']['route_id'], 'R16')
                self.assertEqual(result['primary_method']['id'], 'M13')
                self.assertTrue(any('责任' in x for x in result['current_limits']))
                self.assertEqual(result['output_contract']['max_candidates'], 1)

    def test_correction_plus_help_uses_corrected_facts_and_answers_the_request(self):
        for request in [{'advice_requested': True}, {'urgent_practical_need': True}]:
            result = brief(function='correction', **request)
            self.assertEqual(result['decision']['route_id'], 'R16')
            self.assertTrue(any('更正后的事实' in x for x in result['current_limits']))
        result = brief(function='correction', repair_needed=True, advice_requested=True)
        self.assertEqual(len(result['current_limits']), 2)

    def test_plain_repair_correction_and_questions_keep_their_original_routes(self):
        for facts, expected in [({'repair_needed': True}, 'R07'),
                                ({'function': 'correction'}, 'R12'),
                                ({'function': 'question'}, 'R18'),
                                ({'function': 'distress'}, 'R15')]:
            self.assertEqual(brief(**facts)['decision']['route_id'], expected)

    def test_current_screen_request_keeps_arrangement_and_refusal_limits(self):
        facts = VERIFIED | {'repair_needed': True, 'refusal_scope': 'physical',
            'invitation': 'settled', 'screens': [[
                {'id': 8, 'sender': 'user'}, {'id': 3, 'sender': 'other',
                 'facts': {'function': 'correction', 'advice_requested': True,
                           'invitation': 'cancelled_without_repair'}}]]}
        original = copy.deepcopy(facts)
        result = build_brief({'facts': facts})
        self.assertEqual(result['decision']['route_id'], 'R16')
        for word in ['身体', '没有替代安排', '责任', '更正后的事实']:
            self.assertTrue(any(word in x for x in result['current_limits']))
        self.assertEqual(result['screen_window']['plan_update']['bubble_ids'], [3])
        self.assertEqual(facts, original)

    def test_help_never_bypasses_waiting_stop_or_an_actual_input_gap(self):
        for changed, expected in [({'latest_sender': 'user'}, 'hold'),
                                  ({'refusal_scope': 'contact'}, 'stop'),
                                  ({'speaker_verified': False}, 'clarify'),
                                  ({'turn_gap': 'missing'}, 'clarify')]:
            result = brief(function='advice_request', repair_needed=True, **changed)
            self.assertEqual(result['decision']['action'], expected)
            self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_case_selection_and_candidate_check_do_not_leak_or_add_a_message(self):
        request = {'cases': {'selected': VERIFIED | {'latest_sender': 'user',
            'text_legible': False}, 'other': VERIFIED | {'refusal_scope': 'contact'}},
            'case_key': 'selected', 'candidate': 'SYNTHETIC_DRAFT_NOT_TO_BE_ECHOED'}
        original = copy.deepcopy(request)
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R04')
        self.assertFalse(result['candidate_check']['ok'])
        self.assertEqual(result['current_limits'], [])
        self.assertNotIn(request['candidate'], json.dumps(result))
        self.assertEqual(request, original)


if __name__ == '__main__':
    unittest.main()

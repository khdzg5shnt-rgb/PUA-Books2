"""Fictional metadata: current help, later solutions and one response stay aligned."""
import copy
import json
import subprocess
import sys
import unittest
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from coach import build_brief

VERIFIED = {'speaker_verified': True, 'text_legible': True}


def bubble(ident, sender='other', resolves=None, **facts):
    result = {'id': ident, 'sender': sender, 'facts': facts}
    if resolves is not None:
        result['resolves'] = resolves
    return result


def brief(screens, **facts):
    return build_brief({'facts': VERIFIED | {'screens': screens} | facts})


class CurrentRequestResolution(unittest.TestCase):
    def test_help_before_an_ordinary_question_remains_the_one_main_method(self):
        for help_fact in [{'function': 'advice_request'}, {'advice_requested': True},
                          {'urgent_practical_need': True}]:
            with self.subTest(help_fact=help_fact):
                result = brief([[bubble(7, **help_fact), bubble(2, function='question')]])
                self.assertEqual(result['decision']['route_id'], 'R16')
                self.assertEqual(result['screen_window']['last_id'], 2)
                self.assertEqual(result['screen_window']['reply_to_id'], 7)
                self.assertEqual(result['turn_coverage']['additional_request_ids'], [2])
                self.assertEqual(result['output_contract']['max_candidates'], 1)
                self.assertEqual(result['output_contract']['max_questions'], 1)

    def test_a_single_urgent_request_precedes_other_current_help(self):
        screens = [[bubble(1, function='advice_request'),
                    bubble(2, urgent_practical_need=True), bubble(3, function='question')]]
        result = brief(screens)
        self.assertEqual(result['screen_window']['reply_to_id'], 2)
        self.assertEqual(result['turn_coverage']['additional_request_ids'], [1, 3])
        # Competing same-priority requests need the reader's actual content choice.
        screens[0][0]['facts']['urgent_practical_need'] = True
        result = brief(screens)
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertEqual(result['screen_window']['turn_gap'], 'content')
        self.assertEqual(brief(screens, reply_to_id=1)['decision']['route_id'], 'R16')

    def test_explicit_focus_does_not_hide_unresolved_help(self):
        screens = [[bubble(1, function='advice_request'), bubble(2, function='question')]]
        result = brief(screens, reply_to_id=2)
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertEqual(result['output_contract']['max_candidates'], 0)
        self.assertEqual(brief(screens, reply_to_id=1)['decision']['route_id'], 'R16')

    def test_verified_solution_can_end_the_turn_without_a_new_message(self):
        screens = [[bubble(9, function='advice_request'),
                    bubble(3, resolves=[9], function='closing')]]
        request = {'facts': VERIFIED | {'screens': screens}}
        original = copy.deepcopy(request)
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R13C')
        self.assertEqual(result['output_contract']['max_candidates'], 0)
        self.assertEqual(result['screen_window']['request_resolutions'],
                         [{'request_id': 9, 'resolved_by_ids': [3]}])
        self.assertTrue(result['screen_window']['current_turn_content'][0]['request_resolved'])
        self.assertTrue(result['screen_window']['current_turn_content'][0]['request_marked'])
        self.assertEqual(request, original)

    def test_resolved_help_does_not_override_a_new_question(self):
        screens = [[bubble(1, function='advice_request'),
                    bubble(2, resolves=[1], function='question')]]
        result = brief(screens, goal='invite')
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['screen_window']['reply_to_id'], 2)
        self.assertEqual(result['turn_coverage']['additional_request_ids'], [])
        self.assertEqual(result['output_contract']['recipient'], 'other')
        with self.assertRaises(ValueError):
            brief(screens, reply_to_id=1)

    def test_resolving_one_request_keeps_other_requests_and_new_help(self):
        screens = [[bubble(1, function='question'), bubble(2, function='advice_request'),
                    bubble(3, resolves=[2], function='sharing'), bubble(4, function='question')]]
        result = brief(screens)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['turn_coverage']['additional_request_ids'], [1])
        screens[0][-1]['facts'] = {'function': 'advice_request'}
        result = brief(screens)
        self.assertEqual(result['decision']['route_id'], 'R16')
        self.assertEqual(result['screen_window']['reply_to_id'], 4)
        self.assertEqual(result['turn_coverage']['additional_request_ids'], [1])

    def test_unverified_resolution_order_is_not_inferred_from_upload_or_ids(self):
        target = bubble(9, function='advice_request')
        solution = bubble(4, resolves=[9], function='sharing')
        tail = bubble(2, function='closing')
        for views in permutations([[target, tail], [solution, tail]]):
            result = brief(list(views))
            self.assertEqual(result['decision']['route_id'], 'R00T')
            self.assertEqual(result['screen_window']['request_gap'], 'order')
            self.assertEqual(result['clarification']['field'], 'request_resolution')
            self.assertEqual(result['clarification']['recipient'], 'user')
            self.assertNotIn('request_resolutions', result['screen_window'])
            result = brief(list(views), screen_links=[[9, 4]])
            self.assertEqual(result['decision']['route_id'], 'R13C')

    def test_an_unordered_user_barrier_needs_one_turn_check(self):
        target = bubble(9, function='question')
        solution = bubble(2, resolves=[9], function='closing')
        views = [[target, solution], [bubble(4, 'user'), solution]]
        for order in permutations(views):
            result = brief(list(order))
            self.assertEqual(result['decision']['route_id'], 'R00T')
            self.assertEqual(result['screen_window']['request_gap'], 'turn')
            self.assertEqual(result['clarification']['field'], 'request_resolution')
            result = brief(list(order), screen_links=[[4, 9]])
            self.assertEqual(result['decision']['route_id'], 'R13C')

    def test_resolutions_cannot_jump_across_a_sent_user_reply(self):
        with self.assertRaises(ValueError):
            brief([[bubble(1, function='question'), bubble(2, 'user'),
                    bubble(3, resolves=[1], function='closing')]])
        result = brief([[bubble(1, function='question'),
                         bubble(2, resolves=[1], function='closing'), bubble(3, 'user'),
                         bubble(4, function='advice_request'), bubble(5, function='question')]])
        self.assertEqual(result['decision']['route_id'], 'R16')
        self.assertEqual(result['screen_window']['reply_to_id'], 4)
        self.assertNotIn('request_resolutions', result['screen_window'])

    def test_overlapping_solution_annotations_do_not_resolve_twice(self):
        a = bubble(1, function='question')
        b = bubble(2, function='question')
        done = bubble(3, resolves=[1, 2], function='closing')
        result = brief([[a, b, done], [b, done]])
        self.assertEqual(result['decision']['route_id'], 'R13C')
        self.assertEqual(result['screen_window']['request_resolutions'],
                         [{'request_id': 1, 'resolved_by_ids': [3]},
                          {'request_id': 2, 'resolved_by_ids': [3]}])
        with self.assertRaises(ValueError):
            brief([[a, b, done], [b, bubble(3, resolves=[2], function='closing')]])

    def test_resolving_a_question_does_not_clear_a_cancellation_or_boundary(self):
        screens = [[bubble(1, function='question', invitation='cancelled_without_repair'),
                    bubble(2, resolves=[1], function='sharing'), bubble(3, function='question')]]
        result = brief(screens, invitation='settled', refusal_scope='physical')
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['screen_window']['plan_update']['invitation'], 'cancelled_without_repair')
        self.assertTrue(any('没有替代安排' in x for x in result['current_limits']))
        self.assertTrue(any('身体' in x for x in result['current_limits']))
        self.assertFalse(any('双方已确认' in x for x in result['current_limits']))

    def test_contact_stop_waiting_and_cropped_tail_keep_priority(self):
        screens = [[bubble(1, function='question'), bubble(2, resolves=[1], function='question')]]
        self.assertEqual(brief(screens, refusal_scope='contact')['decision']['route_id'], 'R01')
        result = brief([screens[0]+[bubble(3, 'user')]])
        self.assertEqual(result['decision']['route_id'], 'R04')
        result = brief(screens, turn_gap='missing')
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertEqual(result['screen_window']['current_turn_content'], [])
        self.assertNotIn('request_resolutions', result['screen_window'])

    def test_selected_case_and_all_five_task_contracts_remain_independent(self):
        screens = [[bubble(1, function='advice_request'), bubble(2, function='question')]]
        for task in ['reply', 'meaning', 'analysis', 'review', 'training']:
            request = {'task': task, 'case_key': 'current', 'cases': {
                'unused': VERIFIED | {'refusal_scope': 'contact', 'screens': [
                    [bubble(1, function='question'), bubble(2, resolves=[1], function='closing')]]},
                'current': VERIFIED | {'screens': screens}}}
            result = build_brief(request)
            self.assertEqual(result['decision']['route_id'], 'R16')
            self.assertNotIn('request_resolutions', result['screen_window'])
            self.assertEqual(result['output_contract']['recipient'], 'other' if task == 'reply' else 'user')
            self.assertNotIn('unused', json.dumps(result))

    def test_invalid_resolution_metadata_and_reversed_order_are_rejected(self):
        for invalid in [None, [], '1', [True], [0], [-1], [1, 1], [2], [99]]:
            with self.subTest(invalid=invalid):
                done = bubble(2, function='closing');done['resolves'] = invalid
                with self.assertRaises(ValueError):
                    brief([[bubble(1, function='question'), done]])
        for sender in ['user', 'unknown']:
            with self.assertRaises(ValueError):
                brief([[bubble(1, function='question'), bubble(2, sender, resolves=[1])]])
        with self.assertRaises(ValueError):
            brief([[bubble(1, function='sharing'), bubble(2, resolves=[1])]])
        with self.assertRaises(ValueError):
            brief([[bubble(2, resolves=[1]), bubble(1, function='question')]])

    def test_cli_success_and_errors_do_not_echo_drafts_or_raw_input(self):
        command = [sys.executable, str(ROOT/'scripts/coach.py'), '--request', '-']
        request = {'facts': VERIFIED | {'screens': [[bubble(1, function='question'),
                   bubble(2, resolves=[1], function='closing')]]},
                   'candidate': 'SYNTHETIC_PRIVATE_DRAFT'}
        result = subprocess.run(command, input=json.dumps(request), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['candidate_check']['ok'])
        self.assertNotIn('SYNTHETIC_PRIVATE_DRAFT', result.stdout+result.stderr)
        request['facts']['screens'][0][1]['resolves'] = ['SYNTHETIC_PRIVATE_MARKER']
        result = subprocess.run(command, input=json.dumps(request), text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
        self.assertNotIn('SYNTHETIC_PRIVATE_MARKER', result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()

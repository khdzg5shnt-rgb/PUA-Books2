"""Synthetic current-turn functions: a light tail cannot erase real content."""
import copy
import json
import subprocess
import sys
import unittest
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief

VERIFIED = {'speaker_verified': True, 'text_legible': True}
SUBSTANTIVE_ROUTES = {'distress': 'R15', 'good_news': 'R17', 'correction': 'R12'}


def bubble(ident, sender='other', **facts):
    return {'id': ident, 'sender': sender, 'facts': facts}


def brief(screens, **facts):
    return build_brief({'facts': VERIFIED | {'screens': screens} | facts})


class SubstantiveTail(unittest.TestCase):
    def test_light_tail_needs_content_selection_after_substantive_content(self):
        for function in SUBSTANTIVE_ROUTES:
            for tail in ['unknown', 'banter', 'opening', 'closing']:
                with self.subTest(function=function, tail=tail):
                    result = brief([[bubble(1, 'user'), bubble(2, function=function),
                                     bubble(3, function=tail, roleplay_shared=True)]],
                                   reciprocity='mutual', goal='invite', invite_ready=True,
                                   user_availability_known=True, activity_verified=True)
                    self.assertEqual(result['decision']['route_id'], 'R00T')
                    self.assertEqual(result['screen_window']['last_id'], 3)
                    self.assertEqual(result['screen_window']['turn_gap'], 'content')
                    self.assertIsNone(result['screen_window']['reply_to_id'])
                    self.assertEqual(result['output_contract']['max_candidates'], 0)
                    self.assertEqual(result['clarification']['recipient'], 'user')

    def test_verified_main_content_keeps_the_existing_method(self):
        for function, route in SUBSTANTIVE_ROUTES.items():
            result = brief(
                [[bubble(9, function=function),
                  bubble(3, function='banter', roleplay_shared=True)]],
                reply_to_id=9, reciprocity='mutual', goal='invite', invite_ready=True,
                user_availability_known=True, activity_verified=True)
            self.assertEqual(result['decision']['route_id'], route)
            self.assertEqual(result['screen_window']['last_id'], 3)
            self.assertEqual(result['screen_window']['reply_to_id'], 9)
            self.assertEqual(result['turn_coverage']['context_ids'], [3])
            self.assertEqual(result['output_contract']['max_candidates'], 1)

    def test_verified_later_closure_or_topic_change_is_still_allowed(self):
        for function in SUBSTANTIVE_ROUTES:
            for tail, route in [('closing', 'R13C'), ('sharing', 'R27'),
                                ('banter', 'R24')]:
                result = brief([[bubble(1, function=function), bubble(2, function=tail)]],
                               reply_to_id=2, reciprocity='mutual')
                self.assertEqual(result['decision']['route_id'], route)
                self.assertEqual(result['screen_window']['reply_to_id'], 2)
                self.assertNotIn('request_resolutions', result['screen_window'])

    def test_old_turn_content_does_not_block_the_current_light_reply(self):
        for function in SUBSTANTIVE_ROUTES:
            result = brief([[bubble(1, function=function), bubble(2, 'user'),
                             bubble(3, function='banter')]], reciprocity='mutual')
            self.assertEqual(result['decision']['route_id'], 'R24')
            self.assertEqual(result['screen_window']['current_turn_ids'], [3])

    def test_upload_order_and_nonchronological_ids_do_not_choose_content(self):
        first, middle, last = (bubble(8, 'user'), bubble(9, function='distress'),
                               bubble(2, function='banter'))
        for screens in permutations([[first, middle], [middle, last]]):
            result = brief(list(screens), reciprocity='mutual')
            self.assertEqual(result['decision']['route_id'], 'R00T')
            self.assertEqual(result['screen_window']['turn_gap'], 'content')
            result = brief(list(screens), reply_to_id=9, reciprocity='mutual')
            self.assertEqual(result['decision']['route_id'], 'R15')

    def test_uncertain_user_barrier_requires_order_before_content_selection(self):
        for function in SUBSTANTIVE_ROUTES:
            content, last = bubble(9, function=function), bubble(2, function='banter')
            for screens in permutations([[content, last], [bubble(4, 'user'), last]]):
                result = brief(list(screens), reciprocity='mutual')
                self.assertEqual(result['screen_window']['turn_gap'], 'order')
                result = brief(list(screens), screen_links=[[4, 9]], reciprocity='mutual')
                self.assertEqual(result['screen_window']['turn_gap'], 'content')
                result = brief(list(screens), screen_links=[[9, 4]], reciprocity='mutual')
                self.assertEqual(result['decision']['route_id'], 'R24')

    def test_flat_input_single_bubbles_and_nonlight_new_content_are_unchanged(self):
        for function, route in SUBSTANTIVE_ROUTES.items():
            self.assertEqual(brief([[bubble(1, function=function)]])['decision']['route_id'], route)
            result = build_brief({'facts': VERIFIED | {'latest_sender': 'other',
                                                       'function': function}})
            self.assertEqual(result['decision']['route_id'], route)
        for tail, route in [('banter', 'R24'), ('closing', 'R13C')]:
            self.assertEqual(brief([[bubble(1, function=tail)]], reciprocity='mutual')
                             ['decision']['route_id'], route)
        for tail, route in [('question', 'R18'), ('advice_request', 'R16'),
                            ('sharing', 'R27'), ('appreciation', 'R29')]:
            self.assertEqual(brief([[bubble(1, function='distress'),
                                     bubble(2, function=tail)]])['decision']['route_id'], route)

    def test_explicit_help_retains_priority_and_only_one_reply_is_allowed(self):
        screens = [[bubble(1, function='distress'), bubble(2, function='advice_request'),
                    bubble(3, function='question')]]
        result = brief(screens)
        self.assertEqual(result['decision']['route_id'], 'R16')
        self.assertEqual(result['screen_window']['reply_to_id'], 2)
        self.assertEqual(result['turn_coverage']['additional_request_ids'], [3])
        self.assertEqual(result['output_contract']['max_candidates'], 1)
        self.assertEqual(brief(screens, reply_to_id=1)['decision']['route_id'], 'R00T')

    def test_wait_contact_stop_and_arrangement_updates_keep_priority(self):
        screens = [[bubble(1, function='distress'),
                    bubble(2, function='closing', invitation='cancelled_without_repair')]]
        self.assertEqual(brief(screens, refusal_scope='contact')['decision']['route_id'], 'R01')
        result = brief(screens, invitation='settled')
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertEqual(result['screen_window']['plan_update']['invitation'],
                         'cancelled_without_repair')
        self.assertTrue(any('没有替代安排' in item for item in result['current_limits']))
        screens[0].append(bubble(3, 'user'))
        self.assertEqual(brief(screens)['decision']['route_id'], 'R04')
        self.assertEqual(brief(screens, necessary_new_logistics=True)['decision']['route_id'], 'R04N')

    def test_task_case_revision_and_input_data_stay_separate(self):
        for task in ['reply', 'meaning', 'analysis', 'review', 'training']:
            request = {'task': task, 'case_key': 'current', 'cases': {
                'unused': VERIFIED | {'latest_sender': 'other', 'refusal_scope': 'contact'},
                'current': VERIFIED | {'screens': [[bubble(1, function='good_news'),
                                                   bubble(2, function='banter')]]}}}
            original = copy.deepcopy(request)
            result = build_brief(request)
            self.assertEqual(result['decision']['route_id'], 'R00T')
            self.assertEqual(request, original)
            self.assertNotIn('unused', json.dumps(result))
        request = {'facts': VERIFIED | {'screens': [[bubble(1, function='good_news'),
                                                   bubble(2, function='banter')]]},
                   'revision': {'draft_state': 'unsent', 'requested': ['no_teasing'],
                                'turn_anchor': {'last_id': 2, 'reply_to_id': 1}}}
        self.assertFalse(build_brief(request)['draft_revision']['applied'])
        request['facts']['reply_to_id'] = 1
        self.assertTrue(build_brief(request)['draft_revision']['applied'])

    def test_cli_does_not_echo_candidate_while_content_is_unresolved(self):
        request = {'facts': VERIFIED | {'screens': [[bubble(1, function='distress'),
                                                   bubble(2, function='banter')]]},
                   'candidate': 'SYNTHETIC_PRIVATE_DRAFT'}
        run = subprocess.run([sys.executable, str(ROOT / 'scripts/coach.py'), '--request', '-'],
                             input=json.dumps(request), text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertFalse(result['candidate_check']['ok'])
        self.assertNotIn('SYNTHETIC_PRIVATE_DRAFT', run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()

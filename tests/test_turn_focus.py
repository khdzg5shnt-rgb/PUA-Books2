"""Verified content selection within one synthetic incoming message turn."""
import json
import sys
import unittest
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief
from route import select_route
from screen_window import resolve_screens

VERIFIED = {'speaker_verified': True, 'text_legible': True}


def bubble(ident, sender='other', **facts):
    return {'id': ident, 'sender': sender, 'facts': facts}


def brief(screens, **facts):
    return build_brief({'facts': VERIFIED | {'screens': screens} | facts})


class TurnFocus(unittest.TestCase):
    def test_later_background_or_closure_does_not_discard_a_pending_request(self):
        requests = [{'function': 'question'}, {'function': 'advice_request'},
                    {'advice_requested': True}, {'urgent_practical_need': True}]
        for request in requests:
            for tail in ['sharing', 'closing', 'correction', 'unknown']:
                with self.subTest(request=request, tail=tail):
                    screens = [[bubble(1, 'user'), bubble(2, **request),
                                bubble(3, function=tail)]]
                    result = brief(screens)
                    self.assertEqual(result['decision']['route_id'], 'R00T')
                    self.assertEqual(result['screen_window']['turn_gap'], 'content')
                    self.assertEqual(result['screen_window']['last_id'], 3)
                    self.assertEqual(result['screen_window']['current_turn_ids'], [2, 3])
                    self.assertIsNone(result['screen_window']['reply_to_id'])
                    self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_explicit_focus_selects_one_bubble_without_merging_its_neighbors(self):
        config = json.loads((ROOT / 'system/router.json').read_text())
        screens = [[bubble(1, 'user'), bubble(2, function='question'),
                    bubble(3, function='sharing', current_turn_low=True,
                           roleplay_shared=True, current_scope_relation='different')]]
        current, window = resolve_screens(screens, config, [], reply_to_id=2)
        self.assertEqual(current, {'function': 'question', 'latest_sender': 'other',
                                   'pending_reply': False, 'turn_gap': 'none'})
        self.assertEqual(window['last_id'], 3)
        self.assertEqual(window['reply_to_id'], 2)
        self.assertEqual(brief(screens, reply_to_id=2)['decision']['route_id'], 'R18')

    def test_verified_withdrawal_or_correction_can_explicitly_choose_the_tail(self):
        for tail, route in [('sharing', 'R27'), ('closing', 'R13C'), ('correction', 'R12')]:
            result = brief([[bubble(1, function='question'), bubble(2, function=tail)]],
                           reply_to_id=2)
            self.assertEqual(result['decision']['route_id'], route)
            self.assertEqual(result['screen_window']['reply_to_id'], 2)
        result = brief([[bubble(1, function='advice_request'), bubble(2, function='question')]])
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['screen_window']['reply_to_id'], 2)

    def test_old_turn_is_excluded_and_a_sent_user_message_still_requires_waiting(self):
        screens = [[bubble(1, function='question'), bubble(2, 'user'),
                    bubble(3, function='sharing')]]
        result = brief(screens)
        self.assertEqual(result['decision']['route_id'], 'R27')
        self.assertEqual(result['screen_window']['current_turn_ids'], [3])
        with self.assertRaises(ValueError):
            brief(screens, reply_to_id=1)
        result = brief([[bubble(1, function='question'), bubble(2, 'user')]])
        self.assertEqual(result['decision']['route_id'], 'R04')
        self.assertEqual(result['screen_window']['current_turn_ids'], [])
        self.assertIsNone(result['screen_window']['reply_to_id'])
        with self.assertRaises(ValueError):
            brief([[bubble(1), bubble(2, 'user')]], reply_to_id=1)

    def test_upload_order_does_not_choose_a_turn_or_resolve_an_unordered_barrier(self):
        question = bubble(4, function='question')
        last = bubble(2, function='sharing')
        views = [[question, last], [bubble(9, 'user'), last]]
        for upload_order in permutations(views):
            for focus in [{}, {'reply_to_id': 4}]:
                result = brief(list(upload_order), **focus)
                self.assertEqual(result['decision']['route_id'], 'R00T')
                self.assertEqual(result['screen_window']['turn_gap'], 'order')
                self.assertEqual(result['screen_window']['last_id'], 2)
                self.assertEqual(result['screen_window']['current_turn_ids'], [2])
                self.assertIsNone(result['screen_window']['reply_to_id'])
            result = brief(list(upload_order), reply_to_id=4, screen_links=[[9, 4]])
            self.assertEqual(result['decision']['route_id'], 'R18')
            self.assertEqual(result['screen_window']['current_turn_ids'], [4, 2])
        # An unknown sender is a possible outgoing barrier too.
        unknown = [[question, last], [bubble(9, 'unknown'), last]]
        self.assertEqual(brief(unknown, reply_to_id=4)['screen_window']['turn_gap'], 'order')

    def test_overlapping_views_share_ids_without_inheriting_other_cases(self):
        user, question, detail = (bubble(8, 'user'), bubble(3, function='question'),
                                  bubble(5, function='sharing'))
        views = [[user, question], [question, detail]]
        for upload_order in permutations(views):
            request = {'cases': {
                'old': VERIFIED | {'screens': [[bubble(3, 'user')]], 'refusal_scope': 'contact'},
                'current': VERIFIED | {'screens': list(upload_order), 'reply_to_id': 3}},
                'case_key': 'current'}
            result = build_brief(request)
            self.assertEqual(result['decision']['route_id'], 'R18')
            self.assertEqual(result['current_limits'], [])
            self.assertEqual(result['screen_window']['last_id'], 5)
            self.assertEqual(result['screen_window']['current_turn_ids'], [3, 5])
            self.assertEqual(result['screen_window']['reply_to_id'], 3)

    def test_contact_refusal_wins_over_content_gap_and_other_limits_survive_focus(self):
        screens = [[bubble(1, function='question'), bubble(2, function='sharing')]]
        for focus in [{}, {'reply_to_id': 1}]:
            result = brief(screens, refusal_scope='contact', **focus)
            self.assertEqual(result['decision']['route_id'], 'R01')
            self.assertEqual(result['decision']['action'], 'stop')
        result = brief(screens, refusal_scope='physical', reply_to_id=1)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertTrue(any('身体' in limit for limit in result['current_limits']))

    def test_focus_rejects_noncurrent_or_unverified_ids_and_needs_screens(self):
        screens = [[bubble(1, 'user'), bubble(2, 'unknown'), bubble(3)]]
        for ident in [None, True, '3', 0, -1, 9, 1, 2]:
            with self.subTest(ident=ident):
                with self.assertRaises(ValueError):
                    brief(screens, reply_to_id=ident)
        with self.assertRaises(ValueError):
            select_route(VERIFIED | {'reply_to_id': 3})
        result = brief([[bubble(1), bubble(2)]], reply_to_id=1, turn_gap='missing')
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertEqual(result['screen_window']['current_turn_ids'], [])
        self.assertIsNone(result['screen_window']['reply_to_id'])


if __name__ == '__main__':
    unittest.main()

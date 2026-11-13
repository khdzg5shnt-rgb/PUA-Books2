"""Synthetic multi-screen requests and end-of-turn reply contracts."""
import json
import subprocess
import sys
import unittest
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief

VERIFIED = {'speaker_verified': True, 'text_legible': True, 'latest_sender': 'other'}


def bubble(number, sender, **facts):
    return {'id': number, 'sender': sender, 'facts': facts}


def brief(facts, **request):
    return build_brief({'facts': VERIFIED | facts, **request})


class ScreenWindow(unittest.TestCase):
    def test_overlap_resolves_the_same_bubble_in_every_upload_order(self):
        first = bubble(30, 'user')
        middle = bubble(4, 'other', function='sharing')
        last = bubble(2, 'other', function='question')
        views = [[first, middle], [middle, last], [bubble(2, 'unknown'), {'kind': 'draft'}]]
        for order in permutations(views):
            result = brief({'screens': list(order), 'pending_reply': True, 'latest_sender': 'user'})
            self.assertEqual(result['screen_window'], {'last_id': 2, 'latest_sender': 'other',
                                                       'distinct_sent': 3, 'turn_gap': 'none',
                                                       'current_turn_ids': [4, 2], 'reply_to_id': 2,
                                                       'current_turn_content': [
                                                           {'id': 4, 'function': 'sharing',
                                                            'request_marked': False, 'selected_primary': False},
                                                           {'id': 2, 'function': 'question',
                                                            'request_marked': True, 'selected_primary': True}]})
            self.assertEqual(result['decision']['route_id'], 'R18')
            self.assertEqual(set(result['fact_adjustments']), {'latest_sender', 'pending_reply'})
            self.assertEqual(result['output_contract']['recipient'], 'other')

    def test_earlier_same_turn_request_is_not_silently_erased(self):
        old = bubble(1, 'other', function='advice_request', advice_requested=True)
        for last, route in [(bubble(2, 'other'), 'R28'), (bubble(2, 'other', function='closing'), 'R13C')]:
            screens = [[old, {'kind': 'quote'}, last, {'kind': 'notice'}]]
            self.assertEqual(brief({'screens': screens})['decision']['route_id'], 'R00T')
            result = brief({'screens': screens, 'reply_to_id': 2})
            self.assertEqual(result['decision']['route_id'], route)
            self.assertEqual(result['screen_window']['distinct_sent'], 2)
        views = [[bubble(1, 'other'), bubble(2, 'other')], [bubble(9, 'other'), bubble(2, 'other')]]
        self.assertEqual(brief({'screens': views})['screen_window']['last_id'], 2)

    def test_unknown_order_sender_or_no_sent_message_gets_one_user_question(self):
        a, b = bubble(4, 'other'), bubble(7, 'user')
        cases = [
            ([[a], [b]], 'order'), ([[a, b], [b, a]], 'order'),
            ([[a, b], [bubble(4, 'user'), b]], 'order'),
            ([[a], [bubble(4, 'user')]], 'sender'),
            ([[b, bubble(3, 'unknown')]], 'sender'), ([[{'kind': 'draft'}], []], 'missing'),
        ]
        for screens, gap in cases:
            result = brief({'screens': screens, 'pending_reply': True}, candidate='周末见？')
            self.assertEqual(result['decision']['route_id'], 'R00T')
            self.assertEqual(result['screen_window']['turn_gap'], gap)
            self.assertEqual(result['clarification']['recipient'], 'user')
            self.assertEqual(result['clarification']['question'].count('？'), 1)
            self.assertEqual(result['output_contract']['max_candidates'], 0)
            self.assertFalse(result['candidate_check']['ok'])
        result = brief({'screens': [[a], [b]], 'screen_links': [[7, 4]]})
        self.assertEqual(result['screen_window']['last_id'], 4)
        self.assertNotIn('clarification', result)
        cropped = brief({'screens': [[a, b]], 'turn_gap': 'missing'})
        self.assertEqual(cropped['decision']['route_id'], 'R00T')
        self.assertIsNone(cropped['screen_window']['last_id'])

    def test_independent_cases_and_verified_contact_limits(self):
        other, user = bubble(1, 'other', function='sharing'), bubble(1, 'user')
        cases = {'a': VERIFIED | {'screens': [[user]], 'refusal_scope': 'contact'},
                 'b': VERIFIED | {'screens': [[other]]}}
        selected = build_brief({'cases': cases, 'case_key': 'b'})
        self.assertEqual(selected['decision']['route_id'], 'R27')
        self.assertEqual(selected['current_limits'], [])
        self.assertEqual(build_brief({'cases': cases, 'case_key': 'a'})['decision']['action'], 'stop')
        result = brief({'screens': [[user], [bubble(7, 'user')]]})
        self.assertEqual(result['decision']['route_id'], 'R04')
        self.assertNotIn('clarification', result)

    def test_bubble_scope_reaches_the_right_clarification(self):
        screens = [[bubble(4, 'other', function='logistics', current_scope_relation='same')]]
        result = brief({'screens': screens, 'refusal_scope': 'activity', 'invitation': 'accepted'})
        self.assertEqual(result['decision']['route_id'], 'R00S')
        self.assertIn('重新答应', result['clarification']['question'])

    def test_invalid_annotations_do_not_leak_text_through_the_cli(self):
        marker = 'SYNTHETIC_MARKER_DO_NOT_ECHO'
        sent = bubble(1, 'other')
        bad = [
            {'screens': [[sent | {'text': marker}]]},
            {'screens': [[{'kind': 'quote', 'text': marker}]]},
            {'screens': [[bubble(True, 'other')]]},
            {'screens': [[bubble(1, 'other', function=marker)]]},
            {'screens': [[sent]], 'screen_links': [[1, marker]]},
            {'screens': [[sent]], 'function': 'question'},
            {'screens': [[bubble(1, 'other', function='question')], [bubble(1, 'other', function='sharing')]]},
            {'screen_links': [[1, 2]]},
        ]
        for facts in bad:
            run = subprocess.run([sys.executable, str(ROOT/'scripts/coach.py'), '--request', '-'],
                                 input=json.dumps({'facts': VERIFIED | facts}), text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)
            self.assertNotIn(marker, run.stdout + run.stderr)


class EndOfTurn(unittest.TestCase):
    def test_settled_and_mutually_closed_do_not_emit_an_outbound_draft(self):
        for facts in [{'invitation': 'settled', 'function': 'closing'}, {'function': 'closing'}]:
            result = brief(facts, candidate='那再定个时间？')
            self.assertEqual(result['decision']['action'], 'hold')
            self.assertEqual(result['output_contract']['recipient'], 'user')
            self.assertEqual(result['output_contract']['max_candidates'], 0)
            self.assertEqual(result['output_contract']['max_questions'], 0)
            self.assertEqual(result['output_contract']['deliver'], result['user_output'])
            self.assertFalse(result['candidate_check']['ok'])
        self.assertEqual(brief({'invitation': 'accepted', 'function': 'closing'})['decision']['route_id'], 'R09')

    def test_promised_update_and_unscheduled_decline_have_distinct_briefs(self):
        for invitation, route in [('will_update', 'R10W'), ('no_alternative', 'R10')]:
            facts = {'invitation': invitation, 'goal': 'invite'}
            for draft, ok in [('好。', True), ('', True), ('那明天呢？', False)]:
                result = brief(facts, candidate=draft)
                self.assertEqual(result['decision']['route_id'], route)
                self.assertEqual(result['primary_method']['id'], 'M17')
                self.assertEqual(result['read_next']['heading'], '没有替代安排时收住')
                self.assertTrue(result['output_contract']['allow_no_message'])
                self.assertEqual(result['output_contract']['max_questions'], 0)
                self.assertEqual(result['candidate_check']['ok'], ok)
            for task in ('meaning', 'analysis', 'review', 'training'):
                result = brief(facts, task=task)
                self.assertEqual(result['output_contract']['recipient'], 'user')
                self.assertNotIn('allow_no_message', result['output_contract'])
                self.assertNotIn('clarification', result)

    def test_fresh_content_wins_over_old_plans_without_reopening_them(self):
        for plan in ('settled', 'will_update', 'accepted', 'alternative', 'cancelled_with_repair'):
            for function, route in [('question', 'R18'), ('sharing', 'R27'), ('advice_request', 'R16')]:
                result = brief({'invitation': plan, 'function': function, 'goal': 'invite'})
                self.assertEqual(result['decision']['route_id'], route)
                self.assertEqual(result['output_contract']['max_candidates'], 1)
                self.assertNotIn('clarification', result)
        same = {'invitation': 'settled', 'refusal_scope': 'activity',
                'current_scope_relation': 'same', 'function': 'logistics'}
        self.assertEqual(brief(same)['decision']['route_id'], 'R00S')
        self.assertFalse(any('双方已确认' in line for line in brief(same)['current_limits']))
        stopped = brief(same | {'refusal_scope': 'contact'})
        self.assertEqual(len(stopped['current_limits']), 1)


if __name__ == '__main__':
    unittest.main()

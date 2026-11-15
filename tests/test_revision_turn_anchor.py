"""Draft-only style feedback stays with the verified sent-message context."""
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


def sent(ident, sender='other', **facts):
    return {'id': ident, 'sender': sender, 'facts': facts}


def revision(last=2, primary=2):
    return {'draft_state': 'unsent', 'requested': ['no_question', 'no_teasing'],
            'turn_anchor': {'last_id': last, 'reply_to_id': primary}}


def request(screens, **facts):
    return {'facts': VERIFIED | {'screens': screens} | facts, 'revision': revision()}


class RevisionTurnAnchor(unittest.TestCase):
    def test_same_message_applies_style_without_mutating_facts_or_action(self):
        value = request([[sent(1, 'user'), sent(2, function='question')]])
        value['candidate'] = '再问一句？'
        original = copy.deepcopy(value)
        base = build_brief({'facts': value['facts']})
        result = build_brief(value)
        self.assertEqual(value, original)
        self.assertEqual(result['decision'], base['decision'])
        self.assertEqual(result['primary_method'], base['primary_method'])
        self.assertTrue(result['draft_revision']['applied'])
        self.assertEqual(result['draft_revision']['anchor_status'], 'matched')
        self.assertEqual(result['output_contract']['max_questions'], 0)
        self.assertIn('这一条不用调侃、曲解或角色玩笑',
                      result['output_contract']['expression_instructions'])
        self.assertFalse(result['candidate_check']['ok'])

    def test_new_incoming_message_does_not_inherit_old_draft_only_constraints(self):
        value = request([[sent(1, 'user'), sent(2, function='question'),
                          sent(3, function='question')]])
        value['candidate'] = '你周六方便吗？'
        result = build_brief(value)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['screen_window']['reply_to_id'], 3)
        self.assertFalse(result['draft_revision']['applied'])
        self.assertEqual(result['draft_revision']['anchor_status'], 'changed')
        self.assertEqual(result['draft_revision']['constraints'], [])
        self.assertEqual(result['draft_revision']['expression_instructions'], [])
        self.assertNotIn('expression_instructions', result['output_contract'])
        self.assertEqual(result['output_contract']['max_questions'], 1)
        self.assertTrue(result['candidate_check']['ok'])

    def test_new_tail_invalidates_old_draft_even_when_primary_question_is_unchanged(self):
        value = request([[sent(1, 'user'), sent(2, function='question'),
                          sent(3, function='sharing')]], reply_to_id=2)
        result = build_brief(value)
        self.assertEqual(result['screen_window']['reply_to_id'], 2)
        self.assertEqual(result['screen_window']['last_id'], 3)
        self.assertEqual(result['draft_revision']['anchor_status'], 'changed')
        self.assertFalse(result['draft_revision']['applied'])

    def test_selecting_another_current_question_also_requires_its_own_draft_scope(self):
        value = request([[sent(1, 'user'), sent(2, function='question'),
                          sent(3, function='question')]], reply_to_id=3)
        value['revision'] = revision(last=3, primary=2)
        result = build_brief(value)
        self.assertEqual(result['draft_revision']['anchor_status'], 'changed')
        self.assertFalse(result['draft_revision']['applied'])

    def test_overlap_upload_order_does_not_change_a_matching_draft(self):
        views = [[sent(1, 'user'), sent(2, function='question')],
                 [sent(2, function='question'), {'kind': 'draft'}, {'kind': 'quote'}]]
        for order in permutations(views):
            result = build_brief(request(list(order)))
            self.assertEqual(result['draft_revision']['anchor_status'], 'matched')
            self.assertTrue(result['draft_revision']['applied'])

    def test_missing_anchor_with_screens_does_not_force_a_new_user_question(self):
        value = request([[sent(1, 'user'), sent(2, function='question')]])
        value['revision'].pop('turn_anchor')
        result = build_brief(value)
        self.assertEqual(result['draft_revision']['anchor_status'], 'missing')
        self.assertFalse(result['draft_revision']['applied'])
        self.assertEqual(result['decision']['action'], 'draft')
        self.assertNotIn('clarification', result)
        self.assertEqual(result['output_contract']['max_candidates'], 1)

    def test_anchor_without_verified_message_ids_cannot_claim_a_match(self):
        result = build_brief({'facts': VERIFIED | {'latest_sender': 'other', 'function': 'question'},
                              'revision': revision()})
        self.assertEqual(result['draft_revision']['anchor_status'], 'unavailable')
        self.assertFalse(result['draft_revision']['applied'])
        self.assertEqual(result['output_contract']['max_questions'], 1)

    def test_flat_manual_revision_still_works_and_declares_its_limit(self):
        value = revision()
        value.pop('turn_anchor')
        result = build_brief({'facts': VERIFIED | {'latest_sender': 'other', 'function': 'question'},
                              'revision': value})
        self.assertTrue(result['draft_revision']['applied'])
        self.assertEqual(result['draft_revision']['anchor_status'], 'manual')
        self.assertIn('平面输入仍须人工确认同稿', result['draft_revision']['scope'])
        self.assertEqual(result['output_contract']['max_questions'], 0)

    def test_wait_stop_and_input_gaps_still_override_style_feedback(self):
        cases = [
            (request([[sent(1, 'user'), sent(2, function='question'), sent(3, 'user')]]), 'hold'),
            (request([[sent(1, 'user'), sent(2, function='question')]], refusal_scope='contact'), 'stop'),
            (request([[sent(1, 'user'), sent(2, function='question')]], text_legible=False), 'clarify'),
            (request([[sent(2)], [sent(3)]]), 'clarify'),
        ]
        for value, action in cases:
            result = build_brief(value)
            self.assertEqual(result['decision']['action'], action)
            self.assertFalse(result['draft_revision']['applied'])
            self.assertEqual(result['draft_revision']['constraints'], [])
            self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_cancellation_and_acknowledgement_limits_survive_an_expired_draft(self):
        value = request([[sent(1, 'user'), sent(2, function='logistics'),
                          sent(3, function='logistics', invitation='cancelled_without_repair')]],
                        invitation='settled')
        value['candidate'] = '那明天呢？'
        result = build_brief(value)
        self.assertEqual(result['decision']['route_id'], 'R10')
        self.assertFalse(result['draft_revision']['applied'])
        self.assertTrue(any('不换日期追问' in item for item in result['current_limits']))
        self.assertEqual(result['output_contract']['max_questions'], 0)
        self.assertFalse(result['candidate_check']['ok'])

    def test_matching_ids_do_not_bypass_case_identity(self):
        facts = VERIFIED | {'screens': [[sent(1, 'user'), sent(2, function='question')]]}
        value = {'cases': {'a': facts, 'b': facts}, 'case_key': 'b',
                 'revision': revision() | {'case_key': 'a'}}
        with self.assertRaises(ValueError):
            build_brief(value)

    def test_invalid_anchors_are_rejected_without_echoing_private_input(self):
        marker = 'SYNTHETIC_PRIVATE_DRAFT'
        bad = [None, [], 2, {}, {'last_id': 2},
               {'last_id': True, 'reply_to_id': 2}, {'last_id': -1, 'reply_to_id': 2},
               {'last_id': 2, 'reply_to_id': marker},
               {'last_id': 2, 'reply_to_id': 2, 'text': marker}]
        for anchor in bad:
            value = request([[sent(1, 'user'), sent(2, function='question')]])
            value['revision']['turn_anchor'] = anchor
            value['candidate'] = marker
            run = subprocess.run([sys.executable, 'scripts/coach.py', '--request', '-'],
                                 cwd=ROOT, input=json.dumps(value), text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)
            self.assertNotIn(marker, run.stdout + run.stderr)

    def test_stdin_stale_feedback_keeps_one_new_reply_without_echoing_draft(self):
        value = request([[sent(1, 'user'), sent(2, function='question'),
                          sent(3, function='question')]])
        value['candidate'] = 'SYNTHETIC_PRIVATE_DRAFT'
        run = subprocess.run([sys.executable, 'scripts/coach.py', '--request', '-'],
                             cwd=ROOT, input=json.dumps(value), text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertFalse(result['draft_revision']['applied'])
        self.assertEqual(result['output_contract']['max_candidates'], 1)
        self.assertNotIn('SYNTHETIC_PRIVATE_DRAFT', run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()

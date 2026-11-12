"""Unsent draft feedback uses fictional facts and constraint codes only."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief

FACTS = {'speaker_verified': True, 'text_legible': True,
         'latest_sender': 'other', 'function': 'question'}


class DraftRevision(unittest.TestCase):
    def test_feedback_preserves_facts_action_and_prior_constraints(self):
        request = {'facts': dict(FACTS), 'revision': {
            'draft_state': 'unsent', 'retained': ['no_teasing'],
            'requested': ['shorter', 'plain']}}
        original = copy.deepcopy(request)
        base = build_brief({'facts': FACTS})
        revised = build_brief(request)
        self.assertEqual(request, original)
        for key in ('decision', 'primary_method', 'current_limits', 'fact_adjustments'):
            self.assertEqual(revised[key], base[key])
        plan = revised['draft_revision']
        self.assertEqual(plan['constraints'], ['no_teasing', 'shorter', 'plain'])
        self.assertFalse(plan['counts_as_new_message'])
        self.assertEqual(revised['output_contract']['max_candidates'], 1)
        second = build_brief({'facts': FACTS, 'revision': {
            'draft_state': 'unsent', 'retained': plan['constraints'],
            'requested': ['no_question']}, 'candidate': '再问一句？'})
        self.assertIn('no_teasing', second['draft_revision']['constraints'])
        self.assertEqual(second['output_contract']['max_questions'], 0)
        self.assertFalse(second['candidate_check']['ok'])

    def test_only_an_explicit_release_removes_a_prior_constraint(self):
        result = build_brief({'facts': FACTS, 'revision': {
            'draft_state': 'unsent', 'retained': ['plain', 'no_question'],
            'requested': [], 'released': ['no_question']}})
        self.assertEqual(result['draft_revision']['constraints'], ['plain'])
        self.assertEqual(result['output_contract']['max_questions'], 1)

    def test_revision_never_bypasses_a_wait_stop_or_missing_input(self):
        for changed, expected in [({'latest_sender': 'user'}, 'hold'),
                                  ({'refusal_scope': 'contact'}, 'stop'),
                                  ({'text_legible': False}, 'clarify')]:
            result = build_brief({'facts': FACTS | changed,
                'revision': {'draft_state': 'unsent', 'requested': ['plain']},
                'candidate': 'SYNTHETIC_DRAFT_DO_NOT_ECHO'})
            self.assertEqual(result['decision']['action'], expected)
            self.assertFalse(result['draft_revision']['applied'])
            self.assertEqual(result['output_contract']['max_candidates'], 0)
            self.assertFalse(result['candidate_check']['ok'])
            self.assertNotIn('SYNTHETIC_DRAFT_DO_NOT_ECHO', json.dumps(result))

    def test_revision_cannot_be_carried_to_another_selected_case(self):
        request = {'cases': {'a': FACTS, 'b': FACTS}, 'case_key': 'a',
                   'revision': {'case_key': 'a', 'draft_state': 'unsent', 'requested': ['plain']}}
        self.assertTrue(build_brief(request)['draft_revision']['applied'])
        with self.assertRaises(ValueError):
            build_brief(request, case_key='b')
        request['revision'].pop('case_key')
        with self.assertRaises(ValueError):
            build_brief(request)

    def test_invalid_feedback_or_sent_draft_is_rejected_without_echo(self):
        command = [sys.executable, str(ROOT / 'scripts/coach.py'), '--request', '-']
        marker = 'SYNTHETIC_FEEDBACK_DO_NOT_ECHO'
        bad = [None, [], {'draft_state': 'sent', 'requested': ['plain']},
               {'draft_state': 'unsent', 'requested': [marker]},
               {'draft_state': 'unsent', 'requested': ['plain'], 'text': marker},
               {'draft_state': 'unsent', 'requested': ['plain'], 'released': ['plain']},
               {'draft_state': 'unsent', 'requested': [], 'retained': ['plain']},
               {'draft_state': 'unsent', 'requested': ['plain', 'plain']}]
        for revision in bad:
            run = subprocess.run(command, input=json.dumps({'facts': FACTS, 'revision': revision}),
                                 text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)
            self.assertNotIn(marker, run.stdout + run.stderr)
        for task in ('meaning', 'analysis', 'review', 'training'):
            with self.assertRaises(ValueError):
                build_brief({'task': task, 'facts': FACTS,
                             'revision': {'draft_state': 'unsent', 'requested': ['plain']}})


if __name__ == '__main__':
    unittest.main()

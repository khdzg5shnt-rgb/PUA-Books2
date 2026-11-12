"""Review contract checks use fictional facts, not private conversations."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief


class ReviewContract(unittest.TestCase):
    def assert_adjustment_is_optional(self, result):
        contract = result['output_contract']
        self.assertEqual(contract['recipient'], 'user')
        self.assertFalse(contract['force_user_blame'])
        self.assertTrue(contract['allow_no_adjustment'])
        self.assertEqual(contract['min_main_adjustments'], 0)
        self.assertEqual(contract['max_main_adjustments'], 1)
        self.assertIn('是否需要调整及依据', contract['required_parts'])
        self.assertNotIn('一项主要调整', contract['required_parts'])

    def test_settled_arrangement_does_not_require_finding_a_mistake(self):
        # Fictional: both agreed on a time and entrance; the final reply confirms it.
        result = build_brief({'task': 'review', 'facts': {
            'speaker_verified': True, 'text_legible': True,
            'latest_sender': 'other', 'function': 'logistics',
            'invitation': 'settled', 'closed_answer_complete': True,
        }})
        self.assertEqual(result['decision']['route_id'], 'R09C')
        self.assertEqual(result['decision']['action'], 'hold')
        self.assert_adjustment_is_optional(result)

    def test_refusal_does_not_itself_require_blame_or_an_adjustment(self):
        # Fictional: a person declines an activity or asks for no further contact.
        for scope, action in [('activity', 'draft'), ('contact', 'stop')]:
            with self.subTest(scope=scope):
                result = build_brief({'task': 'review', 'facts': {
                    'speaker_verified': True, 'text_legible': True,
                    'latest_sender': 'other', 'refusal_scope': scope,
                }})
                self.assertEqual(result['decision']['action'], action)
                self.assert_adjustment_is_optional(result)


if __name__ == '__main__':
    unittest.main()

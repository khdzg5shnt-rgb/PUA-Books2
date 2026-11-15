"""Reject packaged alternatives while keeping natural single replies usable."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief, check_candidate

VERIFIED = {'speaker_verified': True, 'text_legible': True,
            'latest_sender': 'other', 'function': 'question'}


class CandidateDelivery(unittest.TestCase):
    def test_multiple_alternatives_inside_one_string_are_not_one_candidate(self):
        for candidate in [
            '版本一：周六见。\n版本二：行，周六见。',
            '方案1：周六见；方案2：下次见。',
            '回复一：收到。\n回复二：明白。',
            'A. 周六见。\nB. 行，周六见。',
            '1. 收到。\n2. 明白。',
            '**版本一：**收到。\n**版本二：**明白。',
            '- A：收到。\n- B：明白。',
        ]:
            with self.subTest(candidate=candidate):
                self.assertFalse(check_candidate(candidate, 'reply', 'draft')['ok'])

    def test_legitimate_short_text_is_not_rejected_for_letters_or_choices(self):
        for candidate in ['我在B栋，先去A门。', '你周六还是周日方便？',
                          '方案一先保留，周六再讨论。', '我选B。',
                          '我七点到。\n在东门等你。', '都行？那就周六。',
                          '1.2米的那张。\n1.3米的先不买。', '1:30到。\n2:00出发。']:
            with self.subTest(candidate=candidate):
                self.assertTrue(check_candidate(candidate, 'reply', 'draft')['ok'])

    def test_code_fences_are_not_copyable_message_body(self):
        for candidate in ['```收到。```', '收到。\n```']:
            self.assertFalse(check_candidate(candidate, 'reply', 'draft')['ok'])

    def test_pass_never_claims_semantic_or_style_verification(self):
        # A short draft can still invent a booking; verify facts separately.
        value = check_candidate('我已经订好你家楼下的店。', 'reply', 'draft')
        self.assertTrue(value['ok'])
        self.assertTrue(value['manual_review_required'])
        self.assertIn('事实与口吻仍须人工核对', value['scope'])

    def test_zero_questions_and_no_message_remain_valid_choices(self):
        self.assertTrue(check_candidate('', 'reply', 'draft', allow_empty=True)['ok'])
        self.assertFalse(check_candidate('可以吗？', 'reply', 'draft', max_questions=0)['ok'])
        for action in ['hold', 'stop', 'clarify']:
            self.assertTrue(check_candidate('', 'reply', action)['ok'])
            self.assertFalse(check_candidate('版本一：再说一句。', 'reply', action)['ok'])

    def test_question_limit_does_not_pretend_to_parse_unmarked_questions(self):
        value = check_candidate('你几点到，你从哪里走', 'reply', 'draft')
        self.assertTrue(value['ok'])
        self.assertTrue(value['manual_review_required'])
        self.assertIn('语义问句', value['scope'])

    def test_runtime_candidate_check_never_echoes_private_content(self):
        marker = 'SYNTHETIC_PRIVATE_DRAFT'
        request = {'facts': VERIFIED, 'candidate': f'版本一：{marker}\n版本二：收到。'}
        result = build_brief(request)
        self.assertFalse(result['candidate_check']['ok'])
        self.assertNotIn(marker, json.dumps(result))
        self.assertEqual(result['output_contract']['max_candidates'], 1)

    def test_stdin_accepts_one_draft_and_reports_alternatives_without_echoing(self):
        request = {'facts': VERIFIED,
                   'candidate': 'A. SYNTHETIC_PRIVATE_DRAFT\nB. 收到。'}
        run = subprocess.run([sys.executable, str(ROOT / 'scripts/coach.py'), '--request', '-'],
                             input=json.dumps(request), text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertFalse(result['candidate_check']['ok'])
        self.assertNotIn('SYNTHETIC_PRIVATE_DRAFT', run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()

"""Synthetic input/topic checks, not voice transcription or real screenshot tests."""
import copy
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


def brief(screens, **facts):
    return build_brief({'facts': VERIFIED | {'screens': screens} | facts})


class CurrentTopicScope(unittest.TestCase):
    def test_old_turn_callback_does_not_override_new_sharing(self):
        screens = [[sent(1, function='banter', shared_callback_available=True),
                    sent(2, 'user'), sent(3, function='sharing')]]
        result = brief(screens)
        self.assertEqual(result['decision']['route_id'], 'R27')
        self.assertEqual(result['primary_method']['id'], 'M03')

    def test_other_bubble_in_the_same_turn_does_not_donate_its_callback(self):
        screens = [[sent(1, 'user'),
                    sent(2, function='sharing', shared_callback_available=True),
                    sent(3, function='sharing')]]
        self.assertEqual(brief(screens)['decision']['route_id'], 'R27')
        selected = brief(screens, reply_to_id=2)
        self.assertEqual(selected['decision']['route_id'], 'R23')
        self.assertEqual(selected['screen_window']['last_id'], 3)
        self.assertEqual(selected['screen_window']['reply_to_id'], 2)

    def test_current_relevant_callback_survives_overlap_upload_order(self):
        a = sent(1, 'user')
        b = sent(2, function='sharing', shared_callback_available=True)
        for views in permutations([[a, b], [b, {'kind': 'quote'}]]):
            result = brief(list(views))
            self.assertEqual(result['decision']['route_id'], 'R23')
            self.assertEqual(result['primary_method']['id'], 'M05')

    def test_serious_current_content_still_precedes_a_relevant_callback(self):
        for function, route in [('question', 'R18'), ('advice_request', 'R16'),
                                ('distress', 'R15'), ('good_news', 'R17'),
                                ('correction', 'R12')]:
            result = brief([[sent(1, 'user'), sent(2, function=function,
                                                      shared_callback_available=True)]])
            self.assertEqual(result['decision']['route_id'], route)

    def test_flat_input_keeps_current_callback_but_screens_reject_global_tags(self):
        facts = VERIFIED | {'latest_sender': 'other', 'function': 'sharing',
                            'shared_callback_available': True}
        self.assertEqual(build_brief({'facts': facts})['decision']['route_id'], 'R23')
        with self.assertRaises(ValueError):
            brief([[sent(1, 'user'), sent(2, function='sharing')]],
                  shared_callback_available=True)

    def test_topic_change_never_creates_an_exception_to_waiting(self):
        screens = [[sent(1, function='sharing', shared_callback_available=True),
                    sent(2, 'user')]]
        result = brief(screens, goal='reply')
        self.assertEqual(result['decision']['route_id'], 'R04')
        self.assertEqual(result['output_contract']['max_candidates'], 0)
        necessary = brief(screens, necessary_new_logistics=True,
                          invitation='no_alternative', refusal_scope='activity')
        self.assertEqual(necessary['decision']['route_id'], 'R04N')
        self.assertTrue(any('只通知' in item for item in necessary['current_limits']))
        self.assertTrue(any('不换日期追问' in item for item in necessary['current_limits']))


class InputEvidenceScope(unittest.TestCase):
    def test_unheard_incoming_voice_needs_content_but_outgoing_voice_can_wait(self):
        incoming = brief([[sent(1, 'user'), sent(2)]], text_legible=False)
        self.assertEqual(incoming['decision']['route_id'], 'R00')
        self.assertEqual(incoming['clarification']['field'], 'text_legible')
        self.assertEqual(incoming['output_contract']['max_questions'], 1)
        self.assertEqual(incoming['output_contract']['max_candidates'], 0)
        outgoing = brief([[sent(1), sent(2, 'user')]], text_legible=False)
        self.assertEqual(outgoing['decision']['route_id'], 'R04')
        self.assertNotIn('clarification', outgoing)

    def test_withdrawal_notice_is_not_a_new_reply_or_a_boundary_cancellation(self):
        # The withdrawn body is not supplied as an active sent bubble. Its
        # historical arrangement or boundary remains a separate verified fact.
        screens = [[sent(1, 'user'), {'kind': 'notice'}]]
        self.assertEqual(brief(screens, invitation='settled')['decision']['route_id'], 'R04')
        self.assertEqual(brief(screens, refusal_scope='contact')['decision']['route_id'], 'R01')
        new_content = [[sent(1, 'user'), {'kind': 'notice'}, sent(3, function='question')]]
        result = brief(new_content, refusal_scope='activity', invitation='no_alternative')
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertTrue(any('不换日期追问' in item for item in result['current_limits']))

    def test_conflicting_edited_versions_do_not_choose_the_last_uploaded_one(self):
        one = [sent(1, 'user'), sent(2, function='question')]
        two = [sent(1, 'user'), sent(2, function='correction')]
        for views in permutations([one, two]):
            with self.assertRaises(ValueError):
                brief(list(views))

    def test_verified_current_version_is_used_without_reusing_an_old_draft(self):
        facts = VERIFIED | {'screens': [[sent(1, 'user'), sent(2, function='question')]]}
        request = {'facts': facts}
        original = copy.deepcopy(request)
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertNotIn('draft_revision', result)
        self.assertEqual(request, original)
        uncertain = brief(facts['screens'], text_legible=False)
        self.assertEqual(uncertain['decision']['action'], 'clarify')
        self.assertEqual(uncertain['output_contract']['max_questions'], 1)

    def test_platform_notice_cannot_resolve_a_pending_request_by_itself(self):
        screens = [[sent(1, 'user'), sent(2, function='advice_request'),
                    {'kind': 'notice', 'resolves': [2]}]]
        with self.assertRaises(ValueError):
            brief(screens)


if __name__ == '__main__':
    unittest.main()

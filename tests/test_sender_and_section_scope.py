"""Unknown senders and exact source bindings, using fictional input only."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief
from route import select_route
from search_knowledge import search
from validate_os import validate

VERIFIED = {'speaker_verified': True, 'text_legible': True}


class VerifiedSender(unittest.TestCase):
    def test_unknown_or_omitted_direction_cannot_authorize_a_draft(self):
        for direction in [{}, {'latest_sender': 'unknown'}]:
            for task in ['reply', 'meaning', 'analysis', 'review', 'training']:
                request = {'task': task, 'facts': VERIFIED | direction | {
                    'function': 'question', 'pending_reply': False}}
                original = copy.deepcopy(request)
                result = build_brief(request | {'candidate': ''} if task == 'reply' else request)
                self.assertEqual(result['decision']['route_id'], 'R00T')
                self.assertEqual(result['clarification']['question'], '最后一条已发消息是谁发的？')
                self.assertEqual(result['clarification']['recipient'], 'user')
                self.assertEqual(request, original)
                if task == 'reply':
                    self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_waiting_can_remain_conservative_but_new_logistics_needs_direction(self):
        facts = VERIFIED | {'latest_sender': 'unknown', 'pending_reply': True}
        self.assertEqual(select_route(facts)['route_id'], 'R04')
        result = build_brief({'facts': facts | {'necessary_new_logistics': True}})
        self.assertEqual(result['decision']['route_id'], 'R00T')
        self.assertEqual(select_route(facts | {'latest_sender': 'user',
            'necessary_new_logistics': True})['route_id'], 'R04N')

    def test_known_directions_and_contact_refusal_keep_their_priority(self):
        facts = VERIFIED | {'function': 'question'}
        self.assertEqual(select_route(facts | {'latest_sender': 'user'})['route_id'], 'R04')
        result = select_route(facts | {'latest_sender': 'other', 'pending_reply': True})
        self.assertEqual(result['route_id'], 'R18')
        self.assertIn('pending_reply', result['fact_adjustments'])
        self.assertEqual(select_route(facts | {'refusal_scope': 'contact'})['route_id'], 'R01')

    def test_a_verified_first_opening_is_different_from_a_missing_tail(self):
        result = build_brief({'facts': VERIFIED | {
            'latest_sender': 'none', 'function': 'opening'}})
        self.assertEqual(result['decision']['route_id'], 'R25')
        self.assertNotIn('clarification', result)
        with self.assertRaises(ValueError):
            select_route(VERIFIED | {'latest_sender': 'none', 'function': 'question'})


class SectionScope(unittest.TestCase):
    def test_method_focus_does_not_borrow_a_different_section_of_a_cited_book(self):
        for mid, phrase in [('M14', '不从酒量或身体反应推断同意'),
                            ('M25', '生气可以表达不以训斥控制')]:
            hits = search(phrase, method=mid)
            self.assertTrue(hits)
            self.assertFalse(any(h['heading'] == phrase for h in hits))
            self.assertTrue(all(mid in h['section_method_ids'] for h in hits))

    def test_global_search_distinguishes_section_and_whole_file_relations(self):
        hit = search('不从酒量或身体反应推断同意', limit=1)[0]
        self.assertEqual(hit['heading'], '不从酒量或身体反应推断同意')
        self.assertEqual(hit['section_method_ids'], ['M01', 'M23'])
        self.assertNotIn('M14', hit['section_method_ids'])
        self.assertIn('M14', hit['source_method_ids'])

    def test_legacy_page_locator_alone_does_not_bind_all_its_headings(self):
        # B025's M25 citation is now explicitly bound to its two relevant sections.
        hit = search('有自己的安排不等于编造稀缺', method='M25', limit=1)[0]
        self.assertTrue(hit['query_matched'])
        self.assertEqual(hit['heading'], '有自己的安排不等于编造稀缺')
        self.assertIn('M25', hit['section_method_ids'])
        self.assertFalse(any(h['heading'] == '复盘只落在已有证据支持的环节'
            for h in search('复盘只落在已有证据支持的环节', method='M25')))

    def test_focus_changes_only_a_bound_source_and_not_the_reply_decision(self):
        request = {'facts': VERIFIED | {'latest_sender': 'other', 'goal': 'invite',
            'invite_ready': True, 'user_availability_known': True, 'activity_verified': True}}
        regular = build_brief(request)
        unrelated = build_brief(request | {'focus': '不从酒量或身体反应推断同意'})
        self.assertEqual(unrelated['decision'], regular['decision'])
        self.assertEqual(unrelated['read_next'], regular['read_next'])
        self.assertEqual(unrelated['retrieval']['mode'], 'preferred')
        matching = build_brief(request | {'focus': '真实意愿与具体邀约'})
        self.assertEqual(matching['read_next']['heading'], '真实意愿与具体邀约')
        self.assertEqual(matching['decision'], regular['decision'])

    def test_a_broken_explicit_section_binding_fails_the_repository_check(self):
        with tempfile.TemporaryDirectory(prefix='books2-section-binding-') as folder:
            copied = Path(folder) / 'repo'
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns('__pycache__', '.git'))
            path = copied / 'system/methods.json'
            data = json.loads(path.read_text())
            source = next(s for m in data['methods'] if m['id'] == 'M25'
                          for s in m['sources'] if 'section_headings' in s)
            for bad in [[], ['NO_SUCH_SECTION'], ['主动与收住可以同时成立'] * 2]:
                source['section_headings'] = bad
                path.write_text(json.dumps(data, ensure_ascii=False))
                self.assertIn('Invalid method source section binding: M25', validate(copied)['errors'])


if __name__ == '__main__':
    unittest.main()

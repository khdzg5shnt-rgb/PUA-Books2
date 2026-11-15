"""Curated public phrases select one already-bound section, never a route."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coach import build_brief
from knowledge import KnowledgeCatalog
from search_knowledge import search
from validate_os import validate

VERIFIED = {'speaker_verified': True, 'text_legible': True, 'latest_sender': 'other'}


def fixture(root):
    (root / 'system').mkdir()
    (root / 'knowledge/books').mkdir(parents=True)
    path = 'knowledge/books/synthetic.md'
    (root / path).write_text('# Public synthetic notes\n\n## Primary\nGeneral content.\n\n'
                            '## Specific\nEXACT_LITERAL_TARGET.\n\n'
                            '## Other method\nDo not borrow this section.\n')
    methods = [
        {'id': 'M04', 'sources': [{'path': path, 'locator': 'Primary'},
                                {'path': path, 'locator': 'Specific'}]},
        {'id': 'M06', 'sources': [{'path': path, 'locator': 'Other method'}]},
    ]
    lookup = {'methods': {
        'M04': {'aliases': ['generic_answer'],
                'preferred': {'path': path, 'heading': 'Primary'},
                'focus_aliases': [{'phrases': ['SYNTHETIC_ALIAS_ONE'],
                                   'reference': {'path': path, 'heading': 'Specific'}}]},
        'M06': {'aliases': ['generic_banter'],
                'preferred': {'path': path, 'heading': 'Other method'}},
    }}
    (root / 'system/methods.json').write_text(json.dumps({'methods': methods}))
    (root / 'system/knowledge_map.json').write_text(json.dumps(lookup))
    return path, lookup


class FocusAliases(unittest.TestCase):
    def test_all_seven_actual_method_mappings_resolve_without_changing_bindings(self):
        catalog = KnowledgeCatalog()
        count = 0
        for mid in catalog.methods:
            for rule in catalog.focus_aliases(mid):
                hit = search(rule['phrases'][0], method=mid, limit=1, catalog=catalog)[0]
                self.assertTrue(hit['query_matched'])
                self.assertEqual(hit.get('match_basis'), 'curated_phrase')
                self.assertEqual((hit['path'], hit['heading']),
                                 (rule['reference']['path'], rule['reference']['heading']))
                self.assertIn(mid, hit['section_method_ids'])
                count += 1
        self.assertEqual(count, 7)

    def test_literal_hit_keeps_priority_even_when_query_contains_a_curated_phrase(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, lookup = fixture(root)
            lookup['methods']['M04']['focus_aliases'][0]['reference']['heading'] = 'Primary'
            (root / 'system/knowledge_map.json').write_text(json.dumps(lookup))
            hit = search('SYNTHETIC_ALIAS_ONE EXACT_LITERAL_TARGET', method='M04', root=root)[0]
            self.assertEqual(hit['heading'], 'Specific')
            self.assertNotIn('match_basis', hit)

    def test_unmatched_focus_retains_the_original_preferred_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture(root)
            hit = search('NO_MATCHING_PHRASE', method='M04', root=root)[0]
            self.assertEqual(hit['heading'], 'Primary')
            self.assertFalse(hit['query_matched'])

    def test_unscoped_search_does_not_turn_aliases_into_method_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture(root)
            self.assertEqual(search('SYNTHETIC_ALIAS_ONE', root=root), [])
            hit = search('M04 SYNTHETIC_ALIAS_ONE', root=root)[0]
            self.assertEqual(hit['heading'], 'Specific')

    def test_target_cannot_borrow_a_different_methods_section_in_the_same_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, lookup = fixture(root)
            lookup['methods']['M04']['focus_aliases'][0]['reference']['heading'] = 'Other method'
            (root / 'system/knowledge_map.json').write_text(json.dumps(lookup))
            with self.assertRaises(ValueError):
                search('SYNTHETIC_ALIAS_ONE', method='M04', root=root)

    def test_invalid_public_mappings_fail_without_echoing_input(self):
        bad = [None, {}, [{'phrases': []}],
               [{'phrases': [''], 'reference': {'path': 'missing', 'heading': 'missing'}}],
               [{'phrases': ['REPEAT', 'repeat'], 'reference': {'path': 'missing', 'heading': 'missing'}}],
               [{'phrases': ['SYNTHETIC_PRIVATE_MARKER'],
                 'reference': {'path': '../outside.md', 'heading': 'missing'}}]]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, lookup = fixture(root)
            for value in bad:
                with self.subTest(value=value):
                    lookup['methods']['M04']['focus_aliases'] = value
                    (root / 'system/knowledge_map.json').write_text(json.dumps(lookup))
                    with self.assertRaises(ValueError) as error:
                        KnowledgeCatalog(root).focus_aliases('M04')
                    self.assertNotIn('SYNTHETIC_PRIVATE_MARKER', str(error.exception))

    def test_multiple_targets_in_a_single_query_do_not_pick_a_winner(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, lookup = fixture(root)
            lookup['methods']['M04']['focus_aliases'].append({
                'phrases': ['SYNTHETIC_ALIAS_TWO'],
                'reference': {'path': path, 'heading': 'Primary'}})
            (root / 'system/knowledge_map.json').write_text(json.dumps(lookup))
            hit = search('SYNTHETIC_ALIAS_ONE SYNTHETIC_ALIAS_TWO', method='M04', root=root)[0]
            self.assertEqual(hit['heading'], 'Primary')
            self.assertFalse(hit['query_matched'])

    def test_new_operation_sees_phrase_mapping_updates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, lookup = fixture(root)
            self.assertEqual(search('SYNTHETIC_ALIAS_ONE', method='M04', root=root)[0]['heading'], 'Specific')
            lookup['methods']['M04']['focus_aliases'][0]['reference']['heading'] = 'Primary'
            (root / 'system/knowledge_map.json').write_text(json.dumps(lookup))
            self.assertEqual(search('SYNTHETIC_ALIAS_ONE', method='M04', root=root)[0]['heading'], 'Primary')

    def test_brief_changes_only_the_reading_paragraph_and_keeps_refusal_limits(self):
        request = {'facts': VERIFIED | {'invitation': 'no_alternative'},
                   'focus': '没说哪天能见面'}
        original = copy.deepcopy(request)
        base = build_brief({'facts': request['facts']})
        focused = build_brief(request)
        for key in ['decision', 'primary_method', 'current_limits', 'output_contract']:
            self.assertEqual(focused[key], base[key])
        self.assertEqual(focused['retrieval']['mode'], 'curated_phrase')
        self.assertEqual(focused['read_next']['path'], 'knowledge/books/B121.md')
        self.assertEqual(request, original)
        self.assertNotIn(request['focus'], json.dumps(focused, ensure_ascii=False))

    def test_alias_from_another_method_does_not_replace_a_serious_question(self):
        request = {'facts': VERIFIED | {'function': 'question'}, 'focus': '认真聊天时别硬接梗'}
        result = build_brief(request)
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertEqual(result['primary_method']['id'], 'M04')
        self.assertEqual(result['retrieval']['mode'], 'preferred')

    def test_wait_stop_and_clarification_do_not_start_focused_retrieval(self):
        for extra in [{'latest_sender': 'user'}, {'refusal_scope': 'contact'},
                      {'text_legible': False}]:
            with patch('coach.search', side_effect=AssertionError('Should not search')):
                result = build_brief({'facts': VERIFIED | extra, 'focus': '没说哪天能见面'})
            self.assertEqual(result['output_contract']['max_candidates'], 0)

    def test_maintenance_checks_phrase_configuration(self):
        original = KnowledgeCatalog.focus_aliases
        def checked(catalog, mid):
            if mid == 'M04':
                raise ValueError('Invalid synthetic fixture')
            return original(catalog, mid)
        with patch.object(KnowledgeCatalog, 'focus_aliases', checked):
            self.assertIn('Invalid method-scoped focus aliases: M04', validate()['errors'])

    def test_stdin_resolves_a_phrase_without_echoing_it(self):
        phrase = '把学历职业直接说清楚'
        run = subprocess.run([sys.executable, 'scripts/coach.py', '--request', '-'],
                             input=json.dumps({'facts': VERIFIED | {'function': 'question'},
                                               'focus': phrase}),
                             cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['retrieval']['mode'], 'curated_phrase')
        self.assertEqual(result['decision']['route_id'], 'R18')
        self.assertNotIn(phrase, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()

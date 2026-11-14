"""Source retention, fresh retrieval, and compact CLI behavior on public fixtures."""
import collections
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
from method_cards import check_documents, render_documents
from search_knowledge import search


class KnowledgeViews(unittest.TestCase):
    def fixture(self, root):
        (root / 'system').mkdir()
        (root / 'knowledge/books').mkdir(parents=True)
        path = 'knowledge/books/synthetic.md'
        (root / path).write_text('# Synthetic public notes\n\n## Primary\nFirst content.\n\n'
            '## Other\nFocused content.\n\n## Unbound\nMust not leak into this method.\n')
        method = {'id': 'M04', 'name': 'Synthetic answer', 'use_when': 'Known question',
            'operation': 'Answer the current question', 'avoid': 'Do not invent facts',
            'evidence_level': 'Synthetic decision fixture, not effect evidence',
            'sources': [
                {'path': path, 'locator': 'Primary', 'section_headings': ['Primary']},
                {'path': path, 'locator': 'Other', 'section_headings': ['Other']}],
            'example': {'other': 'SYNTHETIC_QUESTION', 'reply': 'SYNTHETIC_REPLY'},
            'example_kind': 'synthetic_not_user_chat'}
        (root / 'system/methods.json').write_text(json.dumps({'methods': [method]}))
        (root / 'system/knowledge_map.json').write_text(json.dumps({'methods': {
            'M04': {'preferred': {'path': path, 'heading': 'Primary'}, 'aliases': ['answer']}}}))
        return path

    def test_focused_search_reads_each_configuration_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            reads = collections.Counter()
            original = Path.read_text

            def tracked(path, *args, **kwargs):
                reads[path.name] += 1
                return original(path, *args, **kwargs)

            with patch.object(Path, 'read_text', tracked):
                hit = search('Focused', root=root, method='M04', limit=1)[0]
            self.assertEqual(hit['heading'], 'Other')
            self.assertEqual(reads['methods.json'], 1)
            self.assertEqual(reads['knowledge_map.json'], 1)
            self.assertEqual(reads['synthetic.md'], 1)

    def test_reusing_a_parsed_section_does_not_consume_or_mutate_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = self.fixture(root)
            catalog = KnowledgeCatalog(root)
            one = catalog.preferred('M04')
            one['excerpt'] = 'CHANGED_COPY'
            two = catalog.resolve({'path': path, 'heading': 'Primary'})
            self.assertIn('First content', two['excerpt'])
            self.assertEqual(two, catalog.preferred('M04'))
            self.assertIn('text', catalog.sections(path)[1])

    def test_new_operations_see_updated_notes_and_method_bindings(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = self.fixture(root)
            self.assertFalse(any(h['heading'] == 'Other' for h in
                search('NEW_PUBLIC_TEXT', root=root, method='M04')))
            p = root / path
            p.write_text(p.read_text().replace('Focused content', 'NEW_PUBLIC_TEXT'))
            self.assertEqual(search('NEW_PUBLIC_TEXT', root=root, method='M04', limit=1)[0]
                             ['heading'], 'Other')
            p = root / 'system/methods.json'
            data = json.loads(p.read_text())
            data['methods'][0]['sources'] = data['methods'][0]['sources'][:1]
            p.write_text(json.dumps(data))
            self.assertFalse(any(h['heading'] == 'Other' for h in
                search('NEW_PUBLIC_TEXT', root=root, method='M04')))

    def test_source_scope_and_repository_scope_are_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            catalog = KnowledgeCatalog(root)
            self.assertTrue(search('Unbound', root=root, limit=1))
            self.assertFalse(any(h['heading'] == 'Unbound' for h in
                search('Unbound', root=root, method='M04', catalog=catalog)))
            with self.assertRaises(ValueError):
                search('Focused', root=ROOT, method='M04', catalog=catalog)
            with self.assertRaises(ValueError):
                catalog.resolve({'path': '../outside.md', 'heading': 'Primary'})

    def test_rendered_cards_keep_actions_examples_and_all_source_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = self.fixture(root)
            rendered = render_documents(root)
            cards = rendered['system/METHOD_CARDS.md']
            sources = rendered['system/METHOD_SOURCES.md']
            self.assertIn('Answer the current question', cards)
            self.assertIn('Do not invent facts', cards)
            self.assertIn('SYNTHETIC_REPLY', cards)
            self.assertIn('METHOD_SOURCES.md#m04', cards)
            self.assertEqual(cards.count('](../' + path + ')'), 1)
            self.assertEqual(sources.count('](../' + path + ')'), 2)
            self.assertNotIn('## Unbound', sources)

    def test_generated_view_drift_is_reported_without_rewriting_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            for relative, text in render_documents(root).items():
                (root / relative).write_text(text)
            self.assertEqual(check_documents(root), [])
            p = root / 'system/METHOD_SOURCES.md'
            p.write_text(p.read_text().replace('- [Other]', '- [Removed]'))
            changed = p.read_text()
            self.assertEqual(check_documents(root), [
                'Generated method view is not synchronized: system/METHOD_SOURCES.md'])
            self.assertEqual(p.read_text(), changed)

    def test_compact_route_cli_keeps_a_reviewable_full_reference_option(self):
        command = [sys.executable, str(ROOT / 'scripts/route.py'), '--facts', '-']
        payload = json.dumps({'speaker_verified': True, 'text_legible': True,
            'latest_sender': 'other', 'function': 'question'})
        compact = subprocess.run(command, input=payload, text=True, capture_output=True)
        full = subprocess.run(command + ['--references'], input=payload, text=True, capture_output=True)
        self.assertEqual(compact.returncode, 0, compact.stderr)
        self.assertEqual(full.returncode, 0, full.stderr)
        short, detailed = json.loads(compact.stdout), json.loads(full.stdout)
        self.assertNotIn('references', short)
        self.assertEqual(short['reference_count'], len(detailed['references']))
        self.assertEqual(short['source'], detailed['source'])
        self.assertEqual(short['route_id'], detailed['route_id'])
        self.assertEqual(short['reference_index']['heading'], 'M04')
        self.assertLess(len(compact.stdout), len(full.stdout))

    def test_brief_and_focused_retrieval_share_one_public_catalog(self):
        original = Path.read_text
        reads = collections.Counter()

        def tracked(path, *args, **kwargs):
            reads[path.name] += 1
            return original(path, *args, **kwargs)

        request = {'facts': {'speaker_verified': True, 'text_legible': True,
            'latest_sender': 'other', 'function': 'question'}, 'focus': 'B106-27'}
        with patch.object(Path, 'read_text', tracked):
            brief = build_brief(request)
        self.assertEqual(brief['primary_method']['id'], 'M04')
        self.assertEqual(brief['read_next']['heading'], 'B106-27 职业、经历与说明按问题本身回答')
        self.assertEqual(reads['methods.json'], 1)
        self.assertEqual(reads['knowledge_map.json'], 1)


if __name__ == '__main__':
    unittest.main()
